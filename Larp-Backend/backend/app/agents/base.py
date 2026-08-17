"""Base LangGraph agent state and abstract interface definitions.

All concrete LangGraph agents inherit from ``BaseAgentInterface`` and operate
on the shared ``BaseAgentState`` dictionary passed between graph nodes.
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional, TypedDict
from uuid import UUID


class BaseAgentState(TypedDict, total=False):
    """Shared state dictionary passed across LangGraph nodes during research execution."""

    job_id: UUID
    user_id: UUID
    query: str
    depth: str
    plan: Optional[Dict[str, Any]]
    raw_sources: Optional[List[Dict[str, Any]]]
    verified_facts: Optional[List[Dict[str, Any]]]
    source_conflicts: Optional[List[Dict[str, Any]]]
    citations: Optional[List[Dict[str, Any]]]
    final_report: Optional[Dict[str, Any]]
    current_step: int
    current_agent: str
    status: str
    error: Optional[str]


class BaseAgentInterface(ABC):
    """Abstract Base Class interface for all LangGraph agents."""

    @property
    @abstractmethod
    def agent_name(self) -> str:
        """Return the unique name of the agent (e.g. 'PlannerAgent')."""
        pass

    @abstractmethod
    async def execute(self, state: BaseAgentState) -> BaseAgentState:
        """Execute the agent node logic on the state dictionary.

        Args:
            state: Current LangGraph state dictionary.

        Returns:
            Updated LangGraph state dictionary.
        """
        pass
