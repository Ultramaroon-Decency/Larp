"""Search Agent interface definition for LangGraph."""

from abc import abstractmethod
from typing import List, Optional
from pydantic import BaseModel, Field

from app.agents.base import BaseAgentInterface, BaseAgentState


class SearchResultItem(BaseModel):
    """Structured web search reference item."""

    url: str = Field(description="Web page URL")
    title: str = Field(description="Web page title")
    snippet: str = Field(description="Relevant text snippet")
    raw_content: Optional[str] = Field(default=None, description="Full scraped content if available")
    relevance_score: float = Field(default=0.0, ge=0.0, le=1.0, description="Relevance score (0.0 to 1.0)")


class SearchAgentInterface(BaseAgentInterface):
    """Abstract interface for the Search Agent responsible for fetching web intelligence."""

    @property
    def agent_name(self) -> str:
        return "SearchAgent"

    @abstractmethod
    async def execute_search(
        self, sub_queries: List[str], max_results_per_query: int = 5
    ) -> List[SearchResultItem]:
        """Execute web searches for a list of sub-queries.

        Args:
            sub_queries: List of decomposed sub-queries.
            max_results_per_query: Max search results per query.

        Returns:
            List of SearchResultItem objects.
        """
        pass

    @abstractmethod
    async def execute(self, state: BaseAgentState) -> BaseAgentState:
        """Execute search node within the LangGraph workflow."""
        pass
