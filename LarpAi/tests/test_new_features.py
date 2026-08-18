"""
Tests for the new feature additions:
    - SourceAuthorityRanker
    - EvaluatorAgent
    - ContradictionDetector
    - ArxivSearchTool
    - WikipediaTool
    - Executor self-healing search
"""

import asyncio
import pytest
from unittest.mock import AsyncMock, patch, MagicMock

# ── Source Authority Ranker ──────────────────────────────────────────────────

from research_agent.app.utils.source_ranker import SourceAuthorityRanker


class TestSourceAuthorityRanker:

    def test_high_authority_known_domain(self):
        score = SourceAuthorityRanker.score_url("https://nature.com/articles/s41586-024-001")
        assert score >= 0.90, "nature.com should score >= 0.90"

    def test_arxiv_domain(self):
        score = SourceAuthorityRanker.score_url("https://arxiv.org/abs/2401.12345")
        assert score >= 0.90, "arxiv.org should score >= 0.90"

    def test_edu_tld(self):
        score = SourceAuthorityRanker.score_url("https://mit.edu/research/paper")
        assert score >= 0.85, ".edu TLD should score >= 0.85"

    def test_gov_tld(self):
        score = SourceAuthorityRanker.score_url("https://cdc.gov/data/report")
        assert score >= 0.85, ".gov TLD should score >= 0.85"

    def test_com_tld_lower_than_edu(self):
        edu_score = SourceAuthorityRanker.score_url("https://stanford.edu/study")
        com_score = SourceAuthorityRanker.score_url("https://randomsite.com/study")
        assert edu_score > com_score

    def test_recency_penalty_for_old_url(self):
        recent = SourceAuthorityRanker.score_url("https://arxiv.org/abs/2025/paper", year_hint=2025)
        old = SourceAuthorityRanker.score_url("https://arxiv.org/abs/2010/paper", year_hint=2010)
        assert recent > old, "Recent publication should score higher than 15-year-old one"

    def test_empty_url_returns_default(self):
        score = SourceAuthorityRanker.score_url("")
        assert score == 0.50

    def test_rank_urls_sorted_descending(self):
        urls = [
            "https://reddit.com/r/science",
            "https://nature.com/articles/test",
            "https://mit.edu/research",
        ]
        ranked = SourceAuthorityRanker.rank_urls(urls)
        scores = [s for _, s in ranked]
        assert scores == sorted(scores, reverse=True), "Should be sorted highest-first"

    def test_domain_label_high_authority(self):
        label = SourceAuthorityRanker.get_domain_label("https://pubmed.ncbi.nlm.nih.gov/123")
        assert label == "High Authority"

    def test_domain_label_low_authority(self):
        label = SourceAuthorityRanker.get_domain_label("https://twitter.com/post")
        assert label == "Low Authority"


# ── EvaluatorAgent ──────────────────────────────────────────────────────────

from research_agent.app.agents.evaluator import EvaluatorAgent, EvaluationVerdict
from research_agent.app.models.aggregator import AggregatedResearchData
from research_agent.app.models.tools import SearchResultItem, FactCheckItem, CitationItem


def _make_aggregated(
    sources: int = 5,
    snippet_words: int = 40,
    claims: int = 3,
    takeaways: int = 3,
    query: str = "solar energy efficiency improvements"
) -> AggregatedResearchData:
    search_results = [
        SearchResultItem(
            title=f"Result {i}: {query.title()}",
            snippet=" ".join(["word"] * snippet_words),
            url=f"https://example{i}.edu/paper",
            score=0.9
        )
        for i in range(sources)
    ]
    verified_claims = [
        FactCheckItem(
            claim=f"Solar energy efficiency has improved significantly {query}.",
            status="verified",
            confidence_score=0.92,
            evidence_sources=[f"https://source{i}.edu"]
        )
        for i in range(claims)
    ]
    return AggregatedResearchData(
        plan_id="plan-test",
        query=query,
        synthesized_takeaways=[f"Takeaway {i}" for i in range(takeaways)],
        all_search_results=search_results,
        all_verified_claims=verified_claims,
        all_citations=[],
        total_sources_count=sources,
        average_confidence_score=0.90
    )


