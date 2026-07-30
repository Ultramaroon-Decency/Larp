"""Citation Agent interface definition for LangGraph."""

from abc import abstractmethod
from typing import List
from pydantic import BaseModel, Field

from app.agents.base import BaseAgentInterface, BaseAgentState
from app.agents.fact_checker import VerifiedFact


class CitationItem(BaseModel):
    """Formatted academic / web citation reference."""

    citation_id: str = Field(description="Unique citation reference key (e.g. '[1]')")
    url: str = Field(description="Source web URL")
    title: str = Field(description="Source title")
    formatted_citation: str = Field(description="Formatted APA/IEEE citation string")
    in_text_tag: str = Field(description="In-text Markdown reference tag (e.g. '[1](https://...)')")


class CitationAgentInterface(BaseAgentInterface):
    """Abstract interface for the Citation Agent responsible for formatting sources and references."""

    @property
    def agent_name(self) -> str:
        return "CitationAgent"

    @abstractmethod
    async def generate_citations(
        self, verified_facts: List[VerifiedFact]
    ) -> List[CitationItem]:
        """Generate structured citations from verified facts.

        Args:
            verified_facts: List of VerifiedFact claims.

        Returns:
            List of formatted CitationItem objects.
        """
        pass

    @abstractmethod
    async def execute(self, state: BaseAgentState) -> BaseAgentState:
        """Execute citation node within the LangGraph workflow."""
        pass
