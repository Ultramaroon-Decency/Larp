from abc import ABC
from typing import List, Optional
from research_agent.app.services.tools.base import BaseTool
from research_agent.app.models.tools import SearchResponse, SearchResultItem


class BaseSearchTool(BaseTool, ABC):
    """
    Abstract interface for Search Tools.
    """
    def __init__(self, name: str = "SearchTool", description: str = "Executes web or domain search queries."):
        super().__init__(name=name, description=description)


class MockSearchTool(BaseSearchTool):
    """
    Mock implementation of SearchTool for Phase 3 testing and offline development.
    """

    def __init__(self):
        super().__init__(
            name="MockSearchTool",
            description="Returns deterministic mock web search results based on input query."
        )

    async def _run(self, query: str, max_results: int = 5) -> SearchResponse:
        """
        Generates mock search results.
        """
        clean_query = query.strip()
        if not clean_query:
            raise ValueError("Search query cannot be empty.")

        mock_items: List[SearchResultItem] = [
            SearchResultItem(
                title=f"Overview of {clean_query}",
                snippet=f"Comprehensive background analysis and findings regarding {clean_query}.",
                url=f"https://example.org/research/{clean_query.lower().replace(' ', '-')}-overview",
                score=0.95
            ),
            SearchResultItem(
                title=f"Detailed Technical Report: {clean_query}",
                snippet=f"In-depth technical breakdown and empirical evaluations of {clean_query}.",
                url=f"https://techdocs.org/spec/{clean_query.lower().replace(' ', '-')}",
                score=0.88
            ),
            SearchResultItem(
                title=f"Recent Breakthroughs in {clean_query}",
                snippet=f"Latest updates, statistical metrics, and market impact related to {clean_query}.",
                url=f"https://sciencejournal.io/article/{clean_query.lower().replace(' ', '-')}",
                score=0.82
            )
        ]

        results = mock_items[:max_results]
        return SearchResponse(
            query=clean_query,
            results=results,
            total_results=len(results)
        )
