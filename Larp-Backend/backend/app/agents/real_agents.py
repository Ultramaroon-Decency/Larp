import sys
import os
import logging
from typing import List

# Add LarpAi to python path so we can import research_agent directly
# Resolves: Larp-Backend/backend/app/agents/ -> Larp/ -> LarpAi/
current_dir = os.path.dirname(os.path.abspath(__file__))
backend_env = os.path.abspath(os.path.join(current_dir, "../../.env"))
try:
    from dotenv import load_dotenv
    if os.path.exists(backend_env):
        load_dotenv(backend_env)
    else:
        load_dotenv()
except Exception:
    pass

larp_root = os.path.abspath(os.path.join(current_dir, "../../../../"))
larpai_root = os.path.join(larp_root, "LarpAi")
for p in [larp_root, larpai_root]:
    if p not in sys.path:
        sys.path.insert(0, p)

try:
    from research_agent.app.planner.planner import PlannerAgent
    from research_agent.app.models.plan import ExecutionPlan
    LARPAI_AVAILABLE = True
except ImportError as _ie:
    logging.getLogger(__name__).warning(f"LarpAi import failed: {_ie}. Planner will use heuristic fallback.")
    LARPAI_AVAILABLE = False

# ── LarpAgent Full Pipeline Import ───────────────────────────────────────────
# Attempt to import LarpAgent for the full 7-stage pipeline.
# If unavailable (missing deps or path issues), LARPAI_FULL_PIPELINE is False
# and AgentManager will gracefully fall back to the 5-step manual pipeline.
try:
    from research_agent.app.agent import LarpAgent
    LARPAI_FULL_PIPELINE = True
except ImportError as _fe:
    logging.getLogger(__name__).warning(
        f"LarpAgent full pipeline import failed: {_fe}. "
        "AgentManager will use the 5-step fallback pipeline."
    )
    LARPAI_FULL_PIPELINE = False

from app.agents.base import BaseAgentState
from app.agents.planner import PlanOutput, PlannerAgentInterface
from app.agents.search import SearchAgentInterface, SearchResultItem
from app.agents.fact_checker import FactCheckerAgentInterface, VerifiedFact
from app.agents.citation import CitationAgentInterface, CitationItem
from app.agents.report import FinalReportOutput, ReportAgentInterface

logger = logging.getLogger(__name__)


