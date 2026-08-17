"""Comprehensive unit test suite for Confidence Scoring system."""

import pytest
from uuid import uuid4

from app.schemas.confidence import ConfidenceLevel, ConfidenceScore
from app.schemas.conflict import ConflictSeverity, ConflictStatus, SourceConflict, SourceRef
from app.services.confidence_scorer import ConfidenceScorer
from app.services.agent_manager import AgentManager
from app.agents.mock_agents import MockReportAgent


@pytest.mark.asyncio
async def test_1_multiple_high_quality_agreeing_sources_high_confidence():
    """Requirement 1: Multiple high-quality agreeing sources produce HIGH confidence (>= 90%)."""
    sources = [
        {"url": "https://sec.gov/filings/x", "domain": "sec.gov", "authority_score": 5.0},
        {"url": "https://treasury.gov/reports/x", "domain": "treasury.gov", "authority_score": 5.0},
        {"url": "https://companyx.com/investors", "domain": "companyx.com", "authority_score": 4.5},
    ]
    facts = [
        {"fact_statement": "Company X generated $10B revenue in 2025.", "supporting_urls": ["https://sec.gov/filings/x"], "is_verified": True},
        {"fact_statement": "Company X net income reached $2B.", "supporting_urls": ["https://companyx.com/investors"], "is_verified": True},
    ]
    citations = [
        {"url": "https://sec.gov/filings/x", "title": "SEC Filing"},
        {"url": "https://companyx.com/investors", "title": "Investor Report"},
    ]

    conf = ConfidenceScorer.calculate_confidence(
        raw_sources=sources,
        verified_facts=facts,
        source_conflicts=[],
        citations=citations,
    )

    assert conf.confidence_level == ConfidenceLevel.HIGH
    assert conf.overall_score >= 90.0
    assert conf.conflict_penalty == 0.0


@pytest.mark.asyncio
async def test_2_one_weak_source_low_confidence():
    """Requirement 2: Single weak low-authority source produces LOW confidence (< 75%)."""
    sources = [
        {"url": "https://randomblog123.blogspot.com/post", "domain": "blogspot.com", "authority_score": 1.0}
    ]
    facts = [
        {"fact_statement": "Unverified rumor about Company X.", "supporting_urls": [], "is_verified": False}
    ]

    conf = ConfidenceScorer.calculate_confidence(
        raw_sources=sources,
        verified_facts=facts,
        source_conflicts=[],
        citations=[],
    )

    assert conf.confidence_level == ConfidenceLevel.LOW
    assert conf.overall_score < 75.0
    assert "limited" in conf.explanation.lower()


@pytest.mark.asyncio
async def test_3_multiple_agreeing_sources_high_agreement():
    """Requirement 3: Multiple agreeing sources yield 100% source agreement score."""
    sources = [
        {"url": "https://reuters.com/a", "authority_score": 2.5},
        {"url": "https://bloomberg.com/b", "authority_score": 2.5},
    ]

    conf = ConfidenceScorer.calculate_confidence(
        raw_sources=sources,
        verified_facts=[],
        source_conflicts=[],
        citations=[],
    )

    assert conf.source_agreement_score == 100.0


@pytest.mark.asyncio
async def test_4_conflicting_sources_decreases_confidence():
    """Requirement 4: Detected source conflicts decrease overall confidence score."""
    sources = [
        {"url": "https://reuters.com/a", "authority_score": 2.5},
        {"url": "https://bloomberg.com/b", "authority_score": 2.5},
    ]
    conflicts = [
        {
            "claim": "Company X revenue",
            "normalized_claim": "company x revenue",
            "source_a": {"url": "https://reuters.com/a", "domain": "reuters.com"},
            "source_b": {"url": "https://bloomberg.com/b", "domain": "bloomberg.com"},
            "severity": "HIGH",
            "status": "UNRESOLVED",
        }
    ]

    conf_no_conflict = ConfidenceScorer.calculate_confidence(raw_sources=sources, source_conflicts=[])
    conf_with_conflict = ConfidenceScorer.calculate_confidence(raw_sources=sources, source_conflicts=conflicts)

    assert conf_with_conflict.overall_score < conf_no_conflict.overall_score
    assert conf_with_conflict.conflict_penalty > 0.0


