"""ResearchReport repository — data access queries for the ``research_reports`` table supporting report versioning."""

from typing import Sequence
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.research_report import ResearchReport
from app.repositories.base import BaseRepository


class ResearchReportRepository(BaseRepository[ResearchReport]):
    """Data access repository for ResearchReport entities with historical versioning support."""

    def __init__(self, session: AsyncSession) -> None:
        super().__init__(model=ResearchReport, session=session)

    async def get_by_job_id(self, job_id: UUID) -> ResearchReport | None:
        """Fetch current latest active report version by job ID."""
        stmt = (
            select(ResearchReport)
            .where(ResearchReport.job_id == job_id, ResearchReport.is_latest == True)
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_versions_by_job_id(self, job_id: UUID) -> Sequence[ResearchReport]:
        """Fetch all historical report revisions for a job ordered by version descending."""
        stmt = (
            select(ResearchReport)
            .where(ResearchReport.job_id == job_id)
            .order_by(ResearchReport.version.desc())
        )
        result = await self.session.execute(stmt)
        return result.scalars().all()

    async def create_report_version(
        self,
        job_id: UUID,
        user_id: UUID,
        title: str,
        summary: str,
        content_markdown: str,
        key_findings: list[dict] | None = None,
        word_count: int = 0,
    ) -> ResearchReport:
        """Create a new report revision for a job. Marks previous version as non-latest."""
        current_latest = await self.get_by_job_id(job_id)

        next_version = 1
        parent_id = None

        if current_latest:
            # Demote current latest version
            await self.update(current_latest.id, {"is_latest": False})
            next_version = current_latest.version + 1
            parent_id = current_latest.id

        new_report_data = {
            "job_id": job_id,
            "user_id": user_id,
            "title": title,
            "summary": summary,
            "content_markdown": content_markdown,
            "key_findings": key_findings or [],
            "word_count": word_count,
            "version": next_version,
            "is_latest": True,
            "parent_version_id": parent_id,
        }

        return await self.create(new_report_data)

    async def get_by_user_id(
        self, user_id: UUID, skip: int = 0, limit: int = 100
    ) -> Sequence[ResearchReport]:
        """Fetch all latest reports belonging to a specific user (newest first)."""
        stmt = (
            select(ResearchReport)
            .where(ResearchReport.user_id == user_id, ResearchReport.is_latest == True)
            .order_by(ResearchReport.created_at.desc())
            .offset(skip)
            .limit(limit)
        )
        result = await self.session.execute(stmt)
        return result.scalars().all()

    async def get_report_with_job(self, report_id: UUID) -> ResearchReport | None:
        """Fetch report eagerly loading associated research job."""
        stmt = (
            select(ResearchReport)
            .options(selectinload(ResearchReport.job))
            .where(ResearchReport.id == report_id)
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()
