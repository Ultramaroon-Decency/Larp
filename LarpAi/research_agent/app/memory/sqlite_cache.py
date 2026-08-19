import json
import sqlite3
import time
import logging
from typing import Any, Optional
from research_agent.app.memory.base import BaseCache

logger = logging.getLogger(__name__)


class SqliteCache(BaseCache):
    """
    SQLite-backed cache and persistence adapter implementing BaseCache.
    Stores key-value pairs with TTL in a single table.
    Useful for lightweight persistence without external dependencies.
    """

    def __init__(self, db_path: str = "research_cache.db", default_ttl_seconds: Optional[int] = 3600):
        self.db_path = db_path
        self.default_ttl = default_ttl_seconds
        self._conn: Optional[sqlite3.Connection] = None
        self._init_db()

    @property
    def conn(self) -> sqlite3.Connection:
        if self._conn is None:
            self._conn = sqlite3.connect(self.db_path)
            self._conn.row_factory = sqlite3.Row
        return self._conn

    def _init_db(self) -> None:
        c = self.conn.cursor()
        c.execute(
            "CREATE TABLE IF NOT EXISTS cache ("
            "  key TEXT PRIMARY KEY,"
            "  value TEXT NOT NULL,"
            "  expire_at REAL"
            ")"
        )
        self.conn.commit()

    def get(self, key: str) -> Optional[Any]:
        try:
            c = self.conn.cursor()
            c.execute("SELECT value, expire_at FROM cache WHERE key = ?", (key,))
            row = c.fetchone()
            if row is None:
                return None
            if row["expire_at"] is not None and time.time() > row["expire_at"]:
                self.delete(key)
                return None
            return json.loads(row["value"])
        except Exception as e:
            logger.warning(f"SQLite get failed for key '{key}': {e}")
            return None

    def set(self, key: str, value: Any, ttl_seconds: Optional[int] = None) -> None:
        try:
            raw = json.dumps(value, default=str)
            ttl = ttl_seconds if ttl_seconds is not None else self.default_ttl
            expire_at = (time.time() + ttl) if ttl is not None else None
            c = self.conn.cursor()
            c.execute(
                "INSERT OR REPLACE INTO cache (key, value, expire_at) VALUES (?, ?, ?)",
                (key, raw, expire_at)
            )
            self.conn.commit()
        except Exception as e:
            logger.warning(f"SQLite set failed for key '{key}': {e}")

    def has(self, key: str) -> bool:
        return self.get(key) is not None

    def delete(self, key: str) -> bool:
        try:
            c = self.conn.cursor()
            c.execute("DELETE FROM cache WHERE key = ?", (key,))
            self.conn.commit()
            return c.rowcount > 0
        except Exception as e:
            logger.warning(f"SQLite delete failed for key '{key}': {e}")
            return False

    def clear(self) -> None:
        try:
            c = self.conn.cursor()
            c.execute("DELETE FROM cache")
            self.conn.commit()
        except Exception as e:
            logger.warning(f"SQLite clear failed: {e}")

    def close(self) -> None:
        if self._conn:
            self._conn.close()
            self._conn = None
