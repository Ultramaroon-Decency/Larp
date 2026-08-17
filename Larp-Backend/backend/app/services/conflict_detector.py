"""Source Conflict Detection engine: normalization, authority scoring, conflict detection, resolution, and failure recovery."""

import re
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Tuple, Set
from uuid import uuid4

from app.core.logging import get_logger
from app.schemas.conflict import (
    ConflictSeverity,
    ConflictStatus,
    SourceConflict,
    SourceRef,
)

logger = get_logger("conflict_detector")


class ClaimNormalizer:
    """Utility class for normalizing claims, currency amounts, dates, and extracting canonical topic keys."""

    @staticmethod
    def normalize_text(text: str) -> str:
        """Clean whitespace, lower text, and simplify punctuation."""
        if not text:
            return ""
        # Lowercase
        normalized = text.lower().strip()
        # Collapse whitespace
        normalized = re.sub(r"\s+", " ", normalized)
        return normalized

    @staticmethod
    def parse_value_amount(text: str) -> Optional[float]:
        """Extract numeric amount considering currency markers (e.g. $10B -> 10,000,000,000, $12B -> 12,000,000,000)."""
        text_clean = text.replace(",", "")
        
        # Match pattern like $10B, $10.5 billion, 10 billion dollars, 10B USD
        billion_match = re.search(r"\$?\s*(\d+(?:\.\d+)?)\s*(?:b|billion)", text_clean, re.IGNORECASE)
        if billion_match:
            return float(billion_match.group(1)) * 1_000_000_000

        million_match = re.search(r"\$?\s*(\d+(?:\.\d+)?)\s*(?:m|million)", text_clean, re.IGNORECASE)
        if million_match:
            return float(million_match.group(1)) * 1_000_000

        percent_match = re.search(r"(\d+(?:\.\d+)?)\s*(?:%|percent)", text_clean, re.IGNORECASE)
        if percent_match:
            return float(percent_match.group(1))

        currency_match = re.search(r"(?:\$|\bUSD\b|\bEUR\b|\bGBP\b)\s*(\d+(?:\.\d+)?)", text_clean, re.IGNORECASE)
        if currency_match:
            return float(currency_match.group(1))

        # Generic numeric match - exclude standalone 4-digit years (1900-2099)
        num_match = re.search(r"\$?\s*(\d+(?:\.\d+)?)", text_clean)
        if num_match:
            val = float(num_match.group(1))
            if 1900 <= val <= 2099 and "$" not in text_clean:
                return None
            return val

        return None

    @staticmethod
    def extract_year(text: str) -> Optional[int]:
        """Extract a 4-digit year from text (e.g. 'launched in 2020' -> 2020)."""
        match = re.search(r"\b(19\d\d|20\d\d)\b", text)
        if match:
            return int(match.group(1))
        return None

    @classmethod
    def get_canonical_topic(cls, claim_statement: str) -> str:
        """Extract canonical topic key for claim grouping (e.g. 'company x revenue 2025')."""
        normalized = cls.normalize_text(claim_statement)
        
        # Strip specific numbers / amounts to get base topic
        topic = re.sub(r"\$?\s*\d+(?:\.\d+)?\s*(?:b|m|billion|million|trillion|dollars|usd|%)?", "", normalized, flags=re.IGNORECASE)
        topic = re.sub(r"\b(19\d\d|20\d\d)\b", "", topic)
        topic = re.sub(r"\s+", " ", topic).strip()
        return topic or normalized


