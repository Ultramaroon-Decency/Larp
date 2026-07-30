"""ResearchHistory database model with optimized indexes for audit history queries."""

import uuid
from typing import TYPE_CHECKING, Any, Dict, Optional

from sqlalchemy import ForeignKey, Index, JSON, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin, UUIDPrimaryKeyMixin

if TYPE_CHECKING:
    from app.models.research_job import ResearchJob
    from app.models.user import User


class ResearchHistory(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """ResearchHistory entity auditing user interactions, jobs created/completed, and report exports."""

    __tablename__ = "research_history"

    user_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), index=True, nullable=False
    )
    job_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        ForeignKey("research_jobs.id", ondelete="CASCADE"), index=True, nullable=True
    )
    action: Mapped[str] = mapped_column(
        String(100), index=True, nullable=False
    )  # e.g. "created", "started", "completed", "failed", "viewed", "exported"
    details: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSON, nullable=True)

    # ── Database Indexes & Optimizations ────────────────────────────────
    __table_args__ = (
        # Composite Index for chronological user audit timeline:
        # Accelerates SELECT * FROM research_history WHERE user_id = ? ORDER BY created_at DESC
        Index("ix_research_history_user_created", "user_id", "created_at"),
    )

    # Relationships
    user: Mapped["User"] = relationship("User", back_populates="history")
    job: Mapped[Optional["ResearchJob"]] = relationship(
        "ResearchJob", back_populates="history_entries"
    )