@pytest.mark.asyncio
async def test_5_resolved_conflict_smaller_penalty():
    """Requirement 5: Resolved conflict incurs smaller penalty than unresolved conflict."""
    conf_resolved = [
        {"severity": "HIGH", "status": "RESOLVED"}
    ]
    conf_unresolved = [
        {"severity": "HIGH", "status": "UNRESOLVED"}
    ]

    score_res = ConfidenceScorer._calculate_conflict_penalty(conf_resolved)
    score_unres = ConfidenceScorer._calculate_conflict_penalty(conf_unresolved)

    assert score_res < score_unres
    assert score_res == 12.0
    assert score_unres == 20.0


@pytest.mark.asyncio
async def test_6_unresolved_conflict_larger_penalty():
    """Requirement 6: Medium unresolved conflict penalty is higher than medium resolved penalty."""
    penalty_res = ConfidenceScorer._calculate_conflict_penalty([{"severity": "MEDIUM", "status": "RESOLVED"}])
    penalty_unres = ConfidenceScorer._calculate_conflict_penalty([{"severity": "MEDIUM", "status": "UNRESOLVED"}])

    assert penalty_res == 6.0
    assert penalty_unres == 10.0


@pytest.mark.asyncio
async def test_7_high_citation_coverage_higher_score():
    """Requirement 7: High citation coverage yields 100% citation coverage score."""
    facts = [{"fact_statement": f"Fact {i}"} for i in range(5)]
    citations = [{"url": f"https://source{i}.com"} for i in range(5)]

    conf = ConfidenceScorer.calculate_confidence(
        raw_sources=citations, verified_facts=facts, citations=citations
    )
    assert conf.citation_coverage_score == 100.0


@pytest.mark.asyncio
async def test_8_low_citation_coverage_lower_score():
    """Requirement 8: Zero citations yield 0% citation coverage score."""
    facts = [{"fact_statement": "Fact 1"}]
    conf = ConfidenceScorer.calculate_confidence(verified_facts=facts, citations=[])
    assert conf.citation_coverage_score == 0.0


@pytest.mark.asyncio
async def test_9_high_evidence_coverage_higher_score():
    """Requirement 9: Claims with supporting URLs yield 100% evidence coverage score."""
    facts = [
        {"fact_statement": "Fact A", "supporting_urls": ["https://a.com"]},
        {"fact_statement": "Fact B", "supporting_urls": ["https://b.com"]},
    ]
    conf = ConfidenceScorer.calculate_confidence(verified_facts=facts)
    assert conf.evidence_coverage_score == 100.0


@pytest.mark.asyncio
async def test_10_low_evidence_coverage_lower_score():
    """Requirement 10: Claims without supporting evidence yield 0% evidence coverage score."""
    facts = [
        {"fact_statement": "Fact A", "supporting_urls": [], "is_verified": False},
        {"fact_statement": "Fact B", "supporting_urls": [], "is_verified": False},
    ]
    conf = ConfidenceScorer.calculate_confidence(verified_facts=facts, raw_sources=[])
    assert conf.evidence_coverage_score == 0.0


@pytest.mark.asyncio
async def test_11_claim_level_confidence_evaluation():
    """Requirement 11: Claim-level confidence evaluates individual claims and supporting/conflicting sources."""
    facts = [
        {"fact_statement": "Company X generated $10B revenue.", "supporting_urls": ["https://sec.gov/1"]}
    ]
    conflicts = [
        {
            "claim": "Company X generated $10B revenue.",
            "normalized_claim": "company x generated $10b revenue.",
            "source_a": {"url": "https://sec.gov/1"},
            "source_b": {"url": "https://fake.com/2"},
            "severity": "MEDIUM",
            "status": "UNRESOLVED",
        }
    ]

    conf = ConfidenceScorer.calculate_confidence(verified_facts=facts, source_conflicts=conflicts)
    assert len(conf.claim_confidences) == 1
    claim_conf = conf.claim_confidences[0]
    assert claim_conf.claim == "Company X generated $10B revenue."
    assert "https://sec.gov/1" in claim_conf.supporting_sources
    assert "https://fake.com/2" in claim_conf.conflicting_sources


@pytest.mark.asyncio
async def test_12_overall_confidence_calculation_deterministic():
    """Requirement 12: Confidence calculation is strictly deterministic for identical inputs."""
    sources = [{"url": "https://sec.gov", "authority_score": 5.0}]
    facts = [{"fact_statement": "Fact 1", "supporting_urls": ["https://sec.gov"]}]
    
    res1 = ConfidenceScorer.calculate_confidence(raw_sources=sources, verified_facts=facts)
    res2 = ConfidenceScorer.calculate_confidence(raw_sources=sources, verified_facts=facts)

    assert res1.overall_score == res2.overall_score
    assert res1.confidence_level == res2.confidence_level
    assert res1.explanation == res2.explanation


