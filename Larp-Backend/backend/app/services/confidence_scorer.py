"""Confidence Scorer service evaluating overall research confidence and claim-level confidence based on evidence quality and consistency."""

from enum import Enum
from typing import Any, Dict, List, Optional, Tuple
from app.core.logging import get_logger
from app.schemas.confidence import ClaimConfidence, ConfidenceLevel, ConfidenceScore
from app.schemas.conflict import ConflictSeverity, ConflictStatus, SourceConflict
from app.services.conflict_detector import SourceConflictDetector

logger = get_logger("confidence_scorer")


class ConfidenceScorer:
    """Dedicated engine calculating evidence-backed deterministic confidence scores."""

    @classmethod
    def calculate_confidence(
        cls,
        raw_sources: Optional[List[Dict[str, Any]]] = None,
        verified_facts: Optional[List[Dict[str, Any]]] = None,
        source_conflicts: Optional[List[Dict[str, Any]]] = None,
        citations: Optional[List[Dict[str, Any]]] = None,
        job_id: Optional[str] = None,
    ) -> ConfidenceScore:
        """Calculate overall research confidence score (0-100) and claim-level confidence.
        
        Formula:
        Overall Score = (0.25 * Source Quality) + (0.25 * Evidence Coverage)
                      + (0.20 * Source Agreement) + (0.20 * Citation Coverage)
                      - Conflict Penalty
        """
        try:
            sources = raw_sources or []
            facts = verified_facts or []
            conflicts = source_conflicts or []
            cites = citations or []

            # ── 1. Calculate Source Quality Score (25% Weight) ─────────────
            source_quality_score = cls._calculate_source_quality(sources)

            # ── 2. Calculate Evidence Coverage Score (25% Weight) ──────────
            evidence_coverage_score = cls._calculate_evidence_coverage(facts, sources)

            # ── 3. Calculate Source Agreement Score (20% Weight) ───────────
            source_agreement_score = cls._calculate_source_agreement(conflicts)

            # ── 4. Calculate Citation Coverage Score (20% Weight) ──────────
            citation_coverage_score = cls._calculate_citation_coverage(facts, cites)

            # ── 5. Calculate Conflict Penalty ──────────────────────────────
            conflict_penalty = cls._calculate_conflict_penalty(conflicts)

            # ── 6. Overall Weighted Score Calculation ──────────────────────
            raw_weighted = (
                (0.25 * source_quality_score)
                + (0.25 * evidence_coverage_score)
                + (0.20 * source_agreement_score)
                + (0.20 * citation_coverage_score)
            )

            # Subtract conflict penalty directly
            final_overall = max(0.0, min(100.0, raw_weighted - conflict_penalty))
            overall_score = round(final_overall, 1)

            # Determine confidence level
            confidence_level = cls._determine_confidence_level(overall_score)

            # ── 7. Claim-Level Confidence Evaluations ──────────────────────
            claim_confidences = cls._calculate_claim_confidences(facts, sources, conflicts)

            # ── 8. Generate Deterministic Explanation ─────────────────────
            explanation = cls._generate_explanation(
                overall_score,
                confidence_level,
                source_quality_score,
                evidence_coverage_score,
                source_agreement_score,
                citation_coverage_score,
                conflict_penalty,
                len(sources),
                len(conflicts),
            )

            result = ConfidenceScore(
                overall_score=overall_score,
                source_quality_score=round(source_quality_score, 1),
                evidence_coverage_score=round(evidence_coverage_score, 1),
                source_agreement_score=round(source_agreement_score, 1),
                citation_coverage_score=round(citation_coverage_score, 1),
                conflict_penalty=round(conflict_penalty, 1),
                confidence_level=confidence_level,
                explanation=explanation,
                claim_confidences=claim_confidences,
            )

            logger.info(
                "confidence_calculated",
                job_id=job_id,
                overall_score=overall_score,
                confidence_level=confidence_level.value,
                conflict_penalty=round(conflict_penalty, 1),
            )

            return result

        except Exception as exc:
            logger.error(
                "confidence_calculation_failed",
                job_id=job_id,
                error=str(exc),
            )
            # Safe resilience fallback
            return ConfidenceScore(
                overall_score=50.0,
                source_quality_score=50.0,
                evidence_coverage_score=50.0,
                source_agreement_score=50.0,
                citation_coverage_score=50.0,
                conflict_penalty=0.0,
                confidence_level=ConfidenceLevel.LOW,
                explanation="Confidence calculation encountered an error and fell back to default baseline.",
                claim_confidences=[],
            )

    @classmethod
    def _calculate_source_quality(cls, sources: List[Dict[str, Any]]) -> float:
        """Calculate normalized source quality score (0.0 to 100.0) based on domain authority tiers."""
        if not sources:
            return 0.0

        authority_scores = []
        for src in sources:
            url = src.get("url", "")
            domain = src.get("domain") or (url.split("/")[2] if "/" in url and len(url.split("/")) > 2 else "web")
            auth = src.get("authority_score") or SourceConflictDetector.calculate_authority_score(url, domain)
            authority_scores.append(auth)

        avg_authority = sum(authority_scores) / len(authority_scores) if authority_scores else 1.0
        
        # Base quality: avg_authority / 5.0 * 100
        quality = (avg_authority / 5.0) * 100.0

        # Multi-source diversity bonus (+5% per independent authority source, max +10%)
        if len(sources) >= 3 and avg_authority >= 2.5:
            quality = min(100.0, quality + 10.0)
        elif len(sources) >= 2 and avg_authority >= 2.5:
            quality = min(100.0, quality + 5.0)

        return round(min(100.0, max(0.0, quality)), 1)

    @classmethod
    def _calculate_evidence_coverage(cls, facts: List[Dict[str, Any]], sources: List[Dict[str, Any]]) -> float:
        """Calculate percentage of claims/facts supported by retrieved evidence sources."""
        if not facts:
            return 80.0 if sources else 0.0

        supported_facts = 0
        for f in facts:
            urls = f.get("supporting_urls") or f.get("supporting_urls_count") or []
            if isinstance(urls, list) and len(urls) > 0:
                supported_facts += 1
            elif isinstance(urls, int) and urls > 0:
                supported_facts += 1
            elif f.get("is_verified", False):
                supported_facts += 1

        coverage = (supported_facts / len(facts)) * 100.0
        return round(min(100.0, max(0.0, coverage)), 1)

    @classmethod
    def _calculate_source_agreement(cls, conflicts: List[Dict[str, Any]]) -> float:
        """Calculate source consensus score based on conflict absence or frequency."""
        if not conflicts:
            return 100.0

        # Each conflict reduces agreement score
        agreement = max(0.0, 100.0 - (len(conflicts) * 20.0))
        return round(agreement, 1)

    @classmethod
    def _calculate_citation_coverage(cls, facts: List[Dict[str, Any]], citations: List[Dict[str, Any]]) -> float:
        """Calculate citation coverage ratio (percentage of facts properly cited)."""
        if not facts:
            return 100.0 if citations else 0.0

        if not citations:
            return 0.0

        # If citations exist, compare count against facts
        cited_ratio = min(1.0, len(citations) / len(facts))
        return round(cited_ratio * 100.0, 1)

    @classmethod
    def _calculate_conflict_penalty(cls, conflicts: List[Dict[str, Any]]) -> float:
        """Calculate penalty points deducted for detected source conflicts based on severity and status."""
        if not conflicts:
            return 0.0

        total_penalty = 0.0
        for conf in conflicts:
            severity = conf.get("severity", "MEDIUM")
            if isinstance(severity, Enum):
                severity = severity.value
            status = conf.get("status", "UNRESOLVED")
            if isinstance(status, Enum):
                status = status.value

            is_unresolved = (status == "UNRESOLVED")

            if severity == "LOW":
                total_penalty += 5.0 if is_unresolved else 3.0
            elif severity == "HIGH":
                total_penalty += 20.0 if is_unresolved else 12.0
            else:  # MEDIUM
                total_penalty += 10.0 if is_unresolved else 6.0

        return round(min(50.0, total_penalty), 1)

    @classmethod
    def _determine_confidence_level(cls, overall_score: float) -> ConfidenceLevel:
        """Determine human readable confidence level based on overall score."""
        if overall_score >= 90.0:
            return ConfidenceLevel.HIGH
        elif overall_score >= 75.0:
            return ConfidenceLevel.MEDIUM
        else:
            return ConfidenceLevel.LOW

    @classmethod
    def _calculate_claim_confidences(
        cls,
        facts: List[Dict[str, Any]],
        sources: List[Dict[str, Any]],
        conflicts: List[Dict[str, Any]],
    ) -> List[ClaimConfidence]:
        """Calculate confidence scores and explanations for individual claims/facts."""
        claim_list: List[ClaimConfidence] = []
        if not facts:
            return claim_list

        for fact in facts:
            statement = fact.get("fact_statement") or fact.get("statement") or "Factual finding"
            urls = fact.get("supporting_urls") or []
            if not isinstance(urls, list):
                urls = []

            # Check if this claim is involved in any conflict
            conflicting_urls = []
            is_conflicted = False
            for conf in conflicts:
                conf_claim = conf.get("claim", "").lower()
                norm_claim = conf.get("normalized_claim", "").lower()
                if conf_claim in statement.lower() or statement.lower() in conf_claim or norm_claim in statement.lower():
                    is_conflicted = True
                    src_b = conf.get("source_b", {})
                    b_url = src_b.get("url") if isinstance(src_b, dict) else str(src_b)
                    if b_url:
                        conflicting_urls.append(b_url)

            # Base claim score calculation
            if urls:
                auth_scores = [SourceConflictDetector.calculate_authority_score(u) for u in urls]
                avg_auth = sum(auth_scores) / len(auth_scores)
                base_score = (avg_auth / 5.0) * 100.0
            else:
                base_score = 50.0 if len(sources) > 0 else 30.0

            if is_conflicted:
                base_score -= 25.0

            claim_score = round(max(0.0, min(100.0, base_score)), 1)
            level = cls._determine_confidence_level(claim_score)

            if urls and not is_conflicted and claim_score >= 85.0:
                explanation = f"Supported by {len(urls)} authoritative source(s) with strong consensus."
            elif is_conflicted:
                explanation = f"Claim has contradictory evidence from {len(conflicting_urls)} conflicting source(s)."
            elif not urls:
                explanation = "Confidence is limited because the claim is supported by limited evidence from a low-authority source."
            else:
                explanation = f"Supported by {len(urls)} source(s)."

            claim_list.append(
                ClaimConfidence(
                    claim=statement,
                    score=claim_score,
                    confidence_level=level,
                    supporting_sources=urls,
                    conflicting_sources=conflicting_urls,
                    explanation=explanation,
                )
            )

        return claim_list

    @classmethod
    def _generate_explanation(
        cls,
        overall_score: float,
        confidence_level: ConfidenceLevel,
        source_quality: float,
        evidence_coverage: float,
        source_agreement: float,
        citation_coverage: float,
        conflict_penalty: float,
        num_sources: int,
        num_conflicts: int,
    ) -> str:
        """Generate a deterministic human-readable summary explanation derived from scoring inputs."""
        if num_sources <= 1 and overall_score < 75.0:
            return "Confidence is limited because the claim is supported by limited evidence from a low-authority source."

        parts = []

        if source_quality >= 85.0:
            parts.append("supported by multiple high-quality sources")
        elif source_quality >= 70.0:
            parts.append("supported by credible sources")
        else:
            parts.append("supported by lower-authority sources")

        if source_agreement >= 90.0 and num_conflicts == 0:
            parts.append("with strong source agreement")
        elif num_conflicts > 0:
            parts.append(f"with {num_conflicts} detected source conflict(s)")

        if citation_coverage >= 90.0:
            parts.append("and high citation coverage")

        summary = "The research is " + " ".join(parts) + "."

        if conflict_penalty > 0:
            summary += f" A conflict penalty of -{conflict_penalty:.0f} points reduced the overall score."

        return summary
