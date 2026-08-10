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

from uuid import UUID

import app.database
from app.core.logging import get_logger
from app.core.security import decode_access_token
from app.middleware.correlation_id import get_correlation_id
from app.repositories.user_repository import UserRepository

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
        # ── Skip public paths ──────────────────────────────────────────
        if _is_public(request.url.path):
            return await call_next(request)

        # ── Skip CORS preflight ────────────────────────────────────────
        if request.method == "OPTIONS":
            return await call_next(request)

        correlation_id = get_correlation_id()

        # ── Extract Bearer token ───────────────────────────────────────
        auth_header = request.headers.get("Authorization", "")
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

        # ── Parse UUID subject ─────────────────────────────────────────
        try:
            user_id = UUID(payload.sub)
        except (ValueError, TypeError):
            logger.warning(
                "Invalid user ID in JWT subject claim",
                http_path=request.url.path,
                correlation_id=correlation_id,
            )
            return _auth_error(401, "Invalid token subject", correlation_id)

        # ── Query user from database & verify account status ────────────
        try:
            async with app.database.async_session_maker() as session:
                user_repo = UserRepository(session)
                db_user = await user_repo.get_by_id(user_id)
        except Exception as exc:
            logger.error(
                "Database error during user authentication lookup",
                error=str(exc),
                http_path=request.url.path,
                correlation_id=correlation_id,
            )
            return _auth_error(500, "Internal server error", correlation_id)

        if db_user is None:
            logger.warning(
                "User from JWT subject claim no longer exists",
                user_id=payload.sub,
                http_path=request.url.path,
                correlation_id=correlation_id,
            )
            return _auth_error(401, "User no longer exists", correlation_id)

        if not db_user.is_active:
            logger.warning(
                "Deactivated user attempted request",
                user_id=payload.sub,
                http_path=request.url.path,
                correlation_id=correlation_id,
            )
            return _auth_error(403, "User account is deactivated", correlation_id)

        # ── Build user context from database record ────────────────────
        user: dict[str, Any] = {
            "id": str(db_user.id),
            "email": db_user.email,
            "full_name": db_user.full_name,
            "role": db_user.role,
            "is_active": db_user.is_active,
            "is_superuser": db_user.is_superuser,
            "is_admin": db_user.is_admin,
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
