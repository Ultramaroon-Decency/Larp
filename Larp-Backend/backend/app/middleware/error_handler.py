"""Global exception handlers.

Registers **five** exception handlers on the FastAPI app, each
producing a standardised ``ErrorResponse`` JSON envelope with the
correlation ID for end-to-end traceability.

Handler priority (FastAPI matches the **most specific** type first):

1. ``AppException``            → domain errors (auth, not-found, conflict, DB, …)
2. ``RequestValidationError``  → Pydantic schema / query-param errors
3. ``HTTPException``           → FastAPI's own auth (OAuth2) and other HTTP errors
4. ``SQLAlchemyError``         → raw database errors not caught by services
5. ``Exception``               → everything else (bugs, OOM, …)

Every handler:
- Logs the error with structured fields + correlation ID.
- Returns the ``ErrorResponse`` schema (never leaks internals).
- Sets the ``X-Request-ID`` response header.
"""

import traceback
from datetime import datetime, timezone

from fastapi import FastAPI, HTTPException, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from sqlalchemy.exc import (
    IntegrityError as SAIntegrityError,
    OperationalError as SAOperationalError,
    SQLAlchemyError,
)

from app.core.exceptions import AppException
from app.core.logging import get_logger
from app.middleware.correlation_id import (
    CORRELATION_ID_HEADER,
    get_correlation_id,
)

logger = get_logger("error_handler")


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _build_error_response(
    status_code: int,
    message: str,
    error_code: str,
    errors: list[str],
    request: Request,
    correlation_id: str,
) -> JSONResponse:
    """Build a standardised error JSON response.

    This is the single function that produces **every** error response
    in the application, guaranteeing a consistent shape.
    """
    return JSONResponse(
        status_code=status_code,
        content={
            "success": False,
            "data": None,
            "message": message,
            "error_code": error_code,
            "errors": errors,
            "correlation_id": correlation_id,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "path": str(request.url.path),
        },
        headers={CORRELATION_ID_HEADER: correlation_id},
    )


def _log_level_for_status(status_code: int):
    """Return the appropriate structlog method for a given HTTP status."""
    if status_code >= 500:
        return logger.error
    if status_code >= 400:
        return logger.warning
    return logger.info


# ---------------------------------------------------------------------------
# Setup
# ---------------------------------------------------------------------------

