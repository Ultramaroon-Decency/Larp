"""
Evaluator Agent
---------------
A self-critiquing reflexion agent that scores a draft research report
against the original query on three axes:

    - Coverage   : Did we find enough diverse sources?
    - Depth      : Are claims substantiated with specific evidence?
    - Relevance  : Does the report answer the exact question asked?

If any axis scores below `threshold` (default 0.70), the EvaluatorAgent
flags specific gaps so the executor can run a targeted second pass.

Usage:
    from research_agent.app.agents.evaluator import EvaluatorAgent

    evaluator = EvaluatorAgent(threshold=0.70)
    verdict = evaluator.evaluate(query, aggregated_data, report)

    if not verdict.passed:
        print(verdict.gap_summary)   # Human-readable gap description
        print(verdict.missing_topics)  # Topics to research further
"""

import re
import logging
from dataclasses import dataclass, field
from typing import List, Optional
from research_agent.app.models.aggregator import AggregatedResearchData
from research_agent.app.models.report import ResearchReport

logger = logging.getLogger(__name__)

# Minimum word count for "substantiated" coverage
_MIN_SNIPPET_WORDS = 30

# Minimum distinct sources for "adequate" coverage
_MIN_SOURCES = 2

# Stop words excluded from keyword relevance matching
_STOP_WORDS = {
    "the", "a", "an", "and", "or", "but", "in", "on", "at", "to", "for",
    "of", "with", "by", "from", "is", "are", "was", "were", "be", "been",
    "being", "have", "has", "had", "do", "does", "did", "will", "would",
    "could", "should", "may", "might", "shall", "can", "not", "no", "nor",
    "so", "yet", "both", "either", "whether", "than", "then", "that",
    "this", "which", "who", "whom", "what", "how", "when", "where", "why",
}


@dataclass
class EvaluationVerdict:
    """
    Result of an EvaluatorAgent assessment run.

    Attributes:
        passed:         True if ALL three axes meet the threshold.
        coverage_score: [0.0–1.0] Source diversity and quantity score.
        depth_score:    [0.0–1.0] Evidence substantiation score.
        relevance_score:[0.0–1.0] Query-to-report alignment score.
        overall_score:  Weighted average of all three axes.
        gap_summary:    Human-readable description of what is lacking.
        missing_topics: Specific sub-topics the agent should research further.
    """
    passed: bool
    coverage_score: float
    depth_score: float
    relevance_score: float
    overall_score: float
    gap_summary: str
    missing_topics: List[str] = field(default_factory=list)


