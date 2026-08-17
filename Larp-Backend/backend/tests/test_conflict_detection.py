"""Comprehensive tests for Source Conflict Detection system (ClaimNormalizer, SourceConflictDetector, AgentManager integration, and Report synthesis)."""

import pytest
from uuid import uuid4
from app.schemas.conflict import ConflictSeverity, ConflictStatus, SourceConflict
from app.services.conflict_detector import ClaimNormalizer, SourceConflictDetector
from app.agents.search import SearchResultItem
from app.agents.fact_checker import VerifiedFact
from app.agents.mock_agents import MockFactCheckerAgent, MockReportAgent
from app.agents.planner import PlanOutput
from app.agents.citation import CitationItem
from app.services.agent_manager import AgentManager


def test_1_identical_claims_no_conflict():
    """Requirement 1: Two identical claims produce no conflict."""
    sources = [
        {"title": "Source 1", "snippet": "Company X generated $10B revenue in 2025.", "url": "https://source1.com"},
        {"title": "Source 2", "snippet": "Company X generated $10B revenue in 2025.", "url": "https://source2.com"},
    ]
    conflicts = SourceConflictDetector.detect_conflicts(sources)
    assert len(conflicts) == 0


def test_2_different_formatting_no_conflict():
    """Requirement 2: Same claim with different currency formatting produces no conflict."""
    sources = [
        {"title": "Source A", "snippet": "Company X generated $10B revenue in 2025.", "url": "https://sourceA.com"},
        {"title": "Source B", "snippet": "Company X 2025 revenue reached 10 billion dollars.", "url": "https://sourceB.com"},
    ]
    conflicts = SourceConflictDetector.detect_conflicts(sources)
    assert len(conflicts) == 0


def test_3_contradictory_numerical_values_conflict_detected():
    """Requirement 3: Clearly contradictory numerical values trigger conflict detection."""
    sources = [
        {"title": "Source A", "snippet": "Company X generated $10B revenue in 2025.", "url": "https://sourceA.com"},
        {"title": "Source B", "snippet": "Company X generated $12B revenue in 2025.", "url": "https://sourceB.com"},
    ]
    conflicts = SourceConflictDetector.detect_conflicts(sources)
    assert len(conflicts) == 1
    conflict = conflicts[0]
    assert conflict.conflicting_values["source_a"] == "$10.0B"
    assert conflict.conflicting_values["source_b"] == "$12.0B"
    assert conflict.severity in [ConflictSeverity.MEDIUM, ConflictSeverity.HIGH]


def test_4_contradictory_dates_conflict_detected():
    """Requirement 4: Contradictory dates trigger conflict detection."""
    sources = [
        {"title": "Source A", "snippet": "Company X launched in 2020.", "url": "https://sourceA.com"},
        {"title": "Source B", "snippet": "Company X launched in 2022.", "url": "https://sourceB.com"},
    ]
    conflicts = SourceConflictDetector.detect_conflicts(sources)
    assert len(conflicts) == 1
    conflict = conflicts[0]
    assert conflict.conflicting_values["source_a"] == "2020"
    assert conflict.conflicting_values["source_b"] == "2022"


def test_5_different_non_contradictory_facts_no_conflict():
    """Requirement 5: Different facts that describe separate metrics are not classified as conflicts."""
    sources = [
        {"title": "Source A", "snippet": "Company X revenue increased by 20% in 2025.", "url": "https://sourceA.com"},
        {"title": "Source B", "snippet": "Company X market cap reached $100B in 2025.", "url": "https://sourceB.com"},
    ]
    conflicts = SourceConflictDetector.detect_conflicts(sources)
    assert len(conflicts) == 0


def test_6_high_authority_vs_low_authority_source_resolved():
    """Requirement 6: High-authority source (.gov / sec.gov) beats low-authority blog -> resolved status."""
    sources = [
        {
            "title": "Official SEC Filing",
            "snippet": "Company X generated $10B revenue in 2025.",
            "url": "https://sec.gov/edgar/data/companyx/2025",
            "domain": "sec.gov",
        },
        {
            "title": "Tech Blog",
            "snippet": "Company X generated $12B revenue in 2025.",
            "url": "https://medium.com/tech-blog/companyx-revenue",
            "domain": "medium.com",
        },
    ]
    conflicts = SourceConflictDetector.detect_conflicts(sources)
    assert len(conflicts) == 1
    conflict = conflicts[0]
    assert conflict.status == ConflictStatus.RESOLVED
    assert conflict.preferred_source == "https://sec.gov/edgar/data/companyx/2025"
    assert "higher source authority" in conflict.resolution_reason.lower() or "sec.gov" in conflict.resolution_reason.lower()


