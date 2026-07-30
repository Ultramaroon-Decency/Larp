"""ResearchJob repository — data access queries for the ``research_jobs`` table."""

from typing import Sequence
from uuid import UUID

from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.research_job import ResearchJob
from app.repositories.base import BaseRepository


class ResearchJobRepository(BaseRepository[ResearchJob]):
    """Data access repository for ResearchJob entities."""

    def __init__(self, session: AsyncSession) -> None:
        super().__init__(model=ResearchJob, session=session)

    async def get_by_user_id(
        self, user_id: UUID, skip: int = 0, limit: int = 100
    ) -> Sequence[ResearchJob]:
        """Fetch all research jobs belonging to a specific user (newest first)."""
        stmt = (
            select(ResearchJob)
            .where(ResearchJob.user_id == user_id)
            .order_by(ResearchJob.created_at.desc())
            .offset(skip)
            .limit(limit)
        )
        result = await self.session.execute(stmt)
        return result.scalars().all()

    async def search_user_history(
        self,
        user_id: UUID,
        skip: int = 0,
        limit: int = 20,
        status: str | None = None,
        depth: str | None = None,
        search: str | None = None,
        order_by: str | None = "-created_at",
    ) -> tuple[Sequence[ResearchJob], int]:
        """Search, filter, sort, and paginate a user's research history.

        Returns:
            Tuple of (list of ResearchJob items, total matching count).
        """
        stmt = select(ResearchJob).where(ResearchJob.user_id == user_id)
        count_stmt = select(func.count()).select_from(ResearchJob).where(ResearchJob.user_id == user_id)

        # Apply filtering by status
        if status:
            stmt = stmt.where(ResearchJob.status == status)
            count_stmt = count_stmt.where(ResearchJob.status == status)

        # Apply filtering by research depth
        if depth:
            stmt = stmt.where(ResearchJob.depth == depth)
            count_stmt = count_stmt.where(ResearchJob.depth == depth)

        # Apply keyword search across title and query
        if search and search.strip():
            keyword = f"%{search.strip()}%"
            search_clause = or_(
                ResearchJob.title.ilike(keyword),
                ResearchJob.query.ilike(keyword),
            )
            stmt = stmt.where(search_clause)
            count_stmt = count_stmt.where(search_clause)

        # Apply dynamic sorting
        if order_by:
            desc = order_by.startswith("-")
            col_name = order_by.lstrip("-")
            col = getattr(ResearchJob, col_name, None)
            if col is not None:
                stmt = stmt.order_by(col.desc() if desc else col.asc())
        else:
            stmt = stmt.order_by(ResearchJob.created_at.desc())

        # Apply pagination
        stmt = stmt.offset(skip).limit(limit)

        # Execute queries
        count_result = await self.session.execute(count_stmt)
        total_count = count_result.scalar_one() or 0

        jobs_result = await self.session.execute(stmt)
        jobs = jobs_result.scalars().all()

        return jobs, total_count

    async def get_job_with_details(self, job_id: UUID) -> ResearchJob | None:
        """Fetch job eagerly loading report, sources, and execution logs."""
        stmt = (
            select(ResearchJob)
            .options(
                selectinload(ResearchJob.report),
                selectinload(ResearchJob.sources),
                selectinload(ResearchJob.execution_logs),
            )
            .where(ResearchJob.id == job_id)
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_jobs_by_status(
        self, status: str, skip: int = 0, limit: int = 100
    ) -> Sequence[ResearchJob]:
        """Fetch jobs filtered by status (pending, in_progress, completed, failed)."""
        return await self.get_many_by(
            skip=skip, limit=limit, order_by="-created_at", status=status
        )

    async def count_by_user(self, user_id: UUID) -> int:
        """Count total research jobs created by a user."""
        return await self.count(user_id=user_id)
