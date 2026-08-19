import json
import logging
from typing import Any, Optional
from research_agent.app.memory.base import BaseCache

logger = logging.getLogger(__name__)


class RedisCache(BaseCache):
    """
    Redis-backed cache adapter implementing BaseCache with TTL expiration.
    Requires the `redis` package and a running Redis instance.
    """

    def __init__(self, redis_client: Any, default_ttl_seconds: Optional[int] = 3600):
        self.client = redis_client
        self.default_ttl = default_ttl_seconds

    def get(self, key: str) -> Optional[Any]:
        try:
            raw = self.client.get(key)
            if raw is None:
                return None
            return json.loads(raw)
        except Exception as e:
            logger.warning(f"Redis get failed for key '{key}': {e}")
            return None

    def set(self, key: str, value: Any, ttl_seconds: Optional[int] = None) -> None:
        try:
            raw = json.dumps(value, default=str)
            ttl = ttl_seconds if ttl_seconds is not None else self.default_ttl
            self.client.setex(key, ttl, raw)
        except Exception as e:
            logger.warning(f"Redis set failed for key '{key}': {e}")

    def has(self, key: str) -> bool:
        try:
            return bool(self.client.exists(key))
        except Exception as e:
            logger.warning(f"Redis exists check failed for key '{key}': {e}")
            return False

    def delete(self, key: str) -> bool:
        try:
            return bool(self.client.delete(key))
        except Exception as e:
            logger.warning(f"Redis delete failed for key '{key}': {e}")
            return False

    def clear(self) -> None:
        try:
            self.client.flushdb()
        except Exception as e:
            logger.warning(f"Redis flush failed: {e}")