class EvaluatorAgent:
    """
    Self-critiquing Reflexion Agent.

    Evaluates aggregated research data and a generated report against
    the original research query. Produces a structured EvaluationVerdict
    that the LarpAgent pipeline can use to decide whether to run a
    second deeper research pass.

    Scoring axes:
        - Coverage (30%):  Distinct source URLs found vs minimum threshold
        - Depth    (40%):  Average snippet length and claim count
        - Relevance(30%):  Keyword overlap between query tokens and report content
    """

    def __init__(self, threshold: float = 0.70):
        """
        Args:
            threshold: Minimum acceptable score per axis (0.0–1.0). Default 0.70.
        """
        self.threshold = max(0.0, min(1.0, threshold))

    # ------------------------------------------------------------------
    # Public interface
    # ------------------------------------------------------------------

    def evaluate(
        self,
        query: str,
        aggregated: AggregatedResearchData,
        report: Optional[ResearchReport] = None
    ) -> EvaluationVerdict:
        """
        Evaluates research quality across three axes and returns a verdict.

        Args:
            query:      The original research query string.
            aggregated: AggregatedResearchData from the ResultAggregatorAgent.
            report:     Optional ResearchReport for relevance scoring against final content.

        Returns:
            EvaluationVerdict with scores and actionable gap details.
        """
        logger.info(f"EvaluatorAgent: Evaluating research quality for query '{query[:60]}'")

        coverage_score = self._score_coverage(aggregated)
        depth_score = self._score_depth(aggregated)
        relevance_score = self._score_relevance(query, aggregated, report)

        # Weighted average: depth matters most
        overall_score = round(
            0.30 * coverage_score +
            0.40 * depth_score +
            0.30 * relevance_score,
            4
        )

        passed = (
            coverage_score >= self.threshold and
            depth_score >= self.threshold and
            relevance_score >= self.threshold
        )

        gap_summary, missing_topics = self._build_gap_summary(
            query, coverage_score, depth_score, relevance_score, aggregated
        )

        verdict = EvaluationVerdict(
            passed=passed,
            coverage_score=round(coverage_score, 4),
            depth_score=round(depth_score, 4),
            relevance_score=round(relevance_score, 4),
            overall_score=overall_score,
            gap_summary=gap_summary,
            missing_topics=missing_topics
        )

        status = "✅ PASSED" if passed else "⚠️  NEEDS DEEPER RESEARCH"
        logger.info(
            f"EvaluatorAgent: {status} | "
            f"coverage={coverage_score:.2f} depth={depth_score:.2f} "
            f"relevance={relevance_score:.2f} overall={overall_score:.2f}"
        )
        return verdict

    # ------------------------------------------------------------------
    # Scoring axes
    # ------------------------------------------------------------------

    def _score_coverage(self, aggregated: AggregatedResearchData) -> float:
        """
        Scores source quantity and diversity.
        Full score (1.0) when >= 5 distinct sources found.
        """
        total_sources = aggregated.total_sources_count
        # Linear scale: 0 sources = 0.0, 5+ sources = 1.0
        return min(1.0, total_sources / max(1, _MIN_SOURCES * 2.5))

    def _score_depth(self, aggregated: AggregatedResearchData) -> float:
        """
        Scores evidence substantiation by measuring:
        - Average snippet word count across search results
        - Number of verified/substantiated claims
        """
        depth_components: List[float] = []

        # Component 1: Snippet depth
        if aggregated.all_search_results:
            word_counts = [
                len(item.snippet.split())
                for item in aggregated.all_search_results
                if item.snippet
            ]
            avg_words = sum(word_counts) / len(word_counts) if word_counts else 0
            snippet_score = min(1.0, avg_words / _MIN_SNIPPET_WORDS)
            depth_components.append(snippet_score)

        # Component 2: Claim substantiation
        if aggregated.all_verified_claims:
            verified_count = sum(
                1 for c in aggregated.all_verified_claims
                if c.status == "verified"
            )
            claim_score = min(1.0, verified_count / max(1, len(aggregated.all_verified_claims)))
            depth_components.append(claim_score)

        # Component 3: Takeaway richness
        if aggregated.synthesized_takeaways:
            takeaway_score = min(1.0, len(aggregated.synthesized_takeaways) / 3.0)
            depth_components.append(takeaway_score)

        if not depth_components:
            return 0.20  # Minimal data found

        return round(sum(depth_components) / len(depth_components), 4)

    def _score_relevance(
        self,
        query: str,
        aggregated: AggregatedResearchData,
        report: Optional[ResearchReport]
    ) -> float:
        """
        Scores how well the research output aligns with the original query
        by measuring keyword overlap between query tokens and report content.
        """
        # Extract meaningful query keywords (exclude stop words)
        query_tokens = {
            w.lower() for w in re.findall(r"\b[a-zA-Z]{3,}\b", query)
            if w.lower() not in _STOP_WORDS
        }

        if not query_tokens:
            return 0.80  # Can't measure without meaningful query tokens

        # Build corpus from all available text
        corpus_parts: List[str] = []
        for item in aggregated.all_search_results:
            corpus_parts.append(item.title)
            corpus_parts.append(item.snippet)
        for claim in aggregated.all_verified_claims:
            corpus_parts.append(claim.claim)
        corpus_parts.extend(aggregated.synthesized_takeaways)
        if report and report.markdown_content:
            corpus_parts.append(report.markdown_content[:2000])  # First 2000 chars

        if not corpus_parts:
            return 0.20

        corpus_text = " ".join(corpus_parts).lower()
        corpus_words = set(re.findall(r"\b[a-zA-Z]{3,}\b", corpus_text))

        matched = query_tokens & corpus_words
        relevance = len(matched) / len(query_tokens) if query_tokens else 0.0
        return round(min(1.0, relevance), 4)

    # ------------------------------------------------------------------
    # Gap analysis
    # ------------------------------------------------------------------

    def _build_gap_summary(
        self,
        query: str,
        coverage: float,
        depth: float,
        relevance: float,
        aggregated: AggregatedResearchData
    ) -> tuple[str, List[str]]:
        """Generates a human-readable gap summary and list of missing topics."""
        gaps: List[str] = []
        missing_topics: List[str] = []

        if coverage < self.threshold:
            gaps.append(
                f"Coverage is low ({coverage:.0%}): only {aggregated.total_sources_count} sources found "
                f"(minimum recommended: {int(_MIN_SOURCES * 2.5)})."
            )
            missing_topics.append(f"Expanded source search for: {query}")

        if depth < self.threshold:
            gaps.append(
                f"Depth is low ({depth:.0%}): search snippets lack substantiation or claims are unverified."
            )
            missing_topics.append(f"In-depth analysis and fact verification for: {query}")

        if relevance < self.threshold:
            gaps.append(
                f"Relevance is low ({relevance:.0%}): research output does not sufficiently address the query keywords."
            )
            # Extract the most important keywords that were missed
            query_tokens = [
                w for w in re.findall(r"\b[a-zA-Z]{4,}\b", query)
                if w.lower() not in _STOP_WORDS
            ]
            if query_tokens:
                missing_topics.append(f"Targeted search for key concepts: {', '.join(query_tokens[:4])}")

        if not gaps:
            summary = (
                f"Research quality is satisfactory. "
                f"Coverage: {coverage:.0%}, Depth: {depth:.0%}, Relevance: {relevance:.0%}."
            )
        else:
            summary = "Research gaps detected:\n" + "\n".join(f"  • {g}" for g in gaps)

        return summary, missing_topics
