"""ResearchJob database model with progress tracking and optimized indexes."""

import uuid
from datetime import datetime
from typing import TYPE_CHECKING, Any, Dict, List, Optional

from sqlalchemy import DateTime, Float, ForeignKey, Index, Integer, JSON, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin, UUIDPrimaryKeyMixin

if TYPE_CHECKING:
    from app.models.user import User
    from app.models.research_report import ResearchReport
    from app.models.research_source import ResearchSource
    from app.models.agent_execution_log import AgentExecutionLog
    from app.models.research_history import ResearchHistory


class ResearchJob(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """ResearchJob entity representing a multi-step research execution task."""

    __tablename__ = "research_jobs"

    user_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), index=True, nullable=False
    )
    title: Mapped[str] = mapped_column(String(500), nullable=False)
    query: Mapped[str] = mapped_column(Text, nullable=False)
    status: Mapped[str] = mapped_column(
        String(50), default="pending", index=True, nullable=False
    )  # pending, in_progress, completed, failed, cancelled
    depth: Mapped[str] = mapped_column(
        String(50), default="standard", nullable=False
    )  # quick, standard, deep
    
    # ── Progress Tracking Columns ───────────────────────────────────────
    current_agent: Mapped[Optional[str]] = mapped_column(
        String(100), nullable=True
    )  # e.g., "WebSearchAgent", "SummarizerAgent", "SynthesizerAgent"
    progress_percentage: Mapped[float] = mapped_column(
        Float, default=0.0, nullable=False
    )  # 0.0 to 100.0%
    execution_time_ms: Mapped[Optional[int]] = mapped_column(
        Integer, nullable=True
    )  # Total elapsed runtime in milliseconds

    config: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSON, nullable=True)
    error_message: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    cancelled_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)

    # ── Database Indexes & Optimizations ────────────────────────────────
    __table_args__ = (
        Index("ix_research_jobs_user_created", "user_id", "created_at"),
        Index("ix_research_jobs_user_status", "user_id", "status"),
        Index("ix_research_jobs_status_created", "status", "created_at"),
    )

    # Relationships
    user: Mapped["User"] = relationship("User", back_populates="jobs")
    report: Mapped[Optional["ResearchReport"]] = relationship(
        "ResearchReport", back_populates="job", uselist=False, cascade="all, delete-orphan"
    )
    sources: Mapped[List["ResearchSource"]] = relationship(
        "ResearchSource", back_populates="job", cascade="all, delete-orphan"
    )
    execution_logs: Mapped[List["AgentExecutionLog"]] = relationship(
        "AgentExecutionLog", back_populates="job", cascade="all, delete-orphan"
    )
    history_entries: Mapped[List["ResearchHistory"]] = relationship(
        "ResearchHistory", back_populates="job", cascade="all, delete-orphan"
    )
