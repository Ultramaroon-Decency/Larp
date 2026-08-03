"""Research Pydantic schemas for requests, responses, and status tracking."""

import uuid
from datetime import datetime
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, ConfigDict, Field


class ResearchJobCreate(BaseModel):
    """Payload for creating a new research job."""

    query: str = Field(min_length=3, description="Research prompt / topic query")
    title: Optional[str] = Field(default=None, max_length=500, description="Optional job title")
    depth: str = Field(default="standard", description="Research depth: 'quick', 'standard', 'deep'")
    config: Optional[Dict[str, Any]] = Field(default=None, description="Optional custom agent config")


class ResearchJobUpdate(BaseModel):
    """Payload for updating an existing research job."""

    title: Optional[str] = Field(default=None, max_length=500)
    status: Optional[str] = Field(default=None)
    current_agent: Optional[str] = Field(default=None)
    progress_percentage: Optional[float] = Field(default=None, ge=0.0, le=100.0)
    execution_time_ms: Optional[int] = Field(default=None, ge=0)
    config: Optional[Dict[str, Any]] = Field(default=None)


class UpdateProgressRequest(BaseModel):
    """Payload for updating job execution status and progress tracking metrics."""

    status: str = Field(description="New status: 'pending', 'in_progress', 'completed', 'failed', 'cancelled'")
    current_agent: Optional[str] = Field(default=None, description="Active agent name (e.g. 'WebSearchAgent')")
    progress_percentage: float = Field(default=0.0, ge=0.0, le=100.0, description="Completion percentage (0.0 to 100.0)")
    execution_time_ms: Optional[int] = Field(default=None, ge=0, description="Elapsed execution duration in milliseconds")
    error_message: Optional[str] = Field(default=None, description="Error message if status is 'failed'")


class SaveMetadataRequest(BaseModel):
    """Payload for updating research job configuration and metadata."""

    title: Optional[str] = Field(default=None)
    config: Optional[Dict[str, Any]] = Field(default=None)


class ResearchJobRead(BaseModel):
    """Summary representation of a ResearchJob."""

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    user_id: uuid.UUID
    title: str
    query: str
    status: str
    depth: str
    current_agent: Optional[str] = None
    progress_percentage: float = 0.0
    execution_time_ms: Optional[int] = None
    config: Optional[Dict[str, Any]] = None
    error_message: Optional[str] = None
    cancelled_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime


class ResearchCancelResponse(BaseModel):
    """Response payload for research job cancellation."""

    success: bool = True
    research_id: uuid.UUID
    status: str = "cancelled"
    message: str = "Research cancelled successfully."


class ResearchJobStatusResponse(BaseModel):
    """Lightweight response for progress tracking endpoints."""

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    status: str
    current_agent: Optional[str] = None
    progress_percentage: float = 0.0
    execution_time_ms: Optional[int] = None
    error_message: Optional[str] = None
    updated_at: datetime


class ResearchSourceRead(BaseModel):
    """Representation of a ResearchSource reference."""

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    job_id: uuid.UUID
    url: str
    title: Optional[str] = None
    domain: Optional[str] = None
    snippet: Optional[str] = None
    relevance_score: Optional[float] = None
    created_at: datetime


class ResearchReportRead(BaseModel):
    """Representation of a generated ResearchReport with versioning metadata."""

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    job_id: uuid.UUID
    user_id: uuid.UUID
    title: str
    summary: str
    content_markdown: str
    key_findings: Optional[List[Dict[str, Any]]] = None
    word_count: int
    version: int = 1
    is_latest: bool = True
    parent_version_id: Optional[uuid.UUID] = None
    created_at: datetime


class ResearchJobDetailsRead(ResearchJobRead):
    """Full representation of a ResearchJob including report and sources."""

    report: Optional[ResearchReportRead] = None
    sources: List[ResearchSourceRead] = Field(default_factory=list)


# Backwards compatibility aliases
ResearchSessionCreate = ResearchJobCreate
ResearchSessionRead = ResearchJobRead
ResearchSessionUpdate = ResearchJobUpdate
