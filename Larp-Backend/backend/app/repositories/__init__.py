"""Repository exports."""

from app.repositories.base import BaseRepository
from app.repositories.user_repository import UserRepository
from app.repositories.research_job_repository import ResearchJobRepository
from app.repositories.research_report_repository import ResearchReportRepository
from app.repositories.research_source_repository import ResearchSourceRepository
from app.repositories.research_history_repository import ResearchHistoryRepository
from app.repositories.payment_repository import PaymentRepository
from app.repositories.agent_execution_log_repository import AgentExecutionLogRepository

# Aliases for backwards compatibility
ResearchRepository = ResearchJobRepository
AgentRepository = AgentExecutionLogRepository

__all__ = [
    "BaseRepository",
    "UserRepository",
    "ResearchJobRepository",
    "ResearchReportRepository",
    "ResearchSourceRepository",
    "ResearchHistoryRepository",
    "PaymentRepository",
    "AgentExecutionLogRepository",
    "ResearchRepository",
    "AgentRepository",
]
