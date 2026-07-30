"""Correlation ID context management.

Provides a ``contextvars``-based correlation ID that flows automatically
through the entire async call-chain of a single request.  The middleware
sets the ID at the start of each request, and the structlog processor
injects it into every log line — no manual passing required.

Flow::

    Client Request
        │
        ▼
    CorrelationIdMiddleware
        ├─ reads  X-Request-ID header  (or generates a UUID4)
        ├─ stores in  contextvars.ContextVar
        ├─ sets  response header  X-Request-ID
        │
        ▼
    structlog processor  (add_correlation_id)
        └─ reads the ContextVar → adds  "correlation_id"  to every log dict
"""

import uuid
from contextvars import ContextVar

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

# ---------------------------------------------------------------------------
# Context variable — one value per async task (= per request)
# ---------------------------------------------------------------------------

_correlation_id_ctx: ContextVar[str] = ContextVar(
    "correlation_id", default=""
)

# Header name used by API gateways, load balancers, and clients.
CORRELATION_ID_HEADER = "X-Request-ID"


# ---------------------------------------------------------------------------
# Public helpers
# ---------------------------------------------------------------------------

def get_correlation_id() -> str:
    """Return the current request's correlation ID (or empty string)."""
    return _correlation_id_ctx.get()


def set_correlation_id(value: str) -> None:
    """Explicitly set a correlation ID (used by the middleware)."""
    _correlation_id_ctx.set(value)


# ---------------------------------------------------------------------------
# structlog processor
# ---------------------------------------------------------------------------

def add_correlation_id(
    logger: object,
    method_name: str,
    event_dict: dict,
) -> dict:
    """Structlog processor that injects the correlation ID into every log.

    Add this to the processor chain in ``setup_logging()`` so that every
    log entry automatically contains ``"correlation_id": "abc-123-…"``.
    """
    cid = _correlation_id_ctx.get()
    if cid:
        event_dict["correlation_id"] = cid
    return event_dict


# ---------------------------------------------------------------------------
# ASGI middleware
# ---------------------------------------------------------------------------

class CorrelationIdMiddleware(BaseHTTPMiddleware):
    """Middleware that manages per-request correlation IDs.

    For each incoming request:

    1. **Read** — If the client sent an ``X-Request-ID`` header, use it.
       This supports distributed tracing across micro-services.
    2. **Generate** — Otherwise, create a fresh UUID4.
    3. **Store** — Set the value in a ``ContextVar`` so that every
       ``structlog`` log line in this request includes it automatically.
    4. **Echo** — Return the same ID in the ``X-Request-ID`` response
       header so the client can quote it in bug reports.
    """

    async def dispatch(self, request: Request, call_next) -> Response:
        # 1. Read from header or generate
        correlation_id = request.headers.get(
            CORRELATION_ID_HEADER, str(uuid.uuid4())
        )

        # 2. Store in contextvars (flows through all awaited calls)
        _correlation_id_ctx.set(correlation_id)

        # 3. Process the request
        response = await call_next(request)

        # 4. Echo back in response header
        response.headers[CORRELATION_ID_HEADER] = correlation_id

        return response
