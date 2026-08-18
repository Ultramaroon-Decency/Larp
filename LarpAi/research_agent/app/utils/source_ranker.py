"""
Source Authority Ranker
-----------------------
Scores web sources based on domain authority, TLD trust level,
publication recency, and whether a source provides citation depth.

Usage:
    from research_agent.app.utils.source_ranker import SourceAuthorityRanker
    score = SourceAuthorityRanker.score_url("https://nature.com/article/xyz")
"""

import re
import logging
from datetime import datetime, timezone
from typing import List, Optional
from urllib.parse import urlparse

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Domain-level trust tiers
# ---------------------------------------------------------------------------
_TLD_TRUST: dict[str, float] = {
    "edu": 0.95,
    "gov": 0.93,
    "ac.uk": 0.92,
    "org": 0.80,
    "net": 0.70,
    "com": 0.60,
    "io": 0.58,
    "co": 0.55,
}

# Known high-authority domain prefixes (partial match)
_HIGH_AUTHORITY_DOMAINS: dict[str, float] = {
    "nature.com": 0.98,
    "science.org": 0.97,
    "pubmed.ncbi.nlm.nih.gov": 0.97,
    "arxiv.org": 0.95,
    "scholar.google.com": 0.94,
    "ieee.org": 0.94,
    "acm.org": 0.93,
    "springer.com": 0.92,
    "sciencedirect.com": 0.91,
    "semanticscholar.org": 0.90,
    "wikipedia.org": 0.75,
    "medium.com": 0.55,
    "reddit.com": 0.40,
    "twitter.com": 0.30,
    "x.com": 0.30,
}

# Year pattern for extracting publication year from URLs / snippets
_YEAR_RE = re.compile(r"\b(20\d{2}|19\d{2})\b")


class SourceAuthorityRanker:
    """
    Stateless utility class providing domain authority scoring for research sources.

    Scoring formula (all values clamped to [0.0, 1.0]):
        final_score = domain_authority * recency_multiplier

    domain_authority: derived from known domain list → TLD tier → 0.50 fallback
    recency_multiplier: 1.0 for current year, decreasing by 0.04 per year of age
    """

    @staticmethod
    def score_url(url: str, year_hint: Optional[int] = None) -> float:
        """
        Returns an authority score [0.0–1.0] for a given URL.

        Args:
            url:        Full URL string of the source.
            year_hint:  Optional publication year to apply recency penalty.
                        If None, attempts to extract year from URL path.

        Returns:
            Float authority score between 0.0 and 1.0.
        """
        if not url or not url.strip():
            return 0.50

        try:
            parsed = urlparse(url.strip().lower())
            hostname = parsed.netloc.lstrip("www.")
        except Exception:
            return 0.50

        # 1. Check known high-authority domains first
        for domain, authority in _HIGH_AUTHORITY_DOMAINS.items():
            if domain in hostname:
                base_score = authority
                break
        else:
            # 2. Fall back to TLD scoring
            base_score = 0.50
            for tld, trust in _TLD_TRUST.items():
                if hostname.endswith(f".{tld}") or hostname == tld:
                    base_score = trust
                    break

        # 3. Apply recency multiplier
        pub_year = year_hint
        if pub_year is None:
            # Try to extract year from URL path
            match = _YEAR_RE.search(parsed.path)
            if match:
                pub_year = int(match.group(1))

        recency_mult = 1.0
        if pub_year:
            current_year = datetime.now(timezone.utc).year
            age_years = max(0, current_year - pub_year)
            # 4% penalty per year of age, minimum multiplier 0.60
            recency_mult = max(0.60, 1.0 - age_years * 0.04)

        final_score = round(min(1.0, base_score * recency_mult), 4)
        logger.debug(f"SourceAuthorityRanker: {hostname} → base={base_score}, recency={recency_mult}, final={final_score}")
        return final_score

    @staticmethod
    def rank_urls(urls: List[str]) -> List[tuple[str, float]]:
        """
        Scores and sorts a list of URLs by authority descending.

        Returns:
            List of (url, score) tuples sorted highest-first.
        """
        scored = [(url, SourceAuthorityRanker.score_url(url)) for url in urls if url]
        return sorted(scored, key=lambda x: x[1], reverse=True)

    @staticmethod
    def get_domain_label(url: str) -> str:
        """
        Returns a short human-readable label for a source's authority tier.

        Returns one of: 'High Authority', 'Moderate Authority', 'Low Authority'
        """
        score = SourceAuthorityRanker.score_url(url)
        if score >= 0.85:
            return "High Authority"
        elif score >= 0.65:
            return "Moderate Authority"
        else:
            return "Low Authority"
