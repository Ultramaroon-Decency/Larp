"""AgentExecutionLog repository — data access queries for the ``agent_execution_logs`` table."""

from typing import Sequence
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.agent_execution_log import AgentExecutionLog
from app.repositories.base import BaseRepository


class AgentExecutionLogRepository(BaseRepository[AgentExecutionLog]):
    """Data access repository for AgentExecutionLog entities."""

    def __init__(self, session: AsyncSession) -> None:
        super().__init__(model=AgentExecutionLog, session=session)

    async def get_by_job_id(self, job_id: UUID) -> Sequence[AgentExecutionLog]:
        """Fetch all execution logs for a job ordered by step_number ascending."""
        stmt = (
            select(AgentExecutionLog)
            .where(AgentExecutionLog.job_id == job_id)
            .order_by(AgentExecutionLog.step_number.asc())
        )
        result = await self.session.execute(stmt)
        return result.scalars().all()

    async def get_failed_logs_by_job(self, job_id: UUID) -> Sequence[AgentExecutionLog]:
        """Fetch failed agent step execution logs for a job."""
        return await self.get_many_by(job_id=job_id, status="failed")
