"""Legacy compatibility module for agent models.

Re-exports AgentExecutionLog as AgentTask / AgentResult for backwards compatibility.
"""

from app.models.agent_execution_log import AgentExecutionLog as AgentTask
from app.models.agent_execution_log import AgentExecutionLog as AgentResult

__all__ = ["AgentTask", "AgentResult"]
