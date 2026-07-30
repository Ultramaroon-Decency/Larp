"""Agent repository — data access for agent tasks and results."""

from typing import Sequence
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.agent import AgentTask, AgentResult
from app.repositories.base import BaseRepository


class AgentRepository(BaseRepository[AgentTask]):
    """Repository for agent task operations.

    Inherits generic CRUD and adds queries for:
    - Tasks by research session.
    - Pending task queue (priority-ordered).
    - Eager-loading results.
    """

    def __init__(self, session: AsyncSession) -> None:
        super().__init__(model=AgentTask, session=session)

    async def get_by_session_id(
        self, session_id: UUID
    ) -> Sequence[AgentTask]:
        """Return all agent tasks for a given research session."""
        return await self.get_many_by(
            order_by="-created_at", session_id=session_id
        )

    async def get_pending_tasks(self, limit: int = 10) -> Sequence[AgentTask]:
        """Return pending tasks ordered by priority (highest first).

        Used by the task worker to pick up the next batch of work.
        """
        stmt = (
            select(AgentTask)
            .where(AgentTask.status == "queued")
            .order_by(AgentTask.priority.desc(), AgentTask.created_at.asc())
            .limit(limit)
        )
        result = await self.session.execute(stmt)
        return result.scalars().all()

    async def get_task_with_results(
        self, task_id: UUID
    ) -> AgentTask | None:
        """Load a task with its results eagerly loaded."""
        stmt = (
            select(AgentTask)
            .options(selectinload(AgentTask.results))
            .where(AgentTask.id == task_id)
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def update_status(
        self, task_id: UUID, status: str
    ) -> AgentTask:
        """Update the task status (queued → running → completed / failed)."""
        return await self.update(task_id, {"status": status})
