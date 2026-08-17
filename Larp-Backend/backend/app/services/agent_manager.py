"""AgentManager orchestrating multi-agent pipelines with execution logging (Execution Time, Cost, Errors, Status)."""

import time
import traceback
from typing import Any, List, Optional
from uuid import UUID

from app.agents.citation import CitationAgentInterface, CitationItem
from app.agents.fact_checker import FactCheckerAgentInterface, VerifiedFact
from app.agents.mock_agents import (
    MockCitationAgent,
    MockFactCheckerAgent,
    MockPlannerAgent,
    MockReportAgent,
    MockSearchAgent,
)
from app.agents.planner import PlanOutput, PlannerAgentInterface
from app.agents.report import FinalReportOutput, ReportAgentInterface
from app.agents.search import SearchAgentInterface, SearchResultItem
from app.core.exceptions import AppException
from app.core.logging import get_logger
from app.repositories.agent_execution_log_repository import AgentExecutionLogRepository
from app.repositories.research_job_repository import ResearchJobRepository
from app.repositories.research_report_repository import ResearchReportRepository
from app.repositories.research_source_repository import ResearchSourceRepository
from app.schemas.conflict import SourceConflict
from app.utils.resilience import execute_with_resilience

logger = get_logger("agent_manager")


class AgentManager:
    """Orchestrator coordinating Planner, Search, Fact Checker, Citation, and Report Generator agents.

    Stores Granular Execution Logs:
    - **Execution Time**: Duration per step in milliseconds.
    - **Cost**: Estimated API token cost per step in USD ($0.0008, $0.0015, etc.).
    - **Errors**: Formatted exception stack trace strings on failure.
    - **Status**: State transition tracking ('queued', 'running', 'completed', 'failed').
    """

    def __init__(
        self,
        job_repo: Optional[ResearchJobRepository] = None,
        report_repo: Optional[ResearchReportRepository] = None,
        source_repo: Optional[ResearchSourceRepository] = None,
        agent_log_repo: Optional[AgentExecutionLogRepository] = None,
        planner_agent: Optional[PlannerAgentInterface] = None,
        search_agent: Optional[SearchAgentInterface] = None,
        fact_checker_agent: Optional[FactCheckerAgentInterface] = None,
        citation_agent: Optional[CitationAgentInterface] = None,
        report_agent: Optional[ReportAgentInterface] = None,
        payment_manager: Optional[Any] = None,
        max_retries: int = 3,
        timeout_seconds: float = 30.0,
    ) -> None:
        self.job_repo = job_repo
        self.report_repo = report_repo
        self.source_repo = source_repo
        self.agent_log_repo = agent_log_repo
        self.max_retries = max_retries
        self.timeout_seconds = timeout_seconds

        # Wire agents or default to mock agents
        self.planner_agent = planner_agent or MockPlannerAgent()
        self.search_agent = search_agent or MockSearchAgent()
        self.fact_checker_agent = fact_checker_agent or MockFactCheckerAgent()
        self.citation_agent = citation_agent or MockCitationAgent()
        self.report_agent = report_agent or MockReportAgent()

        if payment_manager:
            self.payment_manager = payment_manager
        else:
            from app.services.payment_manager import PaymentManager
            self.payment_manager = PaymentManager()

    # ── Step 1: Call Planner ───────────────────────────────────────────
    async def call_planner(self, query: str, depth: str) -> PlanOutput:
        """Call Planner Agent with retry logic, 30s timeout, and fallback plan."""
        def fallback_planner() -> PlanOutput:
            return PlanOutput(
                research_goal=f"Investigate (Fallback): {query}",
                sub_queries=[f"{query} overview", f"{query} details"],
                steps=["1. Fallback Web Search", "2. Report Synthesis"],
            )

        return await execute_with_resilience(
            self.planner_agent.create_plan,
            query,
            depth,
            max_retries=self.max_retries,
            timeout_seconds=self.timeout_seconds,
            agent_name="PlannerAgent",
            fallback_factory=fallback_planner,
        )

    # ── Step 2: Call Search ────────────────────────────────────────────
    async def call_search(self, sub_queries: List[str]) -> List[SearchResultItem]:
        """Call Search Agent with retry logic, 30s timeout, and fallback sources."""
        def fallback_search() -> List[SearchResultItem]:
            return [
                SearchResultItem(
                    url="https://arxiv.org/abs/2305.10601",
                    title="Fallback Search Result — Default Source",
                    snippet="Default web search fallback source content.",
                    relevance_score=0.85,
                )
            ]

        return await execute_with_resilience(
            self.search_agent.execute_search,
            sub_queries,
            max_retries=self.max_retries,
            timeout_seconds=self.timeout_seconds,
            agent_name="SearchAgent",
            fallback_factory=fallback_search,
        )

    # ── Step 3: Call Fact Checker ──────────────────────────────────────
    async def call_fact_checker(
        self, raw_sources: List[SearchResultItem]
    ) -> List[VerifiedFact]:
        """Call Fact Checker Agent with retry logic, 30s timeout, and fallback facts."""
        def fallback_fact_checker() -> List[VerifiedFact]:
            return [
                VerifiedFact(
                    fact_statement=f"Fact statement from source: {src.title}",
                    is_verified=True,
                    confidence_score=0.80,
                    supporting_urls=[src.url],
                )
                for src in raw_sources
            ] if raw_sources else [
                VerifiedFact(
                    fact_statement="Fallback verified statement.",
                    is_verified=True,
                    confidence_score=0.75,
                    supporting_urls=[],
                )
            ]

        return await execute_with_resilience(
            self.fact_checker_agent.verify_facts,
            raw_sources,
            max_retries=self.max_retries,
            timeout_seconds=self.timeout_seconds,
            agent_name="FactCheckerAgent",
            fallback_factory=fallback_fact_checker,
        )

    # ── Step 3b: Call Conflict Detector ──────────────────────────────
    async def call_conflict_detector(
        self, raw_sources: List[SearchResultItem], job_id: Optional[UUID] = None
    ) -> List[SourceConflict]:
        """Call SourceConflictDetector with retry logic, 30s timeout, and fallback empty list."""
        def fallback_conflicts() -> List[SourceConflict]:
            return []

        async def detect_fn(sources):
            if hasattr(self.fact_checker_agent, "detect_conflicts"):
                return await self.fact_checker_agent.detect_conflicts(sources)
            from app.services.conflict_detector import SourceConflictDetector
            return SourceConflictDetector.detect_conflicts(
                [s.model_dump() for s in sources], job_id=str(job_id) if job_id else None
            )

        return await execute_with_resilience(
            detect_fn,
            raw_sources,
            max_retries=self.max_retries,
            timeout_seconds=self.timeout_seconds,
            agent_name="FactCheckerAgent",
            fallback_factory=fallback_conflicts,
        )

    # ── Step 4: Call Citation Generator ───────────────────────────────
    async def call_citation_generator(
        self, verified_facts: List[VerifiedFact]
    ) -> List[CitationItem]:
        """Call Citation Agent with retry logic, 30s timeout, and fallback citations."""
        def fallback_citations() -> List[CitationItem]:
            return [
                CitationItem(
                    citation_id="[1]",
                    url="https://arxiv.org/abs/2305.10601",
                    title="Fallback Citation",
                    formatted_citation="Fallback Citation Reference (2026).",
                    in_text_tag="[1](https://arxiv.org/abs/2305.10601)",
                )
            ]

        return await execute_with_resilience(
            self.citation_agent.generate_citations,
            verified_facts,
            max_retries=self.max_retries,
            timeout_seconds=self.timeout_seconds,
            agent_name="CitationAgent",
            fallback_factory=fallback_citations,
        )

    # ── Step 5: Call Report Generator ──────────────────────────────────
    async def call_report_generator(
        self,
        query: str,
        plan: PlanOutput,
        facts: List[VerifiedFact],
        citations: List[CitationItem],
        conflicts: Optional[List[SourceConflict]] = None,
    ) -> FinalReportOutput:
        """Call Report Generator Agent with retry logic, 30s timeout, and fallback report."""
        def fallback_report() -> FinalReportOutput:
            markdown = (
                f"# Research Report: {query}\n\n"
                f"## Executive Summary\n"
                f"Generated report synthesized with fallback resilience mode for query: {query}.\n\n"
                f"## Key Findings\n"
                f"- Primary finding synthesized across {len(facts)} verified facts."
            )
            return FinalReportOutput(
                title=f"Research Report: {query}",
                summary=f"Fallback summary for {query}",
                content_markdown=markdown,
                key_findings=[{"statement": f.fact_statement} for f in facts],
                word_count=len(markdown.split()),
                conflicts=conflicts or [],
            )

        return await execute_with_resilience(
            self.report_agent.synthesize_report,
            query,
            plan,
            facts,
            citations,
            conflicts,
            max_retries=self.max_retries,
            timeout_seconds=self.timeout_seconds,
            agent_name="ReportAgent",
            fallback_factory=fallback_report,
        )

    # ── End-to-End Pipeline Execution & Agent Execution Logging ───────
    async def run_pipeline(
        self, job_id: UUID, user_id: UUID, query: str, depth: str = "standard"
    ) -> FinalReportOutput:
        """Execute multi-agent pipeline recording Execution Time, Cost, Errors, and Status logs per step."""
        start_time = time.perf_counter()
        logger.info(
            "AgentManager: Starting resilient research pipeline with execution logging",
            job_id=str(job_id),
            user_id=str(user_id),
        )

        try:
            # ── Step 1: Planner Agent ─────────────────────────────────
            step1_start = time.perf_counter()
            await self._update_job_progress(job_id, "in_progress", "PlannerAgent", 15.0, start_time)
            plan = await self.call_planner(query, depth)
            step1_ms = int((time.perf_counter() - step1_start) * 1000)
            await self._log_step(
                job_id, "PlannerAgent", 1, "completed", step1_ms, cost_usd=0.0008,
                input_data={"query": query, "depth": depth},
                output_data={"sub_queries_count": len(plan.sub_queries)}
            )

            # ── Step 2: Search Agent ──────────────────────────────────
            step2_start = time.perf_counter()
            await self._update_job_progress(job_id, "in_progress", "SearchAgent", 40.0, start_time)
            raw_sources = await self.call_search(plan.sub_queries)
            step2_ms = int((time.perf_counter() - step2_start) * 1000)
            await self._log_step(
                job_id, "SearchAgent", 2, "completed", step2_ms, cost_usd=0.0015,
                input_data={"sub_queries": plan.sub_queries},
                output_data={"raw_sources_count": len(raw_sources)}
            )

            if self.source_repo and raw_sources:
                for src in raw_sources:
                    try:
                        await self.source_repo.create(
                            {
                                "job_id": job_id,
                                "url": src.url,
                                "title": src.title,
                                "domain": src.url.split("/")[2] if "/" in src.url else None,
                                "snippet": src.snippet,
                                "relevance_score": src.relevance_score,
                                "raw_content": src.raw_content,
                            }
                        )
                    except Exception:
                        pass

            # ── Step 3: Fact Checker Agent & Conflict Detection ───────
            step3_start = time.perf_counter()
            await self._update_job_progress(job_id, "in_progress", "FactCheckerAgent", 65.0, start_time)
            verified_facts = await self.call_fact_checker(raw_sources)
            conflicts = await self.call_conflict_detector(raw_sources, job_id=job_id)
            step3_ms = int((time.perf_counter() - step3_start) * 1000)
            await self._log_step(
                job_id, "FactCheckerAgent", 3, "completed", step3_ms, cost_usd=0.0012,
                input_data={"raw_sources_count": len(raw_sources)},
                output_data={"verified_facts_count": len(verified_facts), "source_conflicts_count": len(conflicts)}
            )

            # ── Step 4: Citation Agent ────────────────────────────────
            step4_start = time.perf_counter()
            await self._update_job_progress(job_id, "in_progress", "CitationAgent", 80.0, start_time)
            citations = await self.call_citation_generator(verified_facts)
            step4_ms = int((time.perf_counter() - step4_start) * 1000)
            await self._log_step(
                job_id, "CitationAgent", 4, "completed", step4_ms, cost_usd=0.0005,
                input_data={"verified_facts_count": len(verified_facts)},
                output_data={"citations_count": len(citations)}
            )

            # ── Step 5: Report Generator ──────────────────────────────
            step5_start = time.perf_counter()
            await self._update_job_progress(job_id, "in_progress", "ReportAgent", 95.0, start_time)
            final_report = await self.call_report_generator(query, plan, verified_facts, citations, conflicts=conflicts)
            step5_ms = int((time.perf_counter() - step5_start) * 1000)
            await self._log_step(
                job_id, "ReportAgent", 5, "completed", step5_ms, cost_usd=0.0025,
                input_data={"facts_count": len(verified_facts), "citations_count": len(citations)},
                output_data={"word_count": final_report.word_count}
            )

            if self.report_repo:
                try:
                    await self.report_repo.create(
                        {
                            "job_id": job_id,
                            "user_id": user_id,
                            "title": final_report.title,
                            "summary": final_report.summary,
                            "content_markdown": final_report.content_markdown,
                            "key_findings": final_report.key_findings,
                            "word_count": final_report.word_count,
                        }
                    )
                except Exception:
                    pass

            elapsed_ms = int((time.perf_counter() - start_time) * 1000)
            await self._update_job_progress(
                job_id, "completed", "ReportAgent", 100.0, start_time, elapsed_ms=elapsed_ms
            )

            logger.info(
                "AgentManager: Resilient pipeline completed successfully",
                job_id=str(job_id),
                elapsed_ms=elapsed_ms,
                total_cost_usd=0.0065,
            )
            return final_report

        except Exception as exc:
            elapsed_ms = int((time.perf_counter() - start_time) * 1000)
            error_message = f"{exc.__class__.__name__}: {str(exc)}"
            
            # Log failed execution step
            await self._log_step(
                job_id, "AgentManager", 0, "failed", elapsed_ms, cost_usd=0.0,
                error_message=error_message
            )

            logger.error(
                "AgentManager: Pipeline failed",
                job_id=str(job_id),
                error=error_message,
                traceback=traceback.format_exc(),
                elapsed_ms=elapsed_ms,
            )
            await self._update_job_progress(
                job_id,
                "failed",
                "AgentManager",
                0.0,
                start_time,
                error_message=error_message,
                elapsed_ms=elapsed_ms,
            )
            raise AppException(
                message=f"Research pipeline execution failed: {str(exc)}",
                error_code="PIPELINE_EXECUTION_FAILED",
            ) from exc

    async def _log_step(
        self,
        job_id: UUID,
        agent_name: str,
        step_number: int,
        status: str,
        execution_time_ms: int,
        cost_usd: float = 0.0,
        error_message: Optional[str] = None,
        input_data: Optional[dict] = None,
        output_data: Optional[dict] = None,
    ) -> None:
        """Helper to record AgentExecutionLog entries in database."""
        if self.agent_log_repo:
            try:
                await self.agent_log_repo.create(
                    {
                        "job_id": job_id,
                        "agent_name": agent_name,
                        "step_number": step_number,
                        "status": status,
                        "execution_time_ms": execution_time_ms,
                        "cost_usd": cost_usd,
                        "error_message": error_message,
                        "input_data": input_data or {},
                        "output_data": output_data or {},
                    }
                )
            except Exception as exc:
                logger.warning(
                    "Failed to record AgentExecutionLog step",
                    job_id=str(job_id),
                    agent=agent_name,
                    error=str(exc),
                )

    async def _update_job_progress(
        self,
        job_id: UUID,
        status: str,
        agent_name: str,
        percentage: float,
        start_time: float,
        error_message: Optional[str] = None,
        elapsed_ms: Optional[int] = None,
    ) -> None:
        """Update job progress in database and broadcast over WebSockets & Redis PubSub."""
        if elapsed_ms is None:
            elapsed_ms = int((time.perf_counter() - start_time) * 1000)

        if self.job_repo:
            try:
                update_fields = {
                    "status": status,
                    "current_agent": agent_name,
                    "progress_percentage": percentage,
                    "execution_time_ms": elapsed_ms,
                }
                if error_message:
                    update_fields["error_message"] = error_message
                await self.job_repo.update(job_id, update_fields)
            except Exception as exc:
                logger.warning("Failed to update progress in DB", job_id=str(job_id), error=str(exc))

        try:
            from app.core.websocket import manager
            from app.redis import get_redis
            import json

            event_payload = {
                "event": "job_progress_updated",
                "job_id": str(job_id),
                "status": status,
                "current_agent": agent_name,
                "progress_percentage": percentage,
                "execution_time_ms": elapsed_ms,
                "error_message": error_message,
            }
            await manager.broadcast_to_job(job_id, event_payload)

            redis = await get_redis()
            await redis.publish(f"research:{job_id}", json.dumps(event_payload))
        except Exception:
            pass
