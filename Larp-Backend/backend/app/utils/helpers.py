"""Miscellaneous helper functions."""
import uuid
from datetime import datetime, timezone

def generate_uuid() -> uuid.UUID:
    """Generate a random UUID4."""
    return uuid.uuid4()

def utc_now() -> datetime:
    """Return timezone-aware UTC current datetime."""
    return datetime.now(timezone.utc)

def sanitize_string(value: str) -> str:
    """Strip and lowercase a string."""
    if not value:
        return value
    return str(value).strip().lower()