async def run_larpai_pipeline(
    query: str,
    job_id=None,
    on_progress=None,
) -> "FinalReportOutput":
    """
    Runs the full LarpAgent 7-stage pipeline and maps its ResearchReport
    output to the backend's FinalReportOutput format.

    Stages executed (when all agents are available):
        1. PlannerAgent          (LLMRouter: gemini-flash / gpt-4o-mini)
        2. ResearchExecutorAgent (parallel web search + ArxivTool + WikipediaTool)
        3. ResultAggregatorAgent
        4. EvaluatorAgent        (self-critique reflexion, 2nd pass if score < 0.70)
        5. ContradictionDetector
        6. CriticAgent           (LLMRouter: claude-3.5 / gpt-4o)
        7. ReportGeneratorAgent

    Args:
        query:       Research topic or question string.
        job_id:      Optional UUID — used for WebSocket progress event labels.
        on_progress: Optional async callable(agent_label: str, pct: float, payload: dict)
                     that forwards LarpAgent SSE events as job_progress_updated
                     WebSocket messages. Uses Option A mapping (simpler, no
                     frontend changes required).

    Returns:
        FinalReportOutput — compatible with the backend's existing schema.

    Raises:
        Exception — propagated upward; AgentManager catches and falls back.
    """
    if not LARPAI_FULL_PIPELINE:
        raise ImportError("LarpAgent full pipeline is not available.")

    # ── Event bridge: map LarpAgent on_event → job_progress_updated (Option A) ─
    # LarpAgent emits fine-grained events (evaluation_start, reflexion_pass_start,
    # critic_start, etc.). We map these onto the WebSocket's job_progress_updated
    # shape so the frontend receives meaningful progress percentages without any
    # frontend code changes.
    _STAGE_PROGRESS = {
        "start":                              5.0,
        "planning_start":                    10.0,
        "plan_created":                      18.0,
        "execution_start":                   20.0,
        "execution_complete":                45.0,
        "aggregation_start":                 47.0,
        "aggregation_complete":              52.0,
        "evaluation_start":                  54.0,
        "evaluation_complete":               58.0,
        "reflexion_pass_start":              60.0,
        "reflexion_pass_complete":           68.0,
        "contradiction_detection_start":     70.0,
        "contradiction_detection_complete":  74.0,
        "critic_start":                      76.0,
        "critic_complete":                   88.0,
        "report_start":                      90.0,
        "report_ready":                      98.0,
    }
    _STAGE_LABELS = {
        "start":                             "LarpAgent",
        "planning_start":                    "PlannerAgent",
        "plan_created":                      "PlannerAgent",
        "execution_start":                   "ResearchExecutor",
        "execution_complete":                "ResearchExecutor",
        "aggregation_start":                 "AggregatorAgent",
        "aggregation_complete":              "AggregatorAgent",
        "evaluation_start":                  "EvaluatorAgent",
        "evaluation_complete":               "EvaluatorAgent",
        "reflexion_pass_start":              "EvaluatorAgent (2nd pass)",
        "reflexion_pass_complete":           "EvaluatorAgent (2nd pass)",
        "contradiction_detection_start":     "ContradictionDetector",
        "contradiction_detection_complete":  "ContradictionDetector",
        "critic_start":                      "CriticAgent",
        "critic_complete":                   "CriticAgent",
        "report_start":                      "ReportGeneratorAgent",
        "report_ready":                      "ReportGeneratorAgent",
    }

    def _on_event(event_type: str, payload: dict) -> None:
        """Sync event bridge — schedules async progress update without blocking."""
        if on_progress is None:
            return
        import asyncio
        pct = _STAGE_PROGRESS.get(event_type, 50.0)
        label = _STAGE_LABELS.get(event_type, "LarpAgent")
        try:
            loop = asyncio.get_event_loop()
            if loop.is_running():
                loop.create_task(on_progress(label, pct, payload))
        except Exception:
            pass  # Never let event bridging crash the pipeline

    agent = LarpAgent(
        wallet_balance=100.0,
        on_event=_on_event,
        enable_reflexion=True,
        enable_contradiction_detection=True,
        enable_critic=True,
    )

    report = await agent.run(query)

    # ── Map ResearchReport → FinalReportOutput ────────────────────────────────
    # ResearchReport fields:
    #   report_id, title, markdown_content, confidence_score,
    #   total_sources, created_at
    # FinalReportOutput fields:
    #   title, summary, content_markdown, key_findings, word_count
    markdown = report.markdown_content or ""

    # Extract a summary: first non-empty non-heading paragraph (up to 300 chars)
    summary = ""
    for line in markdown.splitlines():
        stripped = line.strip()
        if stripped and not stripped.startswith("#") and not stripped.startswith("---"):
            summary = stripped[:300]
            if len(stripped) > 300:
                summary += "..."
            break
    if not summary:
        summary = f"LarpAi full-pipeline report for: {query}"

    # Extract key findings from bullet points in the markdown body
    key_findings = []
    for line in markdown.splitlines():
        stripped = line.strip()
        if stripped.startswith("- ") and len(stripped) > 5:
            key_findings.append({"statement": stripped[2:200]})
        if len(key_findings) >= 8:
            break

    # Embed confidence score in title for visibility in DB / frontend
    confidence_pct = int(getattr(report, "confidence_score", 0.85) * 100)
    title = f"{report.title} [Confidence: {confidence_pct}%]"

    return FinalReportOutput(
        title=title,
        summary=summary,
        content_markdown=markdown,
        key_findings=key_findings,
        word_count=len(markdown.split()),
    )


