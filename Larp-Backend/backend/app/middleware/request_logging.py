"""Request / response logging middleware.

Logs a structured pair of events for every HTTP request:

- **Request started** — method, path, query string, client IP, user-agent,
  content-length, and the correlation ID.
- **Request completed** — everything above plus the response status code,
  response size, and processing time in milliseconds.

The log level is chosen dynamically:

- ``DEBUG`` for health-check / readiness probes (to avoid log spam).
- ``WARNING`` for 4xx client errors.
- ``ERROR`` for 5xx server errors.
- ``INFO`` for everything else.
"""

import time

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

from app.core.logging import get_logger
from app.middleware.correlation_id import get_correlation_id

logger = get_logger("http")

# Paths that should be logged at DEBUG level to reduce noise.
_QUIET_PATHS: set[str] = {
    "/api/v1/health",
    "/api/v1/health/",
    "/api/v1/health/ready",
}


def _log_level_for_status(status_code: int) -> str:
    """Return the appropriate log-level name for a given HTTP status."""
    if status_code >= 500:
        return "error"
    if status_code >= 400:
        return "warning"
    return "info"


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    """Middleware that emits structured logs for every HTTP request.

    Works in tandem with ``CorrelationIdMiddleware`` — the correlation ID
    is already stored in ``contextvars`` by the time this middleware runs,
    so structlog's ``add_correlation_id`` processor includes it
    automatically.
    """

    async def dispatch(self, request: Request, call_next) -> Response:
        # ── Gather request metadata ────────────────────────────────────
        method = request.method
        path = request.url.path
        query = str(request.query_params) if request.query_params else ""
        client_ip = request.client.host if request.client else "unknown"
        user_agent = request.headers.get("user-agent", "")
        content_length = request.headers.get("content-length", "0")
        correlation_id = get_correlation_id()

        # Use DEBUG for noisy health-check endpoints
        is_quiet = path.rstrip("/") in {p.rstrip("/") for p in _QUIET_PATHS}
        log_fn = logger.debug if is_quiet else logger.info

        # ── Log: request started ───────────────────────────────────────
        log_fn(
            "Request started",
            http_method=method,
            http_path=path,
            http_query=query,
            client_ip=client_ip,
            user_agent=user_agent,
            content_length=content_length,
            correlation_id=correlation_id,
        )

        # ── Execute the route handler ──────────────────────────────────
        start = time.perf_counter()
        response = await call_next(request)
        duration_ms = round((time.perf_counter() - start) * 1000, 2)

        # ── Log: request completed ─────────────────────────────────────
        status = response.status_code
        response_size = response.headers.get("content-length", "unknown")

        # Pick log level based on the response status code
        if is_quiet and status < 400:
            completed_log = logger.debug
        else:
            completed_log = getattr(
                logger, _log_level_for_status(status)
            )

        completed_log(
            "Request completed",
            http_method=method,
            http_path=path,
            http_query=query,
            status_code=status,
            duration_ms=duration_ms,
            response_size=response_size,
            client_ip=client_ip,
            correlation_id=correlation_id,
        )

        return response
