"""
Contradiction Detector
----------------------
Detects factual conflicts between research claims by performing
pairwise comparison of FactCheckItems in AggregatedResearchData.

Two types of contradictions are detected:
    1. Numerical Conflicts  — same topic, significantly different numbers
    2. Sentiment Conflicts  — same topic, opposing positive/negative assertions

Results are returned as a list of ContradictionReport objects,
each describing what conflicts, how severe they are, and from which sources.

Usage:
    from research_agent.app.utils.contradiction_detector import ContradictionDetector

    detector = ContradictionDetector()
    conflicts = detector.detect(aggregated_data)
    section_md = detector.format_markdown_section(conflicts)
"""

import re
import logging
from dataclasses import dataclass, field
from typing import List, Tuple, Optional
from research_agent.app.models.aggregator import AggregatedResearchData
from research_agent.app.models.tools import FactCheckItem

logger = logging.getLogger(__name__)

# Number pattern (e.g. 80%, $3.5 billion, 15x, 200 million)
_NUMBER_RE = re.compile(r"(\d+(?:\.\d+)?)\s*(%|x|\$|billion|million|thousand|k\b)?", re.IGNORECASE)

# Positive / negative sentiment word lists for sentiment conflict detection
_POSITIVE_WORDS = {
    "safe", "effective", "beneficial", "improved", "increase", "growth",
    "proven", "successful", "superior", "efficient", "accurate", "reliable",
    "better", "higher", "faster", "stronger", "advantage", "breakthrough"
}
_NEGATIVE_WORDS = {
    "unsafe", "dangerous", "harmful", "ineffective", "decrease", "decline",
    "failed", "inferior", "inaccurate", "unreliable", "worse", "lower",
    "slower", "weaker", "risk", "flawed", "controversial", "disputed"
}

# Minimum ratio between two numbers to classify as a conflict (e.g. 2x difference)
_NUMERIC_CONFLICT_RATIO = 2.0

# Minimum claim token overlap to consider two claims about the "same topic"
_TOPIC_OVERLAP_THRESHOLD = 0.25


@dataclass
class ContradictionReport:
    """
    Describes a detected contradiction between two research claims.

    Attributes:
        conflict_type:  'numerical' or 'sentiment'
        claim_a:        First conflicting claim text
        claim_b:        Second conflicting claim text
        severity:       'high', 'medium', or 'low'
        detail:         Human-readable explanation of the conflict
        topic_tokens:   Shared topic keywords between the two claims
    """
    conflict_type: str
    claim_a: str
    claim_b: str
    severity: str
    detail: str
    topic_tokens: List[str] = field(default_factory=list)


# Stop words for topic extraction
_STOP_WORDS = {
    "the", "a", "an", "and", "or", "but", "in", "on", "at", "to", "for",
    "of", "with", "by", "from", "is", "are", "was", "were", "be", "been",
    "that", "this", "it", "its", "which", "who", "than", "as", "if", "when"
}