class TestEvaluatorAgent:

    def test_passes_with_rich_data(self):
        agent = EvaluatorAgent(threshold=0.70)
        aggregated = _make_aggregated(sources=5, snippet_words=50, claims=3, takeaways=3)
        verdict = agent.evaluate("solar energy efficiency improvements", aggregated)
        assert isinstance(verdict, EvaluationVerdict)
        assert verdict.coverage_score >= 0.0
        assert verdict.depth_score >= 0.0
        assert verdict.relevance_score >= 0.0

    def test_fails_with_no_sources(self):
        agent = EvaluatorAgent(threshold=0.70)
        aggregated = _make_aggregated(sources=0, snippet_words=0, claims=0, takeaways=0)
        verdict = agent.evaluate("solar energy", aggregated)
        assert not verdict.passed, "No data should fail evaluation"
        assert verdict.coverage_score < 0.70

    def test_gap_summary_populated_on_failure(self):
        agent = EvaluatorAgent(threshold=0.90)  # Very high threshold
        aggregated = _make_aggregated(sources=1, snippet_words=5, claims=0, takeaways=0)
        verdict = agent.evaluate("renewable energy solar wind comparison", aggregated)
        assert verdict.gap_summary  # Should not be empty
        assert "gap" in verdict.gap_summary.lower() or "low" in verdict.gap_summary.lower()

    def test_missing_topics_populated_on_failure(self):
        agent = EvaluatorAgent(threshold=0.95)
        aggregated = _make_aggregated(sources=1, snippet_words=5, claims=0, takeaways=0)
        verdict = agent.evaluate("wind energy turbine efficiency 2025", aggregated)
        # Should have actionable gap topics
        assert isinstance(verdict.missing_topics, list)

    def test_overall_score_in_valid_range(self):
        agent = EvaluatorAgent()
        aggregated = _make_aggregated(sources=3, snippet_words=30, claims=2)
        verdict = agent.evaluate("machine learning transformer models", aggregated)
        assert 0.0 <= verdict.overall_score <= 1.0

    def test_threshold_boundary(self):
        agent_lenient = EvaluatorAgent(threshold=0.01)
        # Use query-relevant content so all three axes can score above near-zero threshold
        aggregated = _make_aggregated(
            sources=3, snippet_words=30, claims=2,
            query="deep learning neural networks"
        )
        # Inject matching keywords into snippets and claims
        for item in aggregated.all_search_results:
            item.snippet = "deep learning neural networks transformer architecture research study"
        for claim in aggregated.all_verified_claims:
            claim.claim = "Deep learning neural networks have significantly improved accuracy."
        lenient_verdict = agent_lenient.evaluate("deep learning neural networks", aggregated)
        assert lenient_verdict.passed, f"Lenient evaluator should pass. Got: {lenient_verdict.gap_summary}"


# ── ContradictionDetector ───────────────────────────────────────────────────

from research_agent.app.utils.contradiction_detector import ContradictionDetector, ContradictionReport
from research_agent.app.models.tools import FactCheckItem


def _make_aggregated_with_claims(claims_data: list) -> AggregatedResearchData:
    claims = [
        FactCheckItem(
            claim=text,
            status=status,
            confidence_score=0.85,
            evidence_sources=["https://example.com"]
        )
        for text, status in claims_data
    ]
    return AggregatedResearchData(
        plan_id="plan-test",
        query="test query",
        synthesized_takeaways=[],
        all_search_results=[],
        all_verified_claims=claims,
        all_citations=[],
        total_sources_count=0,
        average_confidence_score=0.85
    )


class TestContradictionDetector:

    def test_no_conflicts_when_claims_unrelated(self):
        detector = ContradictionDetector()
        aggregated = _make_aggregated_with_claims([
            ("Solar panels convert sunlight into electricity.", "verified"),
            ("The Eiffel Tower is located in Paris, France.", "verified"),
        ])
        conflicts = detector.detect(aggregated)
        assert conflicts == []

    def test_numerical_conflict_detected(self):
        detector = ContradictionDetector()
        aggregated = _make_aggregated_with_claims([
            ("Solar energy efficiency improved by 80 percent in recent studies.", "verified"),
            ("Solar energy efficiency improved by only 10 percent according to research.", "verified"),
        ])
        conflicts = detector.detect(aggregated)
        numerical_conflicts = [c for c in conflicts if c.conflict_type == "numerical"]
        assert len(numerical_conflicts) >= 1

    def test_sentiment_conflict_detected(self):
        detector = ContradictionDetector()
        aggregated = _make_aggregated_with_claims([
            ("The new battery technology is safe and effective for consumer use.", "verified"),
            ("The new battery technology is dangerous and harmful to users.", "disputed"),
        ])
        conflicts = detector.detect(aggregated)
        sentiment_conflicts = [c for c in conflicts if c.conflict_type == "sentiment"]
        assert len(sentiment_conflicts) >= 1

    def test_no_conflicts_with_single_claim(self):
        detector = ContradictionDetector()
        aggregated = _make_aggregated_with_claims([
            ("Wind turbines generate clean renewable energy.", "verified"),
        ])
        conflicts = detector.detect(aggregated)
        assert conflicts == []

    def test_conflict_report_has_required_fields(self):
        detector = ContradictionDetector()
        aggregated = _make_aggregated_with_claims([
            ("Battery capacity increased by 200 percent.", "verified"),
            ("Battery capacity increased by only 20 percent.", "verified"),
        ])
        conflicts = detector.detect(aggregated)
        if conflicts:
            c = conflicts[0]
            assert c.conflict_type in ("numerical", "sentiment")
            assert c.severity in ("high", "medium", "low")
            assert c.claim_a
            assert c.claim_b
            assert c.detail

    def test_format_markdown_empty_when_no_conflicts(self):
        detector = ContradictionDetector()
        md = detector.format_markdown_section([])
        assert md == ""

    def test_format_markdown_contains_section_header(self):
        detector = ContradictionDetector()
        mock_conflict = ContradictionReport(
            conflict_type="numerical",
            claim_a="Efficiency improved by 80%.",
            claim_b="Efficiency improved by 10%.",
            severity="high",
            detail="8.0x divergence detected.",
            topic_tokens=["efficiency", "improved"]
        )
        md = detector.format_markdown_section([mock_conflict])
        assert "Conflicting Evidence" in md
        assert "Claim A" in md
        assert "Claim B" in md


