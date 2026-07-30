"""Shared schemas used across all endpoints.

Defines the standardised response envelope that **every** API response
follows — both success and error.  This ensures clients can always
rely on the same top-level structure.
"""

from datetime import datetime
from typing import Any, Generic, TypeVar

from pydantic import BaseModel, Field

T = TypeVar("T")


# ---------------------------------------------------------------------------
# Standard Response Envelopes
# ---------------------------------------------------------------------------

class ResponseEnvelope(BaseModel, Generic[T]):
    """Standardised success response wrapper.

    Every successful endpoint returns this shape::

        {
            "success": true,
            "data": { ... },
            "message": "Research session created",
            "errors": [],
            "correlation_id": "a3f1-..."
        }
    """

    success: bool = True
    data: T | None = None
    message: str | None = None
    errors: list[str] = Field(default_factory=list)
    correlation_id: str | None = None


class ErrorResponse(BaseModel):
    """Standardised error response wrapper.

    Every error handler returns this exact shape::

        {
            "success": false,
            "data": null,
            "message": "Research session not found",
            "error_code": "NOT_FOUND",
            "errors": ["No session with id 'abc' exists"],
            "correlation_id": "a3f1-...",
            "timestamp": "2026-07-29T12:00:00Z",
            "path": "/api/v1/research/abc"
        }

    The ``error_code`` field is machine-readable — clients can switch
    on it without parsing the human-readable ``message``.
    """

    success: bool = False
    data: None = None
    message: str
    error_code: str
    errors: list[str] = Field(default_factory=list)
    correlation_id: str | None = None
    timestamp: str | None = None
    path: str | None = None


# ---------------------------------------------------------------------------
# Pagination
# ---------------------------------------------------------------------------

class PaginationParams(BaseModel):
    """Pagination query parameters."""

    page: int = Field(default=1, ge=1, description="Page number (1-indexed)")
    page_size: int = Field(
        default=20, ge=1, le=100, description="Items per page (max 100)"
    )


class PaginatedResponse(BaseModel, Generic[T]):
    """Paginated response wrapper."""

    items: list[T]
    total: int
    page: int
    page_size: int
    total_pages: int
