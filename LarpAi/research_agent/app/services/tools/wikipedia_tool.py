"""
Wikipedia Context Fetcher Tool
------------------------------
Fetches structured background context from Wikipedia's REST API.
Returns a clean summary paragraph + the canonical article URL.
Fully free, no API key required.

Integrates with BaseTool and returns SearchResponse schema so
the executor can treat it identically to any other search result.

Usage:
    tool = WikipediaTool()
    result = await tool.execute(query="Large language model", max_sentences=5)
"""

import logging
import httpx
from typing import Any, List
from research_agent.app.services.tools.base import BaseTool
from research_agent.app.models.tools import SearchResponse, SearchResultItem

logger = logging.getLogger(__name__)

_WIKIPEDIA_API = "https://en.wikipedia.org/api/rest_v1/page/summary/{title}"
_WIKIPEDIA_SEARCH = "https://en.wikipedia.org/w/api.php"


class WikipediaTool(BaseTool):
    """
    Wikipedia background context fetcher.

    Workflow:
        1. Search Wikipedia for the best matching article title
        2. Fetch the article's lead summary via the REST summary endpoint
        3. Return as a SearchResultItem with the article's canonical URL

    Features:
        - No API key or account required
        - Graceful offline fallback with informative placeholder
        - Configurable sentence-level truncation
    """

    def __init__(self, timeout_seconds: float = 8.0):
        super().__init__(
            name="WikipediaTool",
            description="Fetches structured background context and definitions from Wikipedia. No API key required."
        )
        self.timeout_seconds = timeout_seconds

    async def _run(self, query: str = "", max_sentences: int = 5, **kwargs) -> Any:
        """
        Fetches Wikipedia summary for the given query.

        Args:
            query:         Topic or concept to look up (e.g. "transformer neural network")
            max_sentences: Maximum number of summary sentences to include in snippet

        Returns:
            SearchResponse containing the Wikipedia summary as a SearchResultItem.
        """
        if not query or not query.strip():
            raise ValueError("Wikipedia query cannot be empty.")

        clean_query = query.strip()
        logger.info(f"WikipediaTool: Looking up '{clean_query[:60]}'")

        try:
            async with httpx.AsyncClient(timeout=self.timeout_seconds) as client:
                # Step 1: Search for the best article title
                best_title = await self._search_title(client, clean_query)
                if not best_title:
                    return self._fallback_response(clean_query)

                # Step 2: Fetch the article summary
                return await self._fetch_summary(client, clean_query, best_title, max_sentences)

        except httpx.TimeoutException:
            logger.warning("WikipediaTool: Request timed out.")
            return self._fallback_response(clean_query)
        except Exception as e:
            logger.error(f"WikipediaTool: Unexpected error: {e}")
            return self._fallback_response(clean_query)

    async def _search_title(self, client: httpx.AsyncClient, query: str) -> str:
        """Uses the MediaWiki API to find the most relevant article title."""
        try:
            params = {
                "action": "query",
                "list": "search",
                "srsearch": query,
                "srlimit": 1,
                "format": "json",
                "utf8": 1,
            }
            resp = await client.get(_WIKIPEDIA_SEARCH, params=params)
            resp.raise_for_status()
            data = resp.json()
            results = data.get("query", {}).get("search", [])
            if results:
                return results[0].get("title", "")
        except Exception as e:
            logger.warning(f"WikipediaTool: Title search failed: {e}")
        return ""

    async def _fetch_summary(
        self,
        client: httpx.AsyncClient,
        original_query: str,
        title: str,
        max_sentences: int
    ) -> SearchResponse:
        """Fetches the lead summary paragraph for a known Wikipedia article title."""
        try:
            # URL-encode the title for the REST API
            encoded_title = title.replace(" ", "_")
            url = _WIKIPEDIA_API.format(title=encoded_title)

            resp = await client.get(url, headers={"Accept": "application/json"})
            resp.raise_for_status()
            data = resp.json()

            extract = data.get("extract", "")
            page_url = data.get("content_urls", {}).get("desktop", {}).get("page", f"https://en.wikipedia.org/wiki/{encoded_title}")
            article_title = data.get("title", title)

            # Truncate to max_sentences
            sentences = extract.split(". ")
            snippet = ". ".join(sentences[:max_sentences])
            if len(sentences) > max_sentences:
                snippet += "."

            from research_agent.app.utils.source_ranker import SourceAuthorityRanker
            score = SourceAuthorityRanker.score_url(page_url)

            items: List[SearchResultItem] = [
                SearchResultItem(
                    title=f"Wikipedia: {article_title}",
                    snippet=snippet or f"Wikipedia article on {title}.",
                    url=page_url,
                    score=score
                )
            ]

            logger.info(f"WikipediaTool: Retrieved summary for '{article_title}'")
            return SearchResponse(query=original_query, results=items, total_results=len(items))

        except Exception as e:
            logger.error(f"WikipediaTool: Summary fetch failed for '{title}': {e}")
            return self._fallback_response(original_query)

    def _fallback_response(self, query: str) -> SearchResponse:
        """Returns an informative offline fallback when Wikipedia is unreachable."""
        items = [
            SearchResultItem(
                title=f"[Wikipedia Offline] Background: {query.title()}",
                snippet=f"Wikipedia background context for '{query}' is available at en.wikipedia.org. Network unavailable during this session.",
                url=f"https://en.wikipedia.org/w/index.php?search={query.replace(' ', '+')}",
                score=0.65
            )
        ]
        return SearchResponse(query=query, results=items, total_results=len(items))