def test_7_equally_credible_sources_unresolved_conflict():
    """Requirement 7: Two equally credible conflicting sources -> unresolved conflict."""
    sources = [
        {
            "title": "Blog A",
            "snippet": "Company X generated $10B revenue in 2025.",
            "url": "https://bloga.com/post1",
            "domain": "bloga.com",
        },
        {
            "title": "Blog B",
            "snippet": "Company X generated $12B revenue in 2025.",
            "url": "https://blogb.com/post2",
            "domain": "blogb.com",
        },
    ]
    conflicts = SourceConflictDetector.detect_conflicts(sources)
    assert len(conflicts) == 1
    conflict = conflicts[0]
    assert conflict.status == ConflictStatus.UNRESOLVED
    assert conflict.preferred_source is None
    assert "could not confidently determine" in conflict.resolution_reason


def test_8_multi_source_support_increases_confidence():
    """Requirement 8: Multiple sources supporting the same value boosts confidence score."""
    sources = [
        {"title": "Source 1", "snippet": "Company X generated $10B revenue in 2025.", "url": "https://src1.com"},
        {"title": "Source 2", "snippet": "Company X 2025 revenue reached 10 billion.", "url": "https://src2.com"},
        {"title": "Source 3", "snippet": "Company X generated $12B revenue in 2025.", "url": "https://src3.com"},
    ]
    conflicts = SourceConflictDetector.detect_conflicts(sources)
    assert len(conflicts) >= 1
    # Check that multi-source supported value ($10B) is preferred or confidence is boosted
    conflict = conflicts[0]
    assert conflict.confidence >= 0.75


def test_9_conflict_detector_failure_handled_gracefully():
    """Requirement 9: Conflict detector handles malformed inputs safely without throwing or crashing."""
    malformed_sources = [None, {"url": "invalid"}, "invalid string input"]
    # Should not raise exception
    conflicts = SourceConflictDetector.detect_conflicts(malformed_sources)
    assert isinstance(conflicts, list)


@pytest.mark.asyncio
async def test_10_final_report_contains_conflict_information():
    """Requirement 10: Final report synthesized by ReportAgent contains Source Conflicts markdown section."""
    query = "Analyze Company X 2025 performance"
    plan = PlanOutput(
        research_goal="Evaluate Company X",
        sub_queries=["Company X revenue 2025"],
        target_domains=["example.com"],
        steps=["Search", "Report"],
    )
    facts = [
        VerifiedFact(
            fact_statement="Company X financial report",
            is_verified=True,
            confidence_score=0.90,
            supporting_urls=["https://sec.gov/filing"],
        )
    ]
    citations = [
        CitationItem(
            citation_id="[1]",
            url="https://sec.gov/filing",
            title="SEC Filing",
            formatted_citation="SEC Filing (2025)",
            in_text_tag="[1](https://sec.gov/filing)",
        )
    ]
    conflicts = [
        SourceConflict(
            claim="Company X 2025 revenue",
            normalized_claim="company x 2025 revenue",
            source_a={
                "url": "https://sec.gov/filing",
                "title": "SEC Filing",
                "domain": "sec.gov",
                "authority_score": 5.0,
            },
            source_b={
                "url": "https://blog.com/post",
                "title": "Blog Post",
                "domain": "blog.com",
                "authority_score": 1.0,
            },
            source_a_evidence="$10B revenue in 2025",
            source_b_evidence="$12B revenue in 2025",
            conflicting_values={"source_a": "$10B", "source_b": "$12B"},
            severity=ConflictSeverity.MEDIUM,
            confidence=0.90,
            status=ConflictStatus.RESOLVED,
            preferred_source="https://sec.gov/filing",
            resolution_reason="SEC Filing preferred due to higher source authority.",
        )
    ]

    report_agent = MockReportAgent()
    output = await report_agent.synthesize_report(query, plan, facts, citations, conflicts=conflicts)

    assert "## Source Conflicts" in output.content_markdown
    assert "Conflict: Company X 2025 revenue" in output.content_markdown
    assert "Status" in output.content_markdown and "Resolved" in output.content_markdown
    assert "Preferred Source" in output.content_markdown
    assert len(output.conflicts) == 1


@pytest.mark.asyncio
async def test_agent_manager_pipeline_execution_with_conflicts():
    """Verify end-to-end AgentManager pipeline execution with conflict detection enqueued."""
    agent_manager = AgentManager()
    job_id = uuid4()
    user_id = uuid4()

    report = await agent_manager.run_pipeline(
        job_id=job_id,
        user_id=user_id,
        query="Company X revenue 2025",
        depth="standard",
    )
    assert report is not None
    assert report.title is not None
    assert report.content_markdown is not None
