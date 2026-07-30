"""ResearchHistory repository — data access queries for the ``research_history`` table."""

from typing import Sequence
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.research_history import ResearchHistory
from app.repositories.base import BaseRepository


class ResearchHistoryRepository(BaseRepository[ResearchHistory]):
    """Data access repository for ResearchHistory entities."""

    def __init__(self, session: AsyncSession) -> None:
        super().__init__(model=ResearchHistory, session=session)

    async def get_by_user_id(
        self, user_id: UUID, skip: int = 0, limit: int = 100
    ) -> Sequence[ResearchHistory]:
        """Fetch history entries for a specific user (newest first)."""
        stmt = (
            select(ResearchHistory)
            .where(ResearchHistory.user_id == user_id)
            .order_by(ResearchHistory.created_at.desc())
            .offset(skip)
            .limit(limit)
        )
        result = await self.session.execute(stmt)
        return result.scalars().all()

    async def get_by_job_id(self, job_id: UUID) -> Sequence[ResearchHistory]:
        """Fetch all history audit entries for a specific job."""
        return await self.get_many_by(order_by="-created_at", job_id=job_id)
