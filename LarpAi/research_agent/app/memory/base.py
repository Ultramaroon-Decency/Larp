from abc import ABC, abstractmethod
from typing import Any, Optional


class BaseCache(ABC):
    """
    Abstract Base Class for cache providers in Larp AI.
    Enables low coupling so in-memory, Redis, or SQLite providers can be plugged in seamlessly.
    """

    @abstractmethod
    def get(self, key: str) -> Optional[Any]:
        """
        Retrieves a value from cache by key.
        Returns None if key is missing or expired.
        """
        pass

    @abstractmethod
    def set(self, key: str, value: Any, ttl_seconds: Optional[int] = None) -> None:
        """
        Stores a key-value pair in cache with an optional TTL (Time To Live).
        """
        pass

    @abstractmethod
    def has(self, key: str) -> bool:
        """
        Checks if a key exists and is unexpired in cache.
        """
        pass

    @abstractmethod
    def delete(self, key: str) -> bool:
        """
        Deletes a key from cache. Returns True if key existed.
        """
        pass

    @abstractmethod
    def clear(self) -> None:
        """
        Clears all stored entries from cache.
        """
        pass