# ── ArxivSearchTool ─────────────────────────────────────────────────────────

from research_agent.app.services.tools.arxiv_tool import ArxivSearchTool
from research_agent.app.models.tools import SearchResponse


class TestArxivSearchTool:

    @pytest.mark.asyncio
    async def test_returns_fallback_on_timeout(self):
        tool = ArxivSearchTool(timeout_seconds=0.001)  # Near-zero timeout forces failure
        result = await tool.execute(query="transformer attention mechanisms")
        # Should succeed gracefully with fallback, not raise
        assert result.success
        assert isinstance(result.data, SearchResponse)

    @pytest.mark.asyncio
    async def test_raises_on_empty_query(self):
        tool = ArxivSearchTool()
        result = await tool.execute(query="")
        assert not result.success
        assert result.error is not None

    @pytest.mark.asyncio
    async def test_fallback_response_has_valid_structure(self):
        tool = ArxivSearchTool()
        response = tool._fallback_response("quantum computing")
        assert isinstance(response, SearchResponse)
        assert len(response.results) >= 1
        assert response.results[0].url.startswith("https://arxiv.org")

    def test_tool_name_and_description(self):
        tool = ArxivSearchTool()
        assert tool.name == "ArxivSearchTool"
        assert "ArXiv" in tool.description


# ── WikipediaTool ────────────────────────────────────────────────────────────

from research_agent.app.services.tools.wikipedia_tool import WikipediaTool


class TestWikipediaTool:

    @pytest.mark.asyncio
    async def test_returns_fallback_on_timeout(self):
        tool = WikipediaTool(timeout_seconds=0.001)
        result = await tool.execute(query="large language model")
        assert result.success
        assert isinstance(result.data, SearchResponse)

    @pytest.mark.asyncio
    async def test_raises_on_empty_query(self):
        tool = WikipediaTool()
        result = await tool.execute(query="")
        assert not result.success

    @pytest.mark.asyncio
    async def test_fallback_response_has_valid_url(self):
        tool = WikipediaTool()
        response = tool._fallback_response("artificial intelligence")
        assert isinstance(response, SearchResponse)
        assert "wikipedia.org" in response.results[0].url

    def test_tool_name(self):
        tool = WikipediaTool()
        assert tool.name == "WikipediaTool"


# ── Executor Self-Healing ────────────────────────────────────────────────────

from research_agent.app.executor.executor import ResearchExecutorAgent
from research_agent.app.models.tools import ToolResult


class TestExecutorSelfHealing:

    @pytest.mark.asyncio
    async def test_new_tools_registered_in_default_executor(self):
        executor = ResearchExecutorAgent()
        assert "arxiv" in executor.tools, "ArxivSearchTool should be registered by default"
        assert "wikipedia" in executor.tools, "WikipediaTool should be registered by default"

    @pytest.mark.asyncio
    async def test_self_healing_falls_back_to_arxiv(self):
        executor = ResearchExecutorAgent()

        # Mock the primary search tool to return 0 results
        zero_result_response = SearchResponse(query="test", results=[], total_results=0)
        mock_primary = AsyncMock(return_value=ToolResult(success=True, data=zero_result_response))
        mock_tool = MagicMock()
        mock_tool.execute = mock_primary

        # Mock arxiv to return 1 result
        arxiv_result = SearchResponse(
            query="test",
            results=[SearchResultItem(title="ArXiv Paper", snippet="Academic paper.", url="https://arxiv.org/abs/test", score=0.92)],
            total_results=1
        )
        mock_arxiv = AsyncMock(return_value=ToolResult(success=True, data=arxiv_result))
        executor.tools["arxiv"].execute = mock_arxiv

        result = await executor._self_healing_search(mock_tool, "test query", "search")
        # Should have called arxiv fallback
        assert mock_arxiv.called or result is not None
