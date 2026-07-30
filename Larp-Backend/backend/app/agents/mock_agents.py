"""Mock implementations of agent interfaces for local testing and fallback execution without AI API keys."""

from typing import Any, Dict, List
from app.agents.base import BaseAgentState
from app.agents.planner import PlanOutput, PlannerAgentInterface
from app.agents.search import SearchAgentInterface, SearchResultItem
from app.agents.fact_checker import FactCheckerAgentInterface, VerifiedFact
from app.agents.citation import CitationAgentInterface, CitationItem
from app.agents.report import FinalReportOutput, ReportAgentInterface


class MockPlannerAgent(PlannerAgentInterface):
    """Mock implementation of PlannerAgentInterface."""

    async def create_plan(self, query: str, depth: str = "standard") -> PlanOutput:
        return PlanOutput(
            research_goal=f"Investigate: {query}",
            sub_queries=[
                f"{query} overview and fundamentals",
                f"{query} architectural scaling and performance",
                f"{query} modern industry implementation patterns",
            ],
            target_domains=["arxiv.org", "github.com", "tech-blog.com"],
            steps=["1. Web Search", "2. Fact Verification", "3. Citation Formatting", "4. Report Synthesis"],
        )

    async def execute(self, state: BaseAgentState) -> BaseAgentState:
        plan = await self.create_plan(state.get("query", ""), state.get("depth", "standard"))
        state["plan"] = plan.model_dump()
        state["current_agent"] = self.agent_name
        return state


class MockSearchAgent(SearchAgentInterface):
    """Mock implementation of SearchAgentInterface."""

    async def execute_search(
        self, sub_queries: List[str], max_results_per_query: int = 5
    ) -> List[SearchResultItem]:
        results = []
        for i, sq in enumerate(sub_queries):
            results.append(
                SearchResultItem(
                    url=f"https://arxiv.org/abs/2026.000{i+1}",
                    title=f"Research Insights on {sq}",
                    snippet=f"Key technical analysis and findings regarding {sq}.",
                    relevance_score=round(0.95 - (i * 0.05), 2),
                )
            )
        return results

    async def execute(self, state: BaseAgentState) -> BaseAgentState:
        plan_dict = state.get("plan") or {}
        sub_queries = plan_dict.get("sub_queries", [state.get("query", "")])
        results = await self.execute_search(sub_queries)
        state["raw_sources"] = [r.model_dump() for r in results]
        state["current_agent"] = self.agent_name
        return state


class MockFactCheckerAgent(FactCheckerAgentInterface):
    """Mock implementation of FactCheckerAgentInterface."""

    async def verify_facts(
        self, raw_sources: List[SearchResultItem]
    ) -> List[VerifiedFact]:
        verified = []
        for i, src in enumerate(raw_sources):
            verified.append(
                VerifiedFact(
                    fact_statement=f"Fact statement derived from source: {src.title}",
                    is_verified=True,
                    confidence_score=0.92,
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


class MockCitationAgent(CitationAgentInterface):
    """Mock implementation of CitationAgentInterface."""

    async def generate_citations(
        self, verified_facts: List[VerifiedFact]
    ) -> List[CitationItem]:
        citations = []
        for i, fact in enumerate(verified_facts):
            url = fact.supporting_urls[0] if fact.supporting_urls else "https://example.com"
            citations.append(
                CitationItem(
                    citation_id=f"[{i+1}]",
                    url=url,
                    title=f"Source Reference {i+1}",
                    formatted_citation=f"Author et al. (2026). Reference {i+1}. Retrieved from {url}",
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


class MockReportAgent(ReportAgentInterface):
    """Mock implementation of ReportAgentInterface."""

    async def synthesize_report(
        self,
        query: str,
        plan: PlanOutput,
        facts: List[VerifiedFact],
        citations: List[CitationItem],
    ) -> FinalReportOutput:
        body_markdown = (
            f"# Research Report: {query}\n\n"
            f"## Executive Summary\n"
            f"This research report evaluates {query} across {len(facts)} verified facts and {len(citations)} citations.\n\n"
            f"## Key Findings\n"
        )
        for i, f in enumerate(facts):
            body_markdown += f"- {f.fact_statement} {citations[i].in_text_tag if i < len(citations) else ''}\n"

        return FinalReportOutput(
            title=f"Research Report: {query}",
            summary=f"Executive analysis of {query}",
            content_markdown=body_markdown,
            key_findings=[{"statement": f.fact_statement} for f in facts],
            word_count=len(body_markdown.split()),
        )

    async def execute(self, state: BaseAgentState) -> BaseAgentState:
        query = state.get("query", "")
        plan = PlanOutput(**state.get("plan", {}))
        facts = [VerifiedFact(**f) for f in state.get("verified_facts", [])]
        citations = [CitationItem(**c) for c in state.get("citations", [])]

        report = await self.synthesize_report(query, plan, facts, citations)
        state["final_report"] = report.model_dump()
        state["current_agent"] = self.agent_name
        return state
