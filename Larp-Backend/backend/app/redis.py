"""Redis connection management module."""

from typing import Optional
from redis.asyncio import Redis, from_url

from app.config import get_settings

settings = get_settings()

redis_pool: Optional[Redis] = None


async def init_redis() -> None:
    """Initialize the Redis connection pool."""
    global redis_pool
    if redis_pool is None:
        redis_pool = from_url(settings.redis_url, decode_responses=True)


async def close_redis() -> None:
    """Close the Redis connection pool."""
    global redis_pool
    if redis_pool is not None:
        await redis_pool.aclose()
        redis_pool = None


async def get_redis() -> Redis:
    """Dependency for providing the Redis client instance."""
    if redis_pool is None:
        raise RuntimeError("Redis connection pool is not initialized")
    return redis_pool
