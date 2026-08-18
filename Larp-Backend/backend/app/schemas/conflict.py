"""Pydantic schemas for Source Conflict Detection."""

from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, Optional
from uuid import uuid4

from pydantic import BaseModel, ConfigDict, Field


class ConflictSeverity(str, Enum):
    """Conflict severity classification."""

    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"


class ConflictStatus(str, Enum):
    """Conflict resolution status."""

    RESOLVED = "RESOLVED"
    UNRESOLVED = "UNRESOLVED"


class SourceRef(BaseModel):
    """Reference to a research source involved in a conflict."""

    model_config = ConfigDict(from_attributes=True)

    url: str = Field(description="Source URL")
    title: Optional[str] = Field(default=None, description="Source webpage title")
    domain: Optional[str] = Field(default=None, description="Source web domain")
    authority_score: float = Field(default=1.0, ge=0.0, le=5.0, description="Domain authority tier score")
    publication_date: Optional[str] = Field(default=None, description="Publication or record date if known")


class SourceConflict(BaseModel):
    """Internal and API representation of a source conflict."""

    model_config = ConfigDict(from_attributes=True)

    conflict_id: str = Field(default_factory=lambda: str(uuid4()), description="Unique identifier for the conflict")
    claim: str = Field(description="Original topic or claim description")
    normalized_claim: str = Field(description="Normalized canonical claim key for comparison")
    source_a: SourceRef = Field(description="First conflicting source")
    source_b: SourceRef = Field(description="Second conflicting source")
    source_a_evidence: str = Field(description="Evidence or snippet from source A")
    source_b_evidence: str = Field(description="Evidence or snippet from source B")
    conflicting_values: Dict[str, Any] = Field(description="Extracted conflicting statements/values (e.g., {'source_a': '$10B', 'source_b': '$12B'})")
    severity: ConflictSeverity = Field(default=ConflictSeverity.MEDIUM, description="Conflict severity level")
    confidence: float = Field(default=0.85, ge=0.0, le=1.0, description="Detection confidence score")
    status: ConflictStatus = Field(default=ConflictStatus.UNRESOLVED, description="Resolution status")
    preferred_source: Optional[str] = Field(default=None, description="URL or identifier of preferred source if resolved")
    resolution_reason: Optional[str] = Field(default=None, description="Explanation for resolution decision or lack thereof")
    detected_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc), description="Timestamp when conflict was detected")


# Alias for response schema
SourceConflictRead = SourceConflict
