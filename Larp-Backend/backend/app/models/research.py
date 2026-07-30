"""Legacy compatibility module for research models.

Re-exports ResearchJob as ResearchSession for backwards compatibility.
"""

from app.models.research_job import ResearchJob as ResearchSession
from app.models.agent_execution_log import AgentExecutionLog as ResearchStep
from app.models.research_job import ResearchJob

__all__ = ["ResearchSession", "ResearchStep", "ResearchJob"]
