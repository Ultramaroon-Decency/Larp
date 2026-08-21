"""
ArXiv Academic Search Tool
--------------------------
Searches the ArXiv open-access preprint repository for scientific papers
using the ArXiv Atom XML API (completely free, no API key required).

Integrates with the BaseTool interface and returns results in the
standard SearchResponse / SearchResultItem schema.

Usage:
    tool = ArxivSearchTool()
    result = await tool.execute(query="transformer attention mechanisms", max_results=5)
"""

import logging
import httpx
import xml.etree.ElementTree as ET
from typing import Any, List
from research_agent.app.services.tools.base import BaseTool
from research_agent.app.models.tools import SearchResponse, SearchResultItem

logger = logging.getLogger(__name__)

# ArXiv Atom API namespace
_NS = {"atom": "http://www.w3.org/2005/Atom", "arxiv": "http://arxiv.org/schemas/atom"}

# ArXiv API base URL
_ARXIV_API_URL = "https://export.arxiv.org/api/query"


class ArxivSearchTool(BaseTool):
    """
    Academic search tool that queries the ArXiv preprint repository.

    - No API key required (fully offline-safe in air-gapped mode when using MockSearchTool)
    - Returns structured SearchResultItem entries with paper titles, abstracts, and PDF links
    - Scored at 0.95 authority by SourceAuthorityRanker (arxiv.org domain)
    """

    def __init__(self, timeout_seconds: float = 10.0):
        super().__init__(
            name="ArxivSearchTool",
            description="Searches ArXiv preprint repository for peer-reviewed scientific papers. No API key required."
        )
        self.timeout_seconds = timeout_seconds

    async def _run(self, query: str = "", max_results: int = 5, **kwargs) -> Any:
        """
        Executes an ArXiv search and returns a SearchResponse.

        Args:
            query:       Search query string (e.g. "quantum computing error correction")
            max_results: Maximum number of paper results to return (default 5, max 20)

        Returns:
            SearchResponse with academic paper results.
        """
        if not query or not query.strip():
            raise ValueError("ArXiv search query cannot be empty.")

        clean_query = query.strip()
        max_results = min(max(1, max_results), 20)  # Clamp between 1 and 20

        logger.info(f"ArxivSearchTool querying: '{clean_query[:60]}' (max_results={max_results})")

        try:
            params = {
                "search_query": f"all:{clean_query}",
                "start": 0,
                "max_results": max_results,
                "sortBy": "relevance",
                "sortOrder": "descending",
            }

            async with httpx.AsyncClient(timeout=self.timeout_seconds) as client:
                response = await client.get(_ARXIV_API_URL, params=params)
                response.raise_for_status()
                return self._parse_arxiv_response(clean_query, response.text)

        except httpx.TimeoutException:
            logger.warning("ArxivSearchTool: Request timed out. Returning fallback results.")
            return self._fallback_response(clean_query)
        except httpx.HTTPStatusError as e:
            logger.error(f"ArxivSearchTool: HTTP error {e.response.status_code}")
            return self._fallback_response(clean_query)
        except Exception as e:
            logger.error(f"ArxivSearchTool: Unexpected error: {e}")
            return self._fallback_response(clean_query)

    def _parse_arxiv_response(self, query: str, xml_text: str) -> SearchResponse:
        """Parses ArXiv Atom XML and extracts paper entries."""
        try:
            root = ET.fromstring(xml_text)
        except ET.ParseError as e:
            logger.error(f"ArxivSearchTool: XML parse error: {e}")
            return self._fallback_response(query)

        items: List[SearchResultItem] = []

        for entry in root.findall("atom:entry", _NS):
            # Extract title (strip extra whitespace from multi-line titles)
            title_el = entry.find("atom:title", _NS)
            title = " ".join((title_el.text or "Untitled").split()) if title_el is not None else "Untitled"

            # Extract abstract/summary (truncate to 300 chars for display)
            summary_el = entry.find("atom:summary", _NS)
            abstract = " ".join((summary_el.text or "").split()) if summary_el is not None else ""
            snippet = abstract[:300] + "..." if len(abstract) > 300 else abstract

            # Prefer the PDF link, fall back to the abstract page link
            pdf_url = ""
            abstract_url = ""
            for link_el in entry.findall("atom:link", _NS):
                rel = link_el.get("rel", "")
                href = link_el.get("href", "")
                link_type = link_el.get("type", "")
                if link_type == "application/pdf":
                    pdf_url = href
                elif rel == "alternate":
                    abstract_url = href

            url = pdf_url or abstract_url or "https://arxiv.org"

            # Extract publication year from 'published' tag for recency scoring
            published_el = entry.find("atom:published", _NS)
            score = 0.92  # Default high authority for ArXiv
            if published_el is not None and published_el.text:
                try:
                    pub_year = int(published_el.text[:4])
                    from research_agent.app.utils.source_ranker import SourceAuthorityRanker
                    score = SourceAuthorityRanker.score_url(url, year_hint=pub_year)
                except (ValueError, ImportError):
                    pass

            items.append(SearchResultItem(
                title=title,
                snippet=snippet,
                url=url,
                score=score
            ))

        logger.info(f"ArxivSearchTool: Parsed {len(items)} results for query '{query[:40]}'")
        return SearchResponse(query=query, results=items, total_results=len(items))

    def _fallback_response(self, query: str) -> SearchResponse:
        """Returns deterministic offline fallback when ArXiv is unreachable."""
        items = [
            SearchResultItem(
                title=f"[ArXiv Offline] Research Overview: {query.title()}",
                snippet=f"Academic preprint coverage for '{query}' is available on arxiv.org. Network unavailable during this session.",
                url=f"https://arxiv.org/search/?query={query.replace(' ', '+')}&searchtype=all",
                score=0.70
            )
        ]
        return SearchResponse(query=query, results=items, total_results=len(items))