def setup_error_handlers(app: FastAPI) -> None:
    """Register all exception handlers on the FastAPI application."""

    # ── 1. Custom application exceptions ───────────────────────────────
    @app.exception_handler(AppException)
    async def app_exception_handler(
        request: Request, exc: AppException
    ) -> JSONResponse:
        """Handle domain exceptions raised by services / routes.

        Covers: ``AuthenticationError``, ``AuthorizationError``,
        ``NotFoundError``, ``ConflictError``, ``ValidationError``,
        ``RateLimitError``, ``DatabaseError``, ``ExternalServiceError``.
        """
        correlation_id = get_correlation_id()

        _log_level_for_status(exc.status_code)(
            "Application error",
            error_type=type(exc).__name__,
            error_code=exc.error_code,
            message=exc.message,
            status_code=exc.status_code,
            errors=exc.errors,
            http_method=request.method,
            http_path=request.url.path,
            correlation_id=correlation_id,
        )

        return _build_error_response(
            status_code=exc.status_code,
            message=exc.message,
            error_code=exc.error_code,
            errors=exc.errors,
            request=request,
            correlation_id=correlation_id,
        )

    # ── 2. Pydantic / FastAPI validation errors ────────────────────────
    @app.exception_handler(RequestValidationError)
    async def validation_exception_handler(
        request: Request, exc: RequestValidationError
    ) -> JSONResponse:
        """Handle request body / query param / path param validation.

        Transforms Pydantic's raw error dicts into human-readable
        strings like ``"body → email: value is not a valid email"``.
        """
        correlation_id = get_correlation_id()

        field_errors: list[str] = []
        for error in exc.errors():
            loc = " → ".join(str(part) for part in error["loc"])
            field_errors.append(f"{loc}: {error['msg']}")

        logger.warning(
            "Validation error",
            error_code="VALIDATION_ERROR",
            error_count=len(field_errors),
            errors=field_errors,
            http_method=request.method,
            http_path=request.url.path,
            correlation_id=correlation_id,
        )

        return _build_error_response(
            status_code=422,
            message="Validation failed",
            error_code="VALIDATION_ERROR",
            errors=field_errors,
            request=request,
            correlation_id=correlation_id,
        )

    # ── 3. FastAPI HTTPException (OAuth2, manual raises) ───────────────
    @app.exception_handler(HTTPException)
    async def http_exception_handler(
        request: Request, exc: HTTPException
    ) -> JSONResponse:
        """Handle FastAPI's built-in HTTPExceptions.

        These come from ``OAuth2PasswordBearer`` (401), FastAPI's
        dependency injection failures, and any manual
        ``raise HTTPException(...)`` calls in the codebase.
        """
        correlation_id = get_correlation_id()

        # Map status codes to error_code strings
        code_map = {
            400: "BAD_REQUEST",
            401: "AUTH_FAILED",
            403: "FORBIDDEN",
            404: "NOT_FOUND",
            405: "METHOD_NOT_ALLOWED",
            429: "RATE_LIMIT_EXCEEDED",
        }
        error_code = code_map.get(exc.status_code, "HTTP_ERROR")

        _log_level_for_status(exc.status_code)(
            "HTTP exception",
            error_code=error_code,
            status_code=exc.status_code,
            detail=exc.detail,
            http_method=request.method,
            http_path=request.url.path,
            correlation_id=correlation_id,
        )

        return _build_error_response(
            status_code=exc.status_code,
            message=str(exc.detail),
            error_code=error_code,
            errors=[str(exc.detail)] if exc.detail else [],
            request=request,
            correlation_id=correlation_id,
        )

    # ── 4. SQLAlchemy database errors ──────────────────────────────────
    @app.exception_handler(SQLAlchemyError)
    async def database_exception_handler(
        request: Request, exc: SQLAlchemyError
    ) -> JSONResponse:
        """Handle raw SQLAlchemy errors not caught by the service layer.

        - ``IntegrityError`` (unique / FK violation) → 409 Conflict.
        - ``OperationalError`` (connection lost) → 503 Service Unavailable.
        - Everything else → 503.

        The **raw SQL error is never sent to the client** — only a safe
        generic message.  The full details are logged server-side.
        """
        correlation_id = get_correlation_id()

        if isinstance(exc, SAIntegrityError):
            status_code = 409
            message = "Data integrity constraint violated"
            error_code = "DB_INTEGRITY_ERROR"
        elif isinstance(exc, SAOperationalError):
            status_code = 503
            message = "Database connection failed"
            error_code = "DB_CONNECTION_FAILED"
        else:
            status_code = 503
            message = "A database error occurred"
            error_code = "DATABASE_ERROR"

        logger.error(
            "Database error",
            error_type=type(exc).__name__,
            error_code=error_code,
            error=str(exc),
            traceback=traceback.format_exc(),
            http_method=request.method,
            http_path=request.url.path,
            correlation_id=correlation_id,
        )

        return _build_error_response(
            status_code=status_code,
            message=message,
            error_code=error_code,
            errors=[],  # never leak SQL details
            request=request,
            correlation_id=correlation_id,
        )

    # ── 5. Catch-all for unexpected errors ─────────────────────────────
    @app.exception_handler(Exception)
    async def global_exception_handler(
        request: Request, exc: Exception
    ) -> JSONResponse:
        """Handle any exception not caught by the above handlers.

        Logs the **full traceback** for debugging but returns only a
        generic message — internal details are never exposed.
        """
        correlation_id = get_correlation_id()

        logger.error(
            "Unhandled exception",
            error_type=type(exc).__name__,
            error_code="INTERNAL_ERROR",
            error=str(exc),
            traceback=traceback.format_exc(),
            http_method=request.method,
            http_path=request.url.path,
            correlation_id=correlation_id,
        )

        return _build_error_response(
            status_code=500,
            message="An unexpected error occurred. Please try again later.",
            error_code="INTERNAL_ERROR",
            errors=[],
            request=request,
            correlation_id=correlation_id,
        )
