"""ResearchSource repository — data access queries for the ``research_sources`` table."""

from typing import Sequence
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.research_source import ResearchSource
from app.repositories.base import BaseRepository


class ResearchSourceRepository(BaseRepository[ResearchSource]):
    """Data access repository for ResearchSource entities."""

    def __init__(self, session: AsyncSession) -> None:
        super().__init__(model=ResearchSource, session=session)

    async def get_by_job_id(self, job_id: UUID) -> Sequence[ResearchSource]:
        """Fetch all sources associated with a research job ordered by relevance score descending."""
        stmt = (
            select(ResearchSource)
            .where(ResearchSource.job_id == job_id)
            .order_by(ResearchSource.relevance_score.desc().nulls_last())
        )
        result = await self.session.execute(stmt)
        return result.scalars().all()

    async def get_by_domain(
        self, domain: str, skip: int = 0, limit: int = 100
    ) -> Sequence[ResearchSource]:
        """Fetch sources matching a specific domain."""
        return await self.get_many_by(skip=skip, limit=limit, domain=domain)
