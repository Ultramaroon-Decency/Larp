"""ResearchSource database model with optimized indexes for citation queries."""

import uuid
from typing import TYPE_CHECKING, Optional

from sqlalchemy import Float, ForeignKey, Index, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin, UUIDPrimaryKeyMixin

if TYPE_CHECKING:
    from app.models.research_job import ResearchJob


class ResearchSource(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """ResearchSource entity storing web references, articles, and citations used during research."""

    __tablename__ = "research_sources"

    job_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("research_jobs.id", ondelete="CASCADE"), index=True, nullable=False
    )
    url: Mapped[str] = mapped_column(String(2048), nullable=False)
    title: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    domain: Mapped[Optional[str]] = mapped_column(
        String(255), index=True, nullable=True
    )
    snippet: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    relevance_score: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    raw_content: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # ── Database Indexes & Optimizations ────────────────────────────────
    __table_args__ = (
        # Composite Index for fetching top sources ordered by relevance:
        # Accelerates SELECT * FROM research_sources WHERE job_id = ? ORDER BY relevance_score DESC
        Index("ix_research_sources_job_relevance", "job_id", "relevance_score"),
    )

    # Relationships
    job: Mapped["ResearchJob"] = relationship("ResearchJob", back_populates="sources")