class SourceConflictDetector:
    """Engine responsible for detecting source contradictions, assessing severity, and resolving conflicts."""

    # Authority domain tiers
    GOVERNMENT_DOMAINS = {"gov", "sec.gov", "edgar.sec.gov", "fda.gov", "census.gov", "who.int"}
    CORPORATE_OFFICIAL_KEYWORDS = {"investor", "filing", "official", "ir.", "sec-filing"}
    ACADEMIC_DOMAINS = {"arxiv.org", "doi.org", "nature.com", "ieee.org", "nih.gov", "edu", "springer.com", "sciencedirect.com"}
    MAJOR_NEWS_DOMAINS = {"reuters.com", "bloomberg.com", "wsj.com", "ft.com", "techcrunch.com", "nytimes.com", "bbc.com", "cnbc.com", "forbes.com"}
    SECONDARY_BLOG_DOMAINS = {"medium.com", "dev.to", "substack.com", "wordpress.com", "blogspot.com"}

    @classmethod
    def calculate_authority_score(cls, url: str, domain: Optional[str] = None) -> float:
        """Determine source authority tier score based on domain/url metadata."""
        if not url:
            return 1.0
        
        url_lower = url.lower()
        dom = (domain or "").lower()
        if not dom and "/" in url_lower:
            parts = url_lower.split("/")
            dom = parts[2] if len(parts) > 2 else url_lower

        # Tier 5: Government / Regulatory
        if any(g in dom for g in cls.GOVERNMENT_DOMAINS):
            return 5.0

        # Tier 4: Corporate Official Filing / Investor Relations
        if any(k in url_lower for k in cls.CORPORATE_OFFICIAL_KEYWORDS):
            return 4.0

        # Tier 3.5: Academic / Peer-reviewed
        if any(a in dom for a in cls.ACADEMIC_DOMAINS) or dom.endswith(".edu"):
            return 3.5

        # Tier 2.5: Major News
        if any(n in dom for n in cls.MAJOR_NEWS_DOMAINS):
            return 2.5

        # Tier 1.5: Secondary blog
        if any(b in dom for b in cls.SECONDARY_BLOG_DOMAINS):
            return 1.5

        # Tier 1.0: General web / blog
        return 1.0

    @classmethod
    def detect_conflicts(
        self,
        sources_or_claims: List[Dict[str, Any]],
        job_id: Optional[str] = None,
    ) -> List[SourceConflict]:
        """Detect source conflicts across extracted claims/sources."""
        try:
            conflicts: List[SourceConflict] = []
            if len(sources_or_claims) < 2:
                return conflicts

            items = []
            for item in sources_or_claims:
                if not isinstance(item, dict):
                    continue
                statement = item.get("statement") or item.get("fact_statement") or item.get("snippet") or item.get("title") or ""
                url = item.get("url") or item.get("supporting_url") or item.get("link") or "https://unknown-source.com"
                domain = item.get("domain") or (url.split("/")[2] if "/" in url and len(url.split("/")) > 2 else "web")
                title = item.get("title") or item.get("source_title") or domain
                authority = item.get("authority_score") or self.calculate_authority_score(url, domain)
                pub_date = item.get("publication_date") or item.get("date")

                items.append({
                    "statement": statement,
                    "url": url,
                    "title": title,
                    "domain": domain,
                    "authority": authority,
                    "pub_date": pub_date,
                    "amount": ClaimNormalizer.parse_value_amount(statement),
                    "year": ClaimNormalizer.extract_year(statement),
                    "canonical_topic": ClaimNormalizer.get_canonical_topic(statement),
                    "raw": item,
                })

            topic_groups: Dict[str, List[dict]] = {}
            for item in items:
                topic = item["canonical_topic"]
                if topic not in topic_groups:
                    topic_groups[topic] = []
                topic_groups[topic].append(item)

            seen_pairs: Set[Tuple[str, str]] = set()

            for topic, group in topic_groups.items():
                if len(group) < 2:
                    continue

                value_counts: Dict[Any, int] = {}
                for it in group:
                    val = it["amount"] or it["year"] or ClaimNormalizer.normalize_text(it["statement"])
                    value_counts[val] = value_counts.get(val, 0) + 1

                for i in range(len(group)):
                    for j in range(i + 1, len(group)):
                        item_a = group[i]
                        item_b = group[j]

                        if item_a["url"] == item_b["url"]:
                            continue

                        pair_key = tuple(sorted([item_a["url"], item_b["url"]]))
                        if pair_key in seen_pairs:
                            continue

                        is_conflict, conflicting_values, severity = self._evaluate_pair_conflict(item_a, item_b)

                        if is_conflict:
                            seen_pairs.add(pair_key)
                            
                            val_a = item_a["amount"] or item_a["year"]
                            val_b = item_b["amount"] or item_b["year"]
                            support_a = value_counts.get(val_a, 1)
                            support_b = value_counts.get(val_b, 1)

                            status, preferred_url, reason = self._resolve_conflict(
                                item_a, item_b, support_a, support_b
                            )

                            source_a_ref = SourceRef(
                                url=item_a["url"],
                                title=item_a["title"],
                                domain=item_a["domain"],
                                authority_score=item_a["authority"],
                                publication_date=item_a["pub_date"],
                            )
                            source_b_ref = SourceRef(
                                url=item_b["url"],
                                title=item_b["title"],
                                domain=item_b["domain"],
                                authority_score=item_b["authority"],
                                publication_date=item_b["pub_date"],
                            )

                            confidence = min(0.95, 0.70 + (0.05 * max(support_a, support_b)) + (0.05 * abs(item_a["authority"] - item_b["authority"])))

                            conflict = SourceConflict(
                                claim=topic or item_a["statement"],
                                normalized_claim=topic,
                                source_a=source_a_ref,
                                source_b=source_b_ref,
                                source_a_evidence=item_a["statement"],
                                source_b_evidence=item_b["statement"],
                                conflicting_values=conflicting_values,
                                severity=severity,
                                confidence=round(confidence, 2),
                                status=status,
                                preferred_source=preferred_url,
                                resolution_reason=reason,
                                detected_at=datetime.now(timezone.utc),
                            )
                            conflicts.append(conflict)

                            if status == ConflictStatus.RESOLVED:
                                logger.info(
                                    "conflict_resolved",
                                    job_id=job_id,
                                    conflict_id=conflict.conflict_id,
                                    topic=topic,
                                    preferred_source=preferred_url,
                                    severity=severity.value,
                                )
                            else:
                                logger.warning(
                                    "conflict_unresolved",
                                    job_id=job_id,
                                    conflict_id=conflict.conflict_id,
                                    topic=topic,
                                    severity=severity.value,
                                )

            return conflicts

        except Exception as exc:
            logger.error(
                "conflict_detection_failed",
                job_id=job_id,
                error=str(exc),
            )
            return []

    @classmethod
    def _evaluate_pair_conflict(
        cls, item_a: dict, item_b: dict
    ) -> Tuple[bool, Dict[str, Any], ConflictSeverity]:
        """Determine if two items in the same topic group conflict and assess severity."""
        amt_a, amt_b = item_a["amount"], item_b["amount"]
        yr_a, yr_b = item_a["year"], item_b["year"]

        # Case 1: Year / Date conflict (e.g. 2020 vs 2022)
        if yr_a is not None and yr_b is not None:
            if yr_a != yr_b:
                diff = abs(yr_a - yr_b)
                severity = ConflictSeverity.LOW if diff == 1 else ConflictSeverity.MEDIUM
                return True, {"source_a": str(yr_a), "source_b": str(yr_b)}, severity

        # Case 2: Numerical amount conflict (e.g. $10B vs $12B)
        if amt_a is not None and amt_b is not None:
            if amt_a != amt_b:
                rel_diff = abs(amt_a - amt_b) / max(amt_a, amt_b)
                if rel_diff < 0.01:
                    return False, {}, ConflictSeverity.LOW

                if rel_diff < 0.05:
                    severity = ConflictSeverity.LOW
                elif rel_diff < 0.30:
                    severity = ConflictSeverity.MEDIUM
                else:
                    severity = ConflictSeverity.HIGH

                val_a_str = f"${amt_a/1e9:.1f}B" if amt_a >= 1e9 else str(amt_a)
                val_b_str = f"${amt_b/1e9:.1f}B" if amt_b >= 1e9 else str(amt_b)

                return True, {"source_a": val_a_str, "source_b": val_b_str}, severity

        # Case 2: Year / Date conflict (e.g. 2020 vs 2022)
        if yr_a is not None and yr_b is not None:
            if yr_a != yr_b:
                diff = abs(yr_a - yr_b)
                severity = ConflictSeverity.LOW if diff == 1 else ConflictSeverity.MEDIUM
                return True, {"source_a": str(yr_a), "source_b": str(yr_b)}, severity

        # Case 3: Contradictory statements without clear numbers
        norm_a = ClaimNormalizer.normalize_text(item_a["statement"])
        norm_b = ClaimNormalizer.normalize_text(item_b["statement"])

        # Check for explicit negation pairs
        negation_terms = [("launched", "failed to launch"), ("approved", "rejected"), ("increased", "decreased"), ("yes", "no"), ("true", "false")]
        for pos, neg in negation_terms:
            if (pos in norm_a and neg in norm_b) or (neg in norm_a and pos in norm_b):
                return True, {"source_a": norm_a, "source_b": norm_b}, ConflictSeverity.HIGH

        # Default: No contradiction found
        return False, {}, ConflictSeverity.LOW

    @classmethod
    def _resolve_conflict(
        cls, item_a: dict, item_b: dict, support_a: int, support_b: int
    ) -> Tuple[ConflictStatus, Optional[str], Optional[str]]:
        """Determine whether conflict can be resolved using authority score, support count, and publication date."""
        eff_auth_a = item_a["authority"] + (0.5 * (support_a - 1))
        eff_auth_b = item_b["authority"] + (0.5 * (support_b - 1))

        auth_diff = abs(eff_auth_a - eff_auth_b)

        # Clear authority difference (e.g., Tier 5 SEC filing vs Tier 1.5 Blog)
        if auth_diff >= 1.0:
            preferred = item_a if eff_auth_a > eff_auth_b else item_b
            less_pref = item_b if eff_auth_a > eff_auth_b else item_a
            reason = f"{preferred['title']} ({preferred['url']}) preferred due to higher source authority ({preferred['authority']} vs {less_pref['authority']})."
            return ConflictStatus.RESOLVED, preferred["url"], reason

        # Significant support count difference (e.g., 3 sources vs 1 source)
        if abs(support_a - support_b) >= 2:
            preferred = item_a if support_a > support_b else item_b
            reason = f"{preferred['title']} preferred because it is supported by {max(support_a, support_b)} independent sources."
            return ConflictStatus.RESOLVED, preferred["url"], reason

        # Equally credible sources -> Unresolved
        reason = "Two credible sources report different values and Larp could not confidently determine which value is correct."
        return ConflictStatus.UNRESOLVED, None, reason
