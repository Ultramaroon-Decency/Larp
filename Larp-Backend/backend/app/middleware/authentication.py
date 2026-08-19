"""Authentication middleware.

Provides JWT-based authentication as an ASGI middleware that runs on
**every** request.  Public paths (health checks, login, register, docs)
are whitelisted and skip verification entirely.

For protected routes the middleware:

1. Extracts the ``Authorization: Bearer <token>`` header.
2. Decodes and validates the JWT using ``core.security``.
3. Loads the user from the database (via ``UserRepository``).
4. Verifies the user is active.
5. Stores the authenticated user in ``request.state.user`` and a
   ``ContextVar`` so it's available to both route handlers and
   structlog processors.

If any step fails, the request is rejected **before** the route handler
runs, with a structured ``401`` or ``403`` JSON response that includes
the correlation ID for traceability.
"""

from contextvars import ContextVar
from typing import Any

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse, Response

from app.core.logging import get_logger
from app.core.security import decode_access_token
from app.middleware.correlation_id import get_correlation_id

logger = get_logger("auth")

# ---------------------------------------------------------------------------
# Context variable for the authenticated user
# ---------------------------------------------------------------------------

_current_user_ctx: ContextVar[dict | None] = ContextVar(
    "current_user", default=None
)


def get_current_user_from_ctx() -> dict | None:
    """Return the authenticated user dict for the current request."""
    return _current_user_ctx.get()


# ---------------------------------------------------------------------------
# Paths that do NOT require authentication
# ---------------------------------------------------------------------------

PUBLIC_PATH_PREFIXES: tuple[str, ...] = (
    "/docs",
    "/redoc",
    "/openapi.json",
    "/api/v1/openapi.json",
    "/api/v1/health",
    "/api/v1/auth/login",
    "/api/v1/auth/register",
    "/api/v1/auth/google",
    "/api/v1/auth/refresh",
    "/api/v1/research",  # Anonymous quick search allowed; deep mode enforced at endpoint level
    "/ws",
    "/api/v1/ws",
)


def _is_public(path: str) -> bool:
    """Return True if the path does not require a valid JWT."""
    normalised = path.rstrip("/")
    for prefix in PUBLIC_PATH_PREFIXES:
        if normalised == prefix.rstrip("/") or normalised.startswith(prefix.rstrip("/") + "/"):
            return True
    return False


# ---------------------------------------------------------------------------
# Error response helpers
# ---------------------------------------------------------------------------

def _auth_error(
    status_code: int,
    message: str,
    correlation_id: str,
) -> JSONResponse:
    return JSONResponse(
        status_code=status_code,
        content={
            "success": False,
            "data": None,
            "message": message,
            "errors": [message],
            "correlation_id": correlation_id,
        },
        headers={
            "WWW-Authenticate": "Bearer",
            "X-Request-ID": correlation_id,
        },
    )


# ---------------------------------------------------------------------------
# Middleware
# ---------------------------------------------------------------------------

class AuthenticationMiddleware(BaseHTTPMiddleware):
    """ASGI middleware that enforces JWT authentication.

    **Why a middleware instead of a FastAPI ``Depends()``?**

    Using ``Depends(get_current_user)`` is fine for most apps, but a
    middleware gives us:

    - A single enforcement point — impossible to forget ``Depends`` on
      a new route.
    - Access to ``request.state.user`` in *other* middleware (e.g.
      rate-limiter can apply per-user limits).
    - Cleaner route signatures (no ``current_user: dict = Depends(…)``
      boilerplate on every endpoint).

    The ``Depends``-based ``get_current_user`` in ``dependencies.py``
    still works — it simply reads from ``request.state.user`` rather
    than re-decoding the token.
    """

    async def dispatch(self, request: Request, call_next) -> Response:
        # ── Skip CORS preflight ────────────────────────────────────────
        if request.method == "OPTIONS":
            return await call_next(request)

        correlation_id = get_correlation_id()
        auth_header = request.headers.get("Authorization", "")

        # ── Skip public paths if no Bearer token is provided ───────────
        if _is_public(request.url.path) and not auth_header.startswith("Bearer "):
            return await call_next(request)

        # ── Extract Bearer token ───────────────────────────────────────
        if not auth_header.startswith("Bearer "):
            logger.warning(
                "Missing or malformed Authorization header",
                http_path=request.url.path,
                correlation_id=correlation_id,
            )
            return _auth_error(401, "Missing or malformed Authorization header", correlation_id)


        token = auth_header[7:]  # strip "Bearer "

        # ── Decode JWT ─────────────────────────────────────────────────
        try:
            payload = decode_access_token(token)
        except Exception:
            logger.warning(
                "Invalid or expired token",
                http_path=request.url.path,
                correlation_id=correlation_id,
            )
            return _auth_error(401, "Invalid or expired token", correlation_id)

        # ── Build user context from token claims ───────────────────────
        user: dict[str, Any] = {
            "id": payload.sub,
            "token_iat": payload.iat,
            "token_exp": payload.exp,
        }


        # ── Store in request state + contextvars ───────────────────────
        request.state.user = user
        _current_user_ctx.set(user)

        logger.debug(
            "Request authenticated",
            user_id=payload.sub,
            http_path=request.url.path,
            correlation_id=correlation_id,
        )

        return await call_next(request)

