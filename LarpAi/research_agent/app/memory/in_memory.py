import time
import hashlib
import logging
from typing import Any, Dict, Optional, Tuple
from research_agent.app.memory.base import BaseCache

logger = logging.getLogger(__name__)


class InMemoryCache(BaseCache):
    """
    Lightweight in-memory cache provider with TTL expiration and MD5 key hashing support.
    Maintains a minimal RAM footprint (<10MB overhead) adhering to hardware constraints.
    """

    def __init__(self, default_ttl_seconds: Optional[int] = 3600, max_entries: int = 1000):
        self.default_ttl = default_ttl_seconds
        self.max_entries = max_entries
        # Storage format: key -> (value, expire_timestamp)
        self._store: Dict[str, Tuple[Any, Optional[float]]] = {}

    @staticmethod
    def generate_key(prefix: str, *parts: str) -> str:
        """
        Generates a deterministic MD5 hash cache key from string parts.
        """
        combined = ":".join(parts)
        digest = hashlib.md5(combined.encode("utf-8")).hexdigest()[:16]
        return f"{prefix}:{digest}"

    def _is_expired(self, expire_at: Optional[float]) -> bool:
        if expire_at is None:
            return False
        return time.time() > expire_at

    def get(self, key: str) -> Optional[Any]:
        if key not in self._store:
            return None

        val, expire_at = self._store[key]
        if self._is_expired(expire_at):
            logger.debug(f"Cache key '{key}' expired. Evicting.")
            del self._store[key]
            return None

        logger.debug(f"Cache hit for key '{key}'.")
        return val

    def set(self, key: str, value: Any, ttl_seconds: Optional[int] = None) -> None:
        # Enforce max capacity eviction if needed
        if len(self._store) >= self.max_entries and key not in self._store:
            # Purge expired keys first
            self._purge_expired()
            if len(self._store) >= self.max_entries:
                # Evict oldest key
                first_key = next(iter(self._store))
                del self._store[first_key]

        effective_ttl = ttl_seconds if ttl_seconds is not None else self.default_ttl
        expire_at = (time.time() + effective_ttl) if effective_ttl is not None else None
        self._store[key] = (value, expire_at)
        logger.debug(f"Cached key '{key}' (TTL: {effective_ttl}s).")

    def has(self, key: str) -> bool:
        return self.get(key) is not None

    def delete(self, key: str) -> bool:
        if key in self._store:
            del self._store[key]
            return True
        return False

    def clear(self) -> None:
        self._store.clear()
        logger.info("In-memory cache cleared.")

    def size(self) -> int:
        self._purge_expired()
        return len(self._store)

    def _purge_expired(self) -> None:
        now = time.time()
        expired_keys = [k for k, (_, expire_at) in self._store.items() if expire_at and now > expire_at]
        for k in expired_keys:
            del self._store[k]
