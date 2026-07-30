"""ResearchReport database model supporting versioning and historical revision tracking."""

import uuid
from typing import TYPE_CHECKING, Any, Dict, List, Optional

from sqlalchemy import Boolean, ForeignKey, Index, Integer, JSON, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin, UUIDPrimaryKeyMixin

if TYPE_CHECKING:
    from app.models.research_job import ResearchJob
    from app.models.user import User


class ResearchReport(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """ResearchReport entity storing final outputs, Markdown body, and historical report versions."""

    __tablename__ = "research_reports"

    job_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("research_jobs.id", ondelete="CASCADE"),
        index=True,
        nullable=False,
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), index=True, nullable=False
    )
    title: Mapped[str] = mapped_column(String(500), nullable=False)
    summary: Mapped[str] = mapped_column(Text, nullable=False)
    content_markdown: Mapped[str] = mapped_column(Text, nullable=False)
    key_findings: Mapped[Optional[List[Dict[str, Any]]]] = mapped_column(
        JSON, nullable=True
    )
    word_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)

    # ── Report Versioning Fields ────────────────────────────────────────
    version: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    is_latest: Mapped[bool] = mapped_column(Boolean, default=True, index=True, nullable=False)
    parent_version_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        ForeignKey("research_reports.id", ondelete="SET NULL"), nullable=True
    )

    # ── Database Indexes & Optimizations ────────────────────────────────
    __table_args__ = (
        Index("ix_research_reports_job_version", "job_id", "version"),
        Index("ix_research_reports_job_latest", "job_id", "is_latest"),
    )

    # Relationships
    job: Mapped["ResearchJob"] = relationship("ResearchJob", back_populates="report")
    user: Mapped["User"] = relationship("User", back_populates="reports")
    parent_version: Mapped[Optional["ResearchReport"]] = relationship(
        "ResearchReport", remote_side="ResearchReport.id", uselist=False
    )
