"""AgentExecutionLog database model with progress metrics, cost calculation, and optimized indexes."""

import uuid
from typing import TYPE_CHECKING, Any, Dict, Optional

from sqlalchemy import Float, ForeignKey, Index, Integer, JSON, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin, UUIDPrimaryKeyMixin

if TYPE_CHECKING:
    from app.models.research_job import ResearchJob


class AgentExecutionLog(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """AgentExecutionLog entity tracking granular execution steps, agent metrics, inputs, outputs, cost, and errors."""

    __tablename__ = "agent_execution_logs"

    job_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("research_jobs.id", ondelete="CASCADE"), index=True, nullable=False
    )
    agent_name: Mapped[str] = mapped_column(
        String(100), index=True, nullable=False
    )  # e.g., "PlannerAgent", "SearchAgent", "FactCheckerAgent", "CitationAgent", "ReportAgent"
    step_number: Mapped[int] = mapped_column(Integer, nullable=False)
    
    # ── Required Execution Metrics ──────────────────────────────────────
    status: Mapped[str] = mapped_column(
        String(50), default="queued", index=True, nullable=False
    )  # queued, running, completed, failed
    execution_time_ms: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    cost_usd: Mapped[Optional[float]] = mapped_column(Float, default=0.0, nullable=True)
    error_message: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    input_data: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSON, nullable=True)
    output_data: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSON, nullable=True)

    # ── Database Indexes & Optimizations ────────────────────────────────
    __table_args__ = (
        Index("ix_agent_execution_logs_job_step", "job_id", "step_number"),
        Index("ix_agent_execution_logs_job_status", "job_id", "status"),
    )

    # Relationships
    job: Mapped["ResearchJob"] = relationship(
        "ResearchJob", back_populates="execution_logs"
    )
