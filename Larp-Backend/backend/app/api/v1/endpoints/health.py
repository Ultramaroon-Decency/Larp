"""Health check endpoints.

Provides two endpoints:

- ``GET /health/``     — liveness probe (always 200 if the process is alive).
- ``GET /health/ready`` — readiness probe (checks DB pool + Redis connectivity).
"""

from datetime import datetime, timezone

from fastapi import APIRouter, Depends
from redis.asyncio import Redis

from app.config import get_settings
from app.database import check_db_health
from app.schemas.common import ResponseEnvelope
from app.dependencies import get_redis_client

router = APIRouter()
settings = get_settings()


@router.get("/", response_model=ResponseEnvelope)
async def health_check() -> ResponseEnvelope:
    """Return basic health status, version, and environment."""
    return ResponseEnvelope(
        success=True,
        message="Service is healthy",
        data={
            "status": "healthy",
            "version": settings.app_version,
            "environment": settings.environment.value,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        },
    )


@router.get("/ready", response_model=ResponseEnvelope)
async def readiness_check(
    redis: Redis = Depends(get_redis_client),
) -> ResponseEnvelope:
    """Verify database and Redis connectivity for readiness probes.

    Uses ``check_db_health()`` which also reports pool statistics
    (pool_size, checked_in, checked_out, overflow).
    """
    checks: dict = {}

    # ── Database (with pool stats) ─────────────────────────────────────
    db_health = await check_db_health()
    checks["database"] = db_health

    # ── Redis ──────────────────────────────────────────────────────────
    try:
        await redis.ping()
        checks["redis"] = {"status": "healthy"}
    except Exception as exc:
        checks["redis"] = {"status": "unhealthy", "error": str(exc)}

    all_ok = all(
        c.get("status") == "healthy" for c in checks.values()
    )

    return ResponseEnvelope(
        success=all_ok,
        message="Service is ready" if all_ok else "Service is degraded",
        data={"status": "ready" if all_ok else "degraded", **checks},
    )