class ContradictionDetector:
    """
    Pairwise contradiction detector for research claims.

    Scans all FactCheckItem pairs from AggregatedResearchData and flags:
    - Numerical conflicts: same subject, significantly divergent numbers
    - Sentiment conflicts: same subject, opposing positive/negative language

    Only claims that share sufficient topic keyword overlap are compared
    (controlled by _TOPIC_OVERLAP_THRESHOLD), avoiding false positives
    between completely unrelated claims.
    """

    def detect(self, aggregated: AggregatedResearchData) -> List[ContradictionReport]:
        """
        Detects all contradictions in aggregated research claims.

        Args:
            aggregated: AggregatedResearchData from ResultAggregatorAgent.

        Returns:
            List of ContradictionReport objects (may be empty if no conflicts found).
        """
        claims = aggregated.all_verified_claims
        if len(claims) < 2:
            return []

        logger.info(f"ContradictionDetector: Scanning {len(claims)} claims for conflicts...")
        conflicts: List[ContradictionReport] = []

        # Pairwise O(n²) comparison — acceptable for typical 3–15 claim counts
        for i in range(len(claims)):
            for j in range(i + 1, len(claims)):
                report = self._compare_claims(claims[i], claims[j])
                if report:
                    conflicts.append(report)

        logger.info(f"ContradictionDetector: Found {len(conflicts)} contradiction(s).")
        return conflicts

    def format_markdown_section(self, conflicts: List[ContradictionReport]) -> str:
        """
        Formats detected contradictions as a Markdown section for inclusion
        in the final research report.

        Returns:
            Markdown string, or empty string if no conflicts found.
        """
        if not conflicts:
            return ""

        lines = [
            "",
            "---",
            "",
            "## ⚠️ Conflicting Evidence Detected",
            "",
            f"> **{len(conflicts)} contradiction(s) found** in the research sources. "
            "Review carefully before citing.",
            "",
        ]

        for idx, c in enumerate(conflicts, 1):
            severity_emoji = {"high": "🔴", "medium": "🟡", "low": "🟢"}.get(c.severity, "⚪")
            lines += [
                f"### Conflict {idx}: {severity_emoji} {c.conflict_type.title()} Conflict ({c.severity.title()} Severity)",
                "",
                f"**Claim A:** {c.claim_a}",
                "",
                f"**Claim B:** {c.claim_b}",
                "",
                f"**Analysis:** {c.detail}",
                "",
            ]

        return "\n".join(lines)

    # ------------------------------------------------------------------
    # Internal comparison logic
    # ------------------------------------------------------------------

    def _compare_claims(
        self,
        claim_a: FactCheckItem,
        claim_b: FactCheckItem
    ) -> Optional[ContradictionReport]:
        """
        Compares two claims and returns a ContradictionReport if conflicting,
        or None if they are consistent or about different topics.
        """
        # Extract meaningful topic tokens from each claim
        tokens_a = self._extract_tokens(claim_a.claim)
        tokens_b = self._extract_tokens(claim_b.claim)

        # Compute topic overlap — skip comparison if claims are about different things
        if not tokens_a or not tokens_b:
            return None
        overlap = tokens_a & tokens_b
        overlap_ratio = len(overlap) / min(len(tokens_a), len(tokens_b))
        if overlap_ratio < _TOPIC_OVERLAP_THRESHOLD:
            return None

        shared_tokens = sorted(overlap)

        # Check for numerical conflict
        nums_a = self._extract_numbers(claim_a.claim)
        nums_b = self._extract_numbers(claim_b.claim)
        if nums_a and nums_b:
            conflict = self._check_numerical_conflict(
                claim_a.claim, claim_b.claim, nums_a, nums_b, shared_tokens
            )
            if conflict:
                return conflict

        # Check for sentiment conflict
        return self._check_sentiment_conflict(claim_a.claim, claim_b.claim, shared_tokens)

    def _check_numerical_conflict(
        self,
        text_a: str,
        text_b: str,
        nums_a: List[float],
        nums_b: List[float],
        shared_tokens: List[str]
    ) -> Optional[ContradictionReport]:
        """Flags significant numerical divergences between two claims."""
        # Compare the largest numbers found (usually the main statistic)
        max_a = max(nums_a)
        max_b = max(nums_b)

        if max_a == 0 or max_b == 0:
            return None

        ratio = max(max_a, max_b) / min(max_a, max_b)
        if ratio < _NUMERIC_CONFLICT_RATIO:
            return None

        severity = "high" if ratio >= 5.0 else ("medium" if ratio >= 3.0 else "low")

        return ContradictionReport(
            conflict_type="numerical",
            claim_a=text_a,
            claim_b=text_b,
            severity=severity,
            detail=(
                f"Claim A cites {max_a:g} while Claim B cites {max_b:g} "
                f"({ratio:.1f}x divergence). Verify which source is more authoritative."
            ),
            topic_tokens=shared_tokens
        )

    def _check_sentiment_conflict(
        self,
        text_a: str,
        text_b: str,
        shared_tokens: List[str]
    ) -> Optional[ContradictionReport]:
        """Flags opposing positive/negative sentiment on the same topic."""
        words_a = set(re.findall(r"\b\w+\b", text_a.lower()))
        words_b = set(re.findall(r"\b\w+\b", text_b.lower()))

        pos_a = bool(words_a & _POSITIVE_WORDS)
        neg_a = bool(words_a & _NEGATIVE_WORDS)
        pos_b = bool(words_b & _POSITIVE_WORDS)
        neg_b = bool(words_b & _NEGATIVE_WORDS)

        # Conflict = one is positive and the other is negative
        is_conflict = (pos_a and neg_b and not neg_a) or (neg_a and pos_b and not pos_a)
        if not is_conflict:
            return None

        found_pos = sorted((words_a | words_b) & _POSITIVE_WORDS)[:3]
        found_neg = sorted((words_a | words_b) & _NEGATIVE_WORDS)[:3]

        return ContradictionReport(
            conflict_type="sentiment",
            claim_a=text_a,
            claim_b=text_b,
            severity="medium",
            detail=(
                f"Opposing positions detected on shared topic [{', '.join(shared_tokens[:4])}]. "
                f"Positive indicators: {found_pos}. Negative indicators: {found_neg}."
            ),
            topic_tokens=shared_tokens
        )

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _extract_tokens(text: str) -> set:
        """Extracts lowercase non-stop-word tokens of length >= 4."""
        return {
            w.lower() for w in re.findall(r"\b[a-zA-Z]{4,}\b", text)
            if w.lower() not in _STOP_WORDS
        }

    @staticmethod
    def _extract_numbers(text: str) -> List[float]:
        """Extracts all numeric values found in text."""
        matches = _NUMBER_RE.findall(text)
        values: List[float] = []
        for num_str, _ in matches:
            try:
                values.append(float(num_str))
            except ValueError:
                pass
        return values
