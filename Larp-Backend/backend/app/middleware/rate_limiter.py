"""Rate limiting middleware using Redis sliding window.

Implements a per-IP sliding-window rate limiter backed by Redis.
Each client IP gets a budget of ``RATE_LIMIT_REQUESTS`` requests per
``RATE_LIMIT_WINDOW_SECONDS``.  When exceeded, the middleware returns
``429 Too Many Requests`` with ``Retry-After`` and standard
``X-RateLimit-*`` headers.

Design decisions:

- **Redis-backed** — works correctly across multiple app instances
  behind a load balancer (unlike in-memory counters).
- **Sliding window** — uses a Redis sorted set with timestamped members,
  giving smoother rate control than fixed-window counters.
- **Graceful degradation** — if Redis is unavailable, requests are
  **allowed through** (fail-open) with a warning log, rather than
  blocking all traffic.
- **Public paths exempt** — health checks are never rate-limited.
"""

import time

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse, Response

from app.core.logging import get_logger
from app.middleware.correlation_id import get_correlation_id

logger = get_logger("rate_limiter")

# Paths exempt from rate limiting
_EXEMPT_PATHS: tuple[str, ...] = (
    "/docs",
    "/redoc",
    "/openapi.json",
    "/api/v1/openapi.json",
    "/api/v1/health",
)


def _is_exempt(path: str) -> bool:
    """Return True if this path should skip rate limiting."""
    normalised = path.rstrip("/")
    for prefix in _EXEMPT_PATHS:
        if normalised == prefix.rstrip("/") or normalised.startswith(prefix.rstrip("/") + "/"):
            return True
    return False


class RateLimitMiddleware(BaseHTTPMiddleware):
    """Sliding-window rate limiter backed by Redis.

    Constructor args:
        max_requests:   Maximum requests allowed in the window.
        window_seconds: Size of the sliding window in seconds.

    Adds three response headers to every response:

    - ``X-RateLimit-Limit``     — the configured max.
    - ``X-RateLimit-Remaining`` — how many requests the client has left.
    - ``X-RateLimit-Reset``     — Unix timestamp when the window resets.

    On ``429``, also adds ``Retry-After`` (seconds until the next slot).
    """

    def __init__(
        self,
        app,
        max_requests: int = 100,
        window_seconds: int = 60,
    ) -> None:
        super().__init__(app)
        self.max_requests = max_requests
        self.window_seconds = window_seconds

    async def dispatch(self, request: Request, call_next) -> Response:
        # ── Skip exempt paths ──────────────────────────────────────────
        if _is_exempt(request.url.path):
            return await call_next(request)

        # ── Identify the client ────────────────────────────────────────
        # Use X-Forwarded-For if behind a reverse proxy, else client IP.
        forwarded = request.headers.get("X-Forwarded-For")
        if forwarded:
            client_ip = forwarded.split(",")[0].strip()
        else:
            client_ip = request.client.host if request.client else "unknown"

        correlation_id = get_correlation_id()
        redis_key = f"rate_limit:{client_ip}"
        now = time.time()
        window_start = now - self.window_seconds

        # ── Check rate limit via Redis ─────────────────────────────────
        try:
            from app.redis import get_redis
            redis = await get_redis()

            # Pipeline: remove old entries, add current, count, get TTL
            pipe = redis.pipeline(transaction=True)
            pipe.zremrangebyscore(redis_key, 0, window_start)
            pipe.zadd(redis_key, {f"{now}:{correlation_id}": now})
            pipe.zcard(redis_key)
            pipe.expire(redis_key, self.window_seconds)
            results = await pipe.execute()

            request_count = results[2]  # zcard result

        except Exception as exc:
            # ── Fail-open: if Redis is down, allow the request ─────────
            logger.warning(
                "Rate limiter Redis error — failing open",
                error=str(exc),
                client_ip=client_ip,
                correlation_id=correlation_id,
            )
            return await call_next(request)

        # ── Calculate remaining budget ─────────────────────────────────
        remaining = max(0, self.max_requests - request_count)
        reset_at = int(now + self.window_seconds)

        # ── Rate limit exceeded ────────────────────────────────────────
        if request_count > self.max_requests:
            retry_after = self.window_seconds

            logger.warning(
                "Rate limit exceeded",
                client_ip=client_ip,
                request_count=request_count,
                max_requests=self.max_requests,
                http_path=request.url.path,
                correlation_id=correlation_id,
            )

            return JSONResponse(
                status_code=429,
                content={
                    "success": False,
                    "data": None,
                    "message": "Rate limit exceeded. Please slow down.",
                    "errors": [
                        f"Maximum {self.max_requests} requests per "
                        f"{self.window_seconds} seconds exceeded"
                    ],
                    "correlation_id": correlation_id,
                },
                headers={
                    "Retry-After": str(retry_after),
                    "X-RateLimit-Limit": str(self.max_requests),
                    "X-RateLimit-Remaining": "0",
                    "X-RateLimit-Reset": str(reset_at),
                    "X-Request-ID": correlation_id,
                },
            )

        # ── Allow request — add rate-limit headers ─────────────────────
        response = await call_next(request)
        response.headers["X-RateLimit-Limit"] = str(self.max_requests)
        response.headers["X-RateLimit-Remaining"] = str(remaining)
        response.headers["X-RateLimit-Reset"] = str(reset_at)
        return response