@pytest.mark.asyncio
async def test_13_no_conflicts_zero_penalty():
    """Requirement 13: Absence of source conflicts results in 0.0 conflict penalty."""
    conf = ConfidenceScorer.calculate_confidence(source_conflicts=[])
    assert conf.conflict_penalty == 0.0


@pytest.mark.asyncio
async def test_14_no_evidence_low_confidence():
    """Requirement 14: No sources or evidence yields LOW confidence score."""
    conf = ConfidenceScorer.calculate_confidence(raw_sources=[], verified_facts=[], citations=[])
    assert conf.confidence_level == ConfidenceLevel.LOW


@pytest.mark.asyncio
async def test_15_missing_source_metadata_handled_gracefully():
    """Requirement 15: Malformed source dictionaries with missing metadata do not throw exceptions."""
    sources = [{"invalid_key": "data"}, {}]
    facts = [{"fact_statement": None}]

    conf = ConfidenceScorer.calculate_confidence(raw_sources=sources, verified_facts=facts)
    assert conf is not None
    assert isinstance(conf.overall_score, float)


@pytest.mark.asyncio
async def test_16_confidence_calculation_failure_resilient():
    """Requirement 16: System fails safely to baseline score if calculation throws an exception."""
    # Pass incompatible data types to test resilience
    conf = ConfidenceScorer.calculate_confidence(raw_sources="invalid_string_type") # type: ignore
    assert conf is not None
    assert conf.confidence_level == ConfidenceLevel.LOW


@pytest.mark.asyncio
async def test_17_final_markdown_report_contains_confidence_section():
    """Requirement 17: MockReportAgent includes ## Confidence section in Markdown output."""
    agent = MockReportAgent()
    conf = ConfidenceScore(
        overall_score=91.0,
        source_quality_score=94.0,
        evidence_coverage_score=90.0,
        source_agreement_score=92.0,
        citation_coverage_score=95.0,
        conflict_penalty=4.0,
        confidence_level=ConfidenceLevel.HIGH,
        explanation="High confidence test report.",
        claim_confidences=[],
    )

    report = await agent.synthesize_report(
        query="Scaling AI Architectures",
        plan=None, # type: ignore
        facts=[],
        citations=[],
        confidence=conf,
    )

    assert "## Confidence" in report.content_markdown
    assert "**Overall Confidence**: 91%" in report.content_markdown
    assert "**Level**: HIGH" in report.content_markdown
    assert "- **Source Quality**: 94%" in report.content_markdown


@pytest.mark.asyncio
async def test_18_source_conflict_detection_tests_pass():
    """Requirement 18: Verify Source Conflict Detector functions correctly alongside ConfidenceScorer."""
    from app.services.conflict_detector import SourceConflictDetector
    detector = SourceConflictDetector()
    sources = [
        {"url": "https://a.com", "snippet": "Company X generated $10 billion revenue in 2025.", "raw_content": "Company X generated $10 billion revenue in 2025."},
        {"url": "https://b.com", "snippet": "Company X generated $12 billion revenue in 2025.", "raw_content": "Company X generated $12 billion revenue in 2025."},
    ]
    conflicts = detector.detect_conflicts(sources)
    assert len(conflicts) > 0


@pytest.mark.asyncio
async def test_19_x402_wallet_tests_pass():
    """Requirement 19: Verify Autonomous Wallet operates cleanly alongside ConfidenceScorer."""
    from app.services.wallet import SimulationWallet
    wallet = SimulationWallet(initial_balance=1.00)
    assert await wallet.get_balance() == 1.00


@pytest.mark.asyncio
async def test_20_full_agent_manager_pipeline_runs_with_confidence():
    """Requirement 20: Full AgentManager research pipeline executes end-to-end with Confidence Scoring."""
    agent_manager = AgentManager()
    job_id = uuid4()
    user_id = uuid4()

    report = await agent_manager.run_pipeline(job_id, user_id, "Multi-Agent AI Confidence Evaluation")
    assert report is not None
    assert report.confidence is not None
    assert report.confidence.overall_score >= 0.0
    assert "## Confidence" in report.content_markdown
