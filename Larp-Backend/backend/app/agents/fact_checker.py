"""Fact Checker Agent interface definition for LangGraph."""

from abc import abstractmethod
from typing import List, Optional
from pydantic import BaseModel, Field

from app.agents.base import BaseAgentInterface, BaseAgentState
from app.agents.search import SearchResultItem


class VerifiedFact(BaseModel):
    """Structured fact verification item."""

    fact_statement: str = Field(description="Extracted factual claim")
    is_verified: bool = Field(description="Verification status flag")
    confidence_score: float = Field(default=0.0, ge=0.0, le=1.0, description="Verification confidence")
    supporting_urls: List[str] = Field(default_factory=list, description="Supporting source URLs")
    contradictions: Optional[List[str]] = Field(default=None, description="Contradictory findings")


class FactCheckerAgentInterface(BaseAgentInterface):
    """Abstract interface for the Fact Checker Agent responsible for validating claims."""

    @property
    def agent_name(self) -> str:
        return "FactCheckerAgent"

    @abstractmethod
    async def verify_facts(
        self, raw_sources: List[SearchResultItem]
    ) -> List[VerifiedFact]:
        """Verify factual statements across retrieved search sources.

        Args:
            raw_sources: List of SearchResultItem retrieved by SearchAgent.

        Returns:
            List of VerifiedFact claims.
        """
        pass

    @abstractmethod
    async def execute(self, state: BaseAgentState) -> BaseAgentState:
        """Execute fact checker node within the LangGraph workflow."""
        pass
