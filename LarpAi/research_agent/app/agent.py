import logging
from typing import Optional, Callable, Dict, Any
from research_agent.app.models.plan import ExecutionPlan
from research_agent.app.models.report import ResearchReport
from research_agent.app.models.aggregator import AggregatedResearchData
from research_agent.app.planner import PlannerAgent
from research_agent.app.executor import ResearchExecutorAgent
from research_agent.app.agents import ResultAggregatorAgent, CriticAgent
from research_agent.app.agents.evaluator import EvaluatorAgent
from research_agent.app.report import ReportGeneratorAgent
from research_agent.app.services.llm_base import BaseLLMProvider
from research_agent.app.services.llm_adapters import get_llm_provider
from research_agent.app.services.llm_router import LLMRouter
from research_agent.app.payment import PaymentAgent
from research_agent.app.utils.contradiction_detector import ContradictionDetector

logger = logging.getLogger(__name__)


class LarpAgent:
    """
    Unified high-level SDK interface for Larp AI Agent Core.
    Designed for seamless single-line integration into backend API servers (FastAPI/Django/Celery).

    New in this version:
        - EvaluatorAgent: Self-critiquing reflexion loop that scores research quality
          on Coverage, Depth, and Relevance axes. Triggers a second deeper research
          pass if any axis falls below the configured threshold.
        - ContradictionDetector: Pairwise claim conflict analysis. Appends a
          dedicated "⚠️ Conflicting Evidence" section to the report when conflicts
          are detected between sources.
        - CriticAgent: Adversarial peer review stressing test for logical flaws,
          objectivity, source authority, and alternative/counter-arguments.
        - LLMRouter: Dynamic cost/latency routing of specific LLM models based on
          task category (planning, verification, critique, formatting).

    Usage:
        from research_agent import LarpAgent

        agent = LarpAgent(wallet_balance=100.0, on_event=my_callback)
        report = await agent.run("Compare solar vs wind energy")
    """

    def __init__(
        self,
        llm_provider: Optional[BaseLLMProvider] = None,
        wallet_balance: float = 100.0,
        on_event: Optional[Callable[[str, Dict[str, Any]], None]] = None,
        evaluator_threshold: float = 0.70,
        enable_reflexion: bool = True,
        enable_contradiction_detection: bool = True,
        enable_critic: bool = True,
    ):
        """
        Args:
            llm_provider:                   LLM backend (auto-detected from env if None).
            wallet_balance:                 Starting x402 wallet balance in USD.
            on_event:                       Optional SSE event callback.
            evaluator_threshold:            Quality threshold [0.0–1.0] below which
                                            a second research pass is triggered (default 0.70).
            enable_reflexion:               If True, runs EvaluatorAgent after first pass
                                            and triggers second pass on low-quality results.
            enable_contradiction_detection: If True, runs ContradictionDetector and injects
                                            a conflict section into the final report.
            enable_critic:                  If True, runs CriticAgent to stress-test the report
                                            and append alternative/counter-arguments.
        """
        self.llm_router = LLMRouter()
        self.llm_provider = llm_provider or self.llm_router.get_provider_for_task("formatting")
        self.payment_agent = PaymentAgent(wallet_balance=wallet_balance)
        self.on_event = on_event
        self.enable_reflexion = enable_reflexion
        self.enable_contradiction_detection = enable_contradiction_detection
        self.enable_critic = enable_critic

        # Dynamic Routing Injection:
        # Planner uses fast model (gemini-2.0-flash / gpt-4o-mini)
        self.planner = PlannerAgent(llm_provider=self.llm_router.get_provider_for_task("planning"))
        
        # Scraper tool uses the router LLM provider configured inside ResearchExecutorAgent
        self.executor = ResearchExecutorAgent(
            llm_provider=self.llm_router.get_provider_for_task("verification"),
            on_event=self.on_event
        )
        self.aggregator = ResultAggregatorAgent()
        self.evaluator = EvaluatorAgent(threshold=evaluator_threshold)
        self.report_generator = ReportGeneratorAgent()
        self.contradiction_detector = ContradictionDetector()
        
        # Critic uses reasoning model (Claude 3.5 Sonnet / GPT-4o)
        self.critic = CriticAgent(llm_provider=self.llm_router.get_provider_for_task("critique"))


    def _emit(self, event_type: str, payload: Dict[str, Any]) -> None:
        """Invokes on_event callback safely if registered."""
        if self.on_event:
            try:
                self.on_event(event_type, payload)
            except Exception as e:
                logger.warning(f"Error in on_event callback for event '{event_type}': {e}")

    async def run(
        self,
        query: str,
        format_type: str = "FULL",
        max_depth: int = 1
    ) -> ResearchReport:
        """
        Runs the end-to-end research workflow:
            Planning → Parallel Execution → Aggregation → [Evaluation → Second Pass?]
            → Contradiction Detection → Adversarial Critique → Cited Report Generation

        Args:
            query:       The research topic or question.
            format_type: 'FULL' for comprehensive report, 'EXECUTIVE' for briefing.
            max_depth:   Depth level for execution (1=standard, 2+=deep-dive).

        Returns:
            ResearchReport containing title, confidence score, and markdown content.
            The markdown may include a "⚠️ Conflicting Evidence" section if contradictions
            are detected between sources.
        """
        clean_query = query.strip()
        if not clean_query:
            raise ValueError("Research query cannot be empty.")

        logger.info(f"LarpAgent starting research workflow for query: '{clean_query[:60]}...'")
        self._emit("start", {"query": clean_query, "format_type": format_type})

        # ── 1. Planning Stage ──────────────────────────────────────────────────
        self._emit("planning_start", {"query": clean_query})
        plan = await self.planner.create_plan(clean_query)
        self._emit("plan_created", {
            "plan_id": plan.plan_id,
            "tasks_count": len(plan.tasks),
            "stages_count": len(plan.execution_order)
        })

        # ── 2. Execution Stage ─────────────────────────────────────────────────
        self._emit("execution_start", {"plan_id": plan.plan_id})
        exec_result = await self.executor.execute_plan(plan, max_depth=max_depth)
        self._emit("execution_complete", {
            "status": exec_result.status,
            "completed_tasks": exec_result.completed_tasks,
            "execution_time_seconds": exec_result.total_execution_time_seconds
        })

        # ── 3. Aggregation Stage ───────────────────────────────────────────────
        self._emit("aggregation_start", {"plan_id": plan.plan_id})
        aggregated = self.aggregator.aggregate_results(exec_result)
        self._emit("aggregation_complete", {
            "total_sources": aggregated.total_sources_count,
            "confidence_score": aggregated.average_confidence_score
        })

        # ── 4. Reflexion / Evaluation Stage (NEW) ─────────────────────────────
        if self.enable_reflexion:
            self._emit("evaluation_start", {"query": clean_query})
            verdict = self.evaluator.evaluate(clean_query, aggregated)
            self._emit("evaluation_complete", {
                "passed": verdict.passed,
                "coverage_score": verdict.coverage_score,
                "depth_score": verdict.depth_score,
                "relevance_score": verdict.relevance_score,
                "overall_score": verdict.overall_score,
                "gap_summary": verdict.gap_summary,
            })

            # If quality is insufficient, run a targeted second research pass
            if not verdict.passed and verdict.missing_topics:
                logger.info(
                    f"EvaluatorAgent: Quality below threshold. "
                    f"Running second pass on {len(verdict.missing_topics)} gap topic(s)."
                )
                self._emit("reflexion_pass_start", {
                    "missing_topics": verdict.missing_topics,
                    "gap_summary": verdict.gap_summary
                })

                for gap_query in verdict.missing_topics:
                    gap_plan = await self.planner.create_plan(gap_query)
                    gap_exec = await self.executor.execute_plan(gap_plan, max_depth=1)
                    gap_aggregated = self.aggregator.aggregate_results(gap_exec)

                    # Merge gap results into the primary aggregated data
                    aggregated.all_search_results.extend(gap_aggregated.all_search_results)
                    aggregated.all_verified_claims.extend(gap_aggregated.all_verified_claims)
                    aggregated.synthesized_takeaways.extend(gap_aggregated.synthesized_takeaways)
                    aggregated.all_citations.extend(gap_aggregated.all_citations)
                    aggregated.total_sources_count += gap_aggregated.total_sources_count

                self._emit("reflexion_pass_complete", {
                    "new_total_sources": aggregated.total_sources_count
                })

        # ── 5. Contradiction Detection ────────────────────────────────────────
        contradiction_section = ""
        if self.enable_contradiction_detection:
            self._emit("contradiction_detection_start", {})
            conflicts = self.contradiction_detector.detect(aggregated)
            if conflicts:
                contradiction_section = self.contradiction_detector.format_markdown_section(conflicts)
                logger.info(f"ContradictionDetector: {len(conflicts)} conflict(s) found.")
            self._emit("contradiction_detection_complete", {
                "conflicts_found": len(conflicts)
            })

        # ── 6. Adversarial Critique Stage (NEW) ───────────────────────────────
        critic_section = ""
        if self.enable_critic:
            self._emit("critic_start", {})
            critic_section = await self.critic.analyze(clean_query, aggregated)
            self._emit("critic_complete", {})

        # ── 7. Report Generation Stage ────────────────────────────────────────
        self._emit("report_start", {"query": clean_query})
        report = self.report_generator.generate_report(aggregated, format_type=format_type)

        # Append contradiction section if conflicts exist
        if contradiction_section:
            report.markdown_content = report.markdown_content + "\n" + contradiction_section

        # Append adversarial critique section
        if critic_section:
            report.markdown_content = report.markdown_content + "\n" + critic_section

        self._emit("report_ready", {
            "report_id": report.report_id,
            "title": report.title,
            "markdown_content": report.markdown_content
        })

        logger.info(f"LarpAgent completed research workflow successfully for report {report.report_id}.")
        return report

    async def run_followup(
        self,
        original_plan: ExecutionPlan,
        original_report: ResearchReport,
        follow_up_prompt: str,
        format_type: str = "FULL"
    ) -> ResearchReport:
        """
        Interactive Follow-up Chat (Delta-DAG Re-Planning):
        Plans and schedules only delta subtasks for the follow-up prompt,
        preserves original findings, merges new facts/citations, and returns an updated report.
        """
        clean_prompt = follow_up_prompt.strip()
        if not clean_prompt:
            raise ValueError("Follow-up prompt cannot be empty.")

        logger.info(f"LarpAgent starting follow-up resolution for query: '{clean_prompt[:50]}'")
        self._emit("followup_start", {"prompt": clean_prompt, "original_plan_id": original_plan.plan_id})

        # 1. Delta Planning Stage
        delta_plan = await self.planner.create_delta_plan(original_plan, clean_prompt)
        self._emit("followup_plan_created", {
            "delta_plan_id": delta_plan.plan_id,
            "tasks_count": len(delta_plan.tasks)
        })

        # 2. Delta Execution Stage
        exec_result = await self.executor.execute_plan(delta_plan, max_depth=1)

        # 3. Delta Aggregation & Merging
        delta_aggregated = self.aggregator.aggregate_results(exec_result)

        # Retrieve/reconstruct previous aggregated data to merge with
        # To simulate merging, we construct a consolidated AggregatedResearchData
        # (Alternatively in a database project this is loaded from DB)
        merged_takeaways = list(set(delta_aggregated.synthesized_takeaways + [
            # parse clean lines from original report as fallback
            line.strip("- ") for line in original_report.markdown_content.split("\n")
            if line.strip().startswith("- ") and len(line) < 300
        ]))

        merged_aggregated = AggregatedResearchData(
            plan_id=original_plan.plan_id,
            query=f"{original_plan.query} -> {clean_prompt}",
            synthesized_takeaways=merged_takeaways[:12],  # Cap takeaways count
            all_search_results=delta_aggregated.all_search_results,
            all_verified_claims=delta_aggregated.all_verified_claims,
            all_citations=delta_aggregated.all_citations,
            total_sources_count=original_report.total_sources + delta_aggregated.total_sources_count,
            average_confidence_score=round((original_report.confidence_score + delta_aggregated.average_confidence_score) / 2.0, 3)
        )

        # 4. Generate Updated Versioned Report
        self._emit("report_start", {"query": clean_prompt})
        updated_report = self.report_generator.generate_report(merged_aggregated, format_type=format_type)
        updated_report.title = f"Updated: {original_report.title}"

        self._emit("report_ready", {
            "report_id": updated_report.report_id,
            "title": updated_report.title,
            "markdown_content": updated_report.markdown_content
        })

        logger.info(f"LarpAgent completed follow-up chat updates successfully.")
        return updated_report