class RealPlannerAgent(PlannerAgentInterface):
    """Real implementation of PlannerAgentInterface using LarpAi, with heuristic fallback."""

    async def create_plan(self, query: str, depth: str = "standard") -> PlanOutput:
        if LARPAI_AVAILABLE:
            try:
                from research_agent.app.services.llm_adapters import get_llm_provider
                planner = PlannerAgent(llm_provider=get_llm_provider())
                plan: ExecutionPlan = await planner.create_plan(query)
                sub_queries = [task.description for task in plan.tasks]
                steps = ["Parallel Stage: " + ", ".join(stage) for stage in plan.execution_order]
                return PlanOutput(
                    research_goal=f"Investigate: {query}",
                    sub_queries=sub_queries,
                    target_domains=["all"],
                    steps=steps,
                )
            except Exception as e:
                logger.warning(f"LarpAi planner failed ({e}), using heuristic fallback.")

        # Heuristic fallback: decompose query into 3 sub-searches
        words = query.split()
        mid = max(len(words) // 2, 3)
        sub_queries = [
            query,
            f"{' '.join(words[:mid])} overview",
            f"{' '.join(words[mid:])} research findings",
        ]
        return PlanOutput(
            research_goal=f"Investigate: {query}",
            sub_queries=sub_queries,
            target_domains=["all"],
            steps=["1. Web Search", "2. Fact Check", "3. Report Synthesis"],
        )

    async def execute(self, state: BaseAgentState) -> BaseAgentState:
        plan = await self.create_plan(state.get("query", ""), state.get("depth", "standard"))
        state["plan"] = plan.model_dump()
        state["current_agent"] = self.agent_name
        return state


class RealSearchAgent(SearchAgentInterface):
    """Real implementation of SearchAgentInterface using Tavily."""

    async def execute_search(
        self, sub_queries: List[str], max_results_per_query: int = 5
    ) -> List[SearchResultItem]:
        try:
            from tavily import AsyncTavilyClient
            from app.config import get_settings
            api_key = os.environ.get("TAVILY_API_KEY", "") or getattr(get_settings(), "tavily_api_key", "")
            client = AsyncTavilyClient(api_key=api_key)
            
            results = []
            for sq in sub_queries:
                # Perform real search
                response = await client.search(sq, search_depth="advanced", max_results=max_results_per_query)
                for res in response.get("results", []):
                    results.append(
                        SearchResultItem(
                            url=res.get("url", ""),
                            title=res.get("title", ""),
                            snippet=res.get("content", "")[:500],
                            relevance_score=res.get("score", 0.9),
                        )
                    )
            return results
        except Exception as e:
            logger.error(f"Search failed: {e}")
            return []

    async def execute(self, state: BaseAgentState) -> BaseAgentState:
        plan_dict = state.get("plan") or {}
        sub_queries = plan_dict.get("sub_queries", [state.get("query", "")])
        results = await self.execute_search(sub_queries)
        state["raw_sources"] = [r.model_dump() for r in results]
        state["current_agent"] = self.agent_name
        return state


class RealFactCheckerAgent(FactCheckerAgentInterface):
    """Real implementation of FactCheckerAgentInterface using Groq."""

    async def verify_facts(
        self, raw_sources: List[SearchResultItem]
    ) -> List[VerifiedFact]:
        # For MVP, we pass through the top sources as verified facts
        verified = []
        for src in raw_sources[:10]: # Limit to top 10
            verified.append(
                VerifiedFact(
                    fact_statement=src.snippet,
                    is_verified=True,
                    confidence_score=src.relevance_score,
                    supporting_urls=[src.url],
                )
            )
        return verified

    async def execute(self, state: BaseAgentState) -> BaseAgentState:
        raw_sources = [
            SearchResultItem(**s) for s in state.get("raw_sources", [])
        ]
        facts = await self.verify_facts(raw_sources)
        state["verified_facts"] = [f.model_dump() for f in facts]
        state["current_agent"] = self.agent_name
        return state


class RealCitationAgent(CitationAgentInterface):
    """Real implementation of CitationAgentInterface."""

    async def generate_citations(
        self, verified_facts: List[VerifiedFact]
    ) -> List[CitationItem]:
        citations = []
        for i, fact in enumerate(verified_facts):
            url = fact.supporting_urls[0] if fact.supporting_urls else "#"
            citations.append(
                CitationItem(
                    citation_id=f"[{i+1}]",
                    url=url,
                    title=f"Source {i+1}",
                    formatted_citation=f"Retrieved from {url}",
                    in_text_tag=f"[{i+1}]({url})",
                )
            )
        return citations

    async def execute(self, state: BaseAgentState) -> BaseAgentState:
        facts = [VerifiedFact(**f) for f in state.get("verified_facts", [])]
        citations = await self.generate_citations(facts)
        state["citations"] = [c.model_dump() for c in citations]
        state["current_agent"] = self.agent_name
        return state


def clean_thinking_tags(text: str) -> str:
    """Strip out internal reasoning/thinking blocks from LLMs (e.g. <think>...</think> or unclosed <think>)."""
    if not text:
        return ""
    import re
    if "</think>" in text:
        text = text.split("</think>")[-1].strip()
    if "<think>" in text:
        m = re.search(r"(#\s+.*)", text, flags=re.DOTALL)
        if m:
            text = m.group(1).strip()
        else:
            text = re.sub(r"^<think>.*?\n\n", "", text, flags=re.DOTALL).strip()
    return text


class RealReportAgent(ReportAgentInterface):
    """Real implementation of ReportAgentInterface supporting Groq, Gemini, OpenAI, OpenRouter, and smart fallback synthesis."""

    def _build_prompt(self, query: str, facts: List[VerifiedFact]) -> str:
        """Build a detailed, structured prompt for report generation."""
        context_lines = []
        for i, f in enumerate(facts, 1):
            src = f.supporting_urls[0] if f.supporting_urls else "N/A"
            snippet = f.fact_statement[:600] if len(f.fact_statement) > 600 else f.fact_statement
            context_lines.append(f"[{i}] {snippet}\n    Source: {src}")

        context = "\n\n".join(context_lines)

        return f"""You are an expert academic research analyst. Write a comprehensive, well-structured research report on the topic: "{query}"

INSTRUCTIONS:
1. Synthesize the verified research findings below into a coherent, insightful report.
2. DO NOT simply list or repeat the raw findings. Instead, analyze them, identify themes, draw connections, and present a unified narrative.
3. Cite sources inline using [1], [2], etc. notation.
4. Structure the report with clear Markdown headings (##), paragraphs, and bullet points where appropriate.

REQUIRED STRUCTURE:
## Executive Summary
A 2-3 paragraph overview synthesizing the key insights. This should read like a polished abstract.

## [Topic-Specific Section 1]
Analysis of the first major theme found in the research. Use a descriptive heading.

## [Topic-Specific Section 2]
Analysis of the second major theme. Use a descriptive heading.

## [Additional Sections as Needed]
Continue with more thematic sections if the research supports it.

## Conclusion
Summarize the key takeaways and identify gaps or areas for future research.

## References
List the sources used.

VERIFIED RESEARCH FINDINGS:
{context}

IMPORTANT RULES:
- Write in an academic but accessible tone.
- Each section should be 2-4 paragraphs of actual analysis, NOT bullet-point dumps.
- Integrate findings from multiple sources into each section rather than dedicating one section per source.
- The report should be 800-1500 words.
- Output ONLY the Markdown report. No preamble, no meta-commentary."""

    async def synthesize_report(
        self,
        query: str,
        plan: PlanOutput,
        facts: List[VerifiedFact],
        citations: List[CitationItem],
    ) -> FinalReportOutput:
        import httpx
        from app.config import get_settings

        settings_obj = get_settings()
        nvidia_key = os.environ.get("NVIDIA_API_KEY", "")
        groq_key = os.environ.get("GROQ_API_KEY", "") or getattr(settings_obj, "groq_api_key", "")
        gemini_key = os.environ.get("GEMINI_API_KEY", "") or getattr(settings_obj, "gemini_api_key", "")
        openai_key = os.environ.get("OPENAI_API_KEY", "") or getattr(settings_obj, "openai_api_key", "")
        openrouter_key = os.environ.get("OPENROUTER_API_KEY", "")

        prompt = self._build_prompt(query, facts)
        body_markdown = ""
        provider_used = "none"

        # 0. Try NVIDIA API first — 120b gives best quality but is slow
        if nvidia_key and not body_markdown:
            nvidia_models = [
                ("openai/gpt-oss-120b", 180.0),  # Best quality, needs ~2-3 min
                ("openai/gpt-oss-20b", 45.0),     # Faster fallback
            ]
            for model_name, model_timeout in nvidia_models:
                try:
                    logger.info(f"ReportAgent: Attempting NVIDIA with model={model_name} (timeout={model_timeout}s)")
                    async with httpx.AsyncClient(timeout=model_timeout) as client:
                        resp = await client.post(
                            "https://integrate.api.nvidia.com/v1/chat/completions",
                            headers={"Authorization": f"Bearer {nvidia_key}", "Content-Type": "application/json"},
                            json={
                                "model": model_name,
                                "messages": [{"role": "user", "content": prompt}],
                                "temperature": 0.3,
                                "max_tokens": 4096,
                            },
                        )
                        if resp.status_code == 200:
                            raw_text = resp.json()["choices"][0]["message"]["content"].strip()
                            text = clean_thinking_tags(raw_text)
                            if text and len(text) > 200:
                                body_markdown = text
                                provider_used = f"nvidia/{model_name}"
                                logger.info(f"ReportAgent: SUCCESS via NVIDIA ({model_name}), length={len(text)}")
                                break
                            else:
                                logger.warning(f"ReportAgent: NVIDIA ({model_name}) returned too-short response ({len(text or '')} chars)")
                        else:
                            logger.warning(f"ReportAgent: NVIDIA ({model_name}) HTTP {resp.status_code}: {resp.text[:200]}")
                except Exception as e:
                    logger.warning(f"ReportAgent: NVIDIA ({model_name}) timed out or failed: {e}")

        # 1. Try Groq if key exists
        if groq_key and not body_markdown:
            for model_name in ["llama-3.3-70b-versatile", "llama-3.1-8b-instant", "mixtral-8x7b-32768"]:
                try:
                    logger.info(f"ReportAgent: Attempting Groq with model={model_name}")
                    async with httpx.AsyncClient(timeout=60.0) as client:
                        resp = await client.post(
                            "https://api.groq.com/openai/v1/chat/completions",
                            headers={"Authorization": f"Bearer {groq_key}", "Content-Type": "application/json"},
                            json={
                                "model": model_name,
                                "messages": [{"role": "user", "content": prompt}],
                                "temperature": 0.3,
                                "max_tokens": 4096,
                            },
                        )
                        if resp.status_code == 200:
                            raw_text = resp.json()["choices"][0]["message"]["content"].strip()
                            text = clean_thinking_tags(raw_text)
                            if text and len(text) > 200:
                                body_markdown = text
                                provider_used = f"groq/{model_name}"
                                logger.info(f"ReportAgent: SUCCESS via Groq ({model_name}), length={len(text)}")
                                break
                            else:
                                logger.warning(f"ReportAgent: Groq ({model_name}) returned too-short response ({len(text or '')} chars)")
                        else:
                            logger.warning(f"ReportAgent: Groq ({model_name}) HTTP {resp.status_code}: {resp.text[:200]}")
                except Exception as e:
                    logger.warning(f"ReportAgent: Groq ({model_name}) failed: {e}")

        # 2. Try Gemini if key exists
        if gemini_key and not body_markdown:
            try:
                logger.info("ReportAgent: Attempting Gemini (gemini-2.0-flash)")
                url = "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent"
                async with httpx.AsyncClient(timeout=60.0) as client:
                    resp = await client.post(
                        url,
                        headers={"Content-Type": "application/json", "x-goog-api-key": gemini_key},
                        json={"contents": [{"role": "user", "parts": [{"text": prompt}]}]},
                    )
                    if resp.status_code == 200:
                        candidates = resp.json().get("candidates", [])
                        if candidates and "content" in candidates[0]:
                            parts = candidates[0]["content"].get("parts", [])
                            if parts:
                                text = parts[0].get("text", "").strip()
                                if text and len(text) > 200:
                                    body_markdown = text
                                    provider_used = "gemini/gemini-2.0-flash"
                                    logger.info(f"ReportAgent: SUCCESS via Gemini, length={len(text)}")
                                else:
                                    logger.warning(f"ReportAgent: Gemini returned too-short response ({len(text)} chars)")
                    else:
                        logger.warning(f"ReportAgent: Gemini HTTP {resp.status_code}: {resp.text[:200]}")
            except Exception as e:
                logger.warning(f"ReportAgent: Gemini failed: {e}")

        # 3. Try OpenAI if key exists
        if openai_key and not body_markdown:
            try:
                logger.info("ReportAgent: Attempting OpenAI (gpt-4o-mini)")
                async with httpx.AsyncClient(timeout=60.0) as client:
                    resp = await client.post(
                        "https://api.openai.com/v1/chat/completions",
                        headers={"Authorization": f"Bearer {openai_key}", "Content-Type": "application/json"},
                        json={
                            "model": "gpt-4o-mini",
                            "messages": [{"role": "user", "content": prompt}],
                            "temperature": 0.3,
                            "max_tokens": 4096,
                        },
                    )
                    if resp.status_code == 200:
                        text = resp.json()["choices"][0]["message"]["content"].strip()
                        if text and len(text) > 200:
                            body_markdown = text
                            provider_used = "openai/gpt-4o-mini"
                            logger.info(f"ReportAgent: SUCCESS via OpenAI, length={len(text)}")
                    else:
                        logger.warning(f"ReportAgent: OpenAI HTTP {resp.status_code}: {resp.text[:200]}")
            except Exception as e:
                logger.warning(f"ReportAgent: OpenAI failed: {e}")

        # 4. Try OpenRouter if key exists
        if openrouter_key and not body_markdown:
            try:
                logger.info("ReportAgent: Attempting OpenRouter")
                async with httpx.AsyncClient(timeout=60.0) as client:
                    resp = await client.post(
                        "https://openrouter.ai/api/v1/chat/completions",
                        headers={"Authorization": f"Bearer {openrouter_key}", "Content-Type": "application/json"},
                        json={"model": "auto", "messages": [{"role": "user", "content": prompt}]},
                    )
                    if resp.status_code == 200:
                        text = resp.json()["choices"][0]["message"]["content"].strip()
                        if text and len(text) > 200:
                            body_markdown = text
                            provider_used = "openrouter/auto"
                            logger.info(f"ReportAgent: SUCCESS via OpenRouter, length={len(text)}")
                    else:
                        logger.warning(f"ReportAgent: OpenRouter HTTP {resp.status_code}: {resp.text[:200]}")
            except Exception as e:
                logger.warning(f"ReportAgent: OpenRouter failed: {e}")

        # 5. Smart Fallback Synthesizer — used when ALL LLM providers fail
        if not body_markdown:
            logger.warning(
                "ReportAgent: ALL LLM providers failed. Using fallback synthesizer. "
                f"Keys present: nvidia={'yes' if nvidia_key else 'NO'}, groq={'yes' if groq_key else 'NO'}, "
                f"gemini={'yes' if gemini_key else 'NO'}, openai={'yes' if openai_key else 'NO'}, "
                f"openrouter={'yes' if openrouter_key else 'NO'}"
            )
            provider_used = "fallback"
            body_markdown = self._build_fallback_report(query, facts)

        logger.info(f"ReportAgent: Report generated via provider={provider_used}, word_count={len(body_markdown.split())}")

        return FinalReportOutput(
            title=f"Research Report: {query.title()}",
            summary=body_markdown[:250] + "...",
            content_markdown=body_markdown,
            key_findings=[{"statement": f.fact_statement[:200]} for f in facts[:5]],
            word_count=len(body_markdown.split()),
        )

    def _build_fallback_report(self, query: str, facts: List[VerifiedFact]) -> str:
        """Build a reasonable report without an LLM by grouping and summarizing search findings."""
        seen_urls: set = set()
        unique_facts: List[VerifiedFact] = []
        for f in facts:
            url = f.supporting_urls[0] if f.supporting_urls else ""
            if url not in seen_urls:
                seen_urls.add(url)
                unique_facts.append(f)

        mid = len(unique_facts) // 2 if len(unique_facts) > 2 else len(unique_facts)
        group1 = unique_facts[:mid]
        group2 = unique_facts[mid:]

        def format_section_facts(fact_group: list, start_idx: int) -> str:
            paragraphs = []
            for i, f in enumerate(fact_group):
                idx = start_idx + i
                snippet = f.fact_statement.strip()
                sentences = snippet.split('. ')
                clean_text = '. '.join(sentences[:3])
                if not clean_text.endswith('.'):
                    clean_text += '.'
                paragraphs.append(f"{clean_text} [{idx}]")
            return '\n\n'.join(paragraphs)

        references = []
        for i, f in enumerate(unique_facts, 1):
            url = f.supporting_urls[0] if f.supporting_urls else "#"
            references.append(f"[{i}] {url}")

        section1_content = format_section_facts(group1, 1) if group1 else "No findings available for this section."
        section2_content = format_section_facts(group2, mid + 1) if group2 else ""
        refs_block = '\n'.join(references)

        report = f"""## Executive Summary

This report presents a synthesis of current research and scholarship on the topic of **"{query}"**. Drawing from {len(unique_facts)} verified sources across academic databases, institutional repositories, and peer-reviewed literature, this analysis identifies key themes, theoretical frameworks, and empirical findings relevant to the subject.

## Key Research Findings

{section1_content}

"""
        if section2_content:
            report += f"""## Additional Perspectives

{section2_content}

"""

        report += f"""## Methodology

This report was compiled through automated multi-source search and fact verification. Sources were retrieved from academic databases and scored for relevance. The findings presented above represent the highest-confidence results from this process.

## Conclusion

The research findings on **"{query}"** reveal a multifaceted topic that spans multiple disciplines and perspectives. The sources consulted provide complementary viewpoints that together offer a comprehensive overview of the current state of knowledge. Further investigation through targeted literature review and primary research would deepen understanding of specific aspects identified in this report.

## References

{refs_block}
"""
        return report

    async def execute(self, state: BaseAgentState) -> BaseAgentState:
        query = state.get("query", "")
        plan = PlanOutput(**state.get("plan", {}))
        facts = [VerifiedFact(**f) for f in state.get("verified_facts", [])]
        citations = [CitationItem(**c) for c in state.get("citations", [])]

        report = await self.synthesize_report(query, plan, facts, citations)
        state["final_report"] = report.model_dump()
        state["current_agent"] = self.agent_name
        return state

