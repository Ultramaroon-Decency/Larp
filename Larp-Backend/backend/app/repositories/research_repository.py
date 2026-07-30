"""Research repository — data access for research sessions and steps."""

from typing import Sequence
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.research import ResearchSession, ResearchStep
from app.repositories.base import BaseRepository


class ResearchRepository(BaseRepository[ResearchSession]):
    """Repository for research session operations.

    Inherits generic CRUD and adds queries for:
    - Per-user session listing (history).
    - Eager-loading steps and agent tasks.
    - Status filtering.
    """

    def __init__(self, session: AsyncSession) -> None:
        super().__init__(model=ResearchSession, session=session)

    async def get_by_user_id(
        self,
        user_id: UUID,
        skip: int = 0,
        limit: int = 100,
    ) -> Sequence[ResearchSession]:
        """Return all research sessions for a specific user (newest first)."""
        stmt = (
            select(ResearchSession)
            .where(ResearchSession.user_id == user_id)
            .order_by(ResearchSession.created_at.desc())
            .offset(skip)
            .limit(limit)
        )
        result = await self.session.execute(stmt)
        return result.scalars().all()

    async def get_with_steps(self, session_id: UUID) -> ResearchSession | None:
        """Load a session with all its steps eagerly loaded.

        Uses ``selectinload`` to avoid N+1 queries when the caller
        accesses ``session.steps``.
        """
        stmt = (
            select(ResearchSession)
            .options(
                selectinload(ResearchSession.steps),
                selectinload(ResearchSession.agent_tasks),
            )
            .where(ResearchSession.id == session_id)
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_by_user_and_id(
        self, user_id: UUID, session_id: UUID
    ) -> ResearchSession | None:
        """Get a session only if it belongs to the given user.

        Used to enforce ownership before allowing read / delete.
        """
        return await self.get_one_by(id=session_id, user_id=user_id)

    async def get_by_status(
        self,
        status: str,
        skip: int = 0,
        limit: int = 100,
    ) -> Sequence[ResearchSession]:
        """Return sessions filtered by status (pending, in_progress, completed)."""
        return await self.get_many_by(
            skip=skip, limit=limit, order_by="-created_at", status=status
        )

    async def count_by_user(self, user_id: UUID) -> int:
        """Count total sessions for a user (for pagination metadata)."""
        return await self.count(user_id=user_id)

    async def update_status(
        self, session_id: UUID, status: str, result_summary: str | None = None
    ) -> ResearchSession:
        """Update the status (and optionally the result summary)."""
        data: dict = {"status": status}
        if result_summary is not None:
            data["result_summary"] = result_summary
        return await self.update(session_id, data)
