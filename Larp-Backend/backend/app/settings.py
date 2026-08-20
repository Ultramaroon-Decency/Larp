"""Application settings module.

Defines the ``Settings`` class which loads and validates all configuration
from environment variables and an optional ``.env`` file.

Best practices applied:
    1. **Fail fast** — Required fields have no defaults; the app won't start
       if they are missing.
    2. **Validate at the boundary** — Field validators run at import time,
       catching bad config before any request is served.
    3. **Constrained types** — ``Field(ge=…, le=…)`` prevents nonsensical
       values (e.g. negative token TTLs or empty secrets).
    4. **Enum for environment** — Prevents typos like ``"prodction"`` that
       would silently fall through string comparisons.
    5. **Computed properties** — Derived values (``is_production``,
       ``access_token_expire_timedelta``) are calculated once, not
       scattered across the codebase.
    6. **Immutable after load** — ``frozen = True`` prevents accidental
       mutation of global config at runtime.
    7. **Single instance** — ``get_settings()`` is ``@lru_cache``-decorated
       so the Settings object is created exactly once.
"""

from datetime import timedelta
from enum import Enum
from functools import lru_cache
from typing import List

from pydantic import Field, field_validator, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


# ---------------------------------------------------------------------------
# Environment Enum
# ---------------------------------------------------------------------------

class EnvironmentType(str, Enum):
    """Allowed runtime environments.

    Using an enum instead of a bare ``str`` ensures that a typo like
    ``ENVIRONMENT="prodction"`` raises a validation error at startup
    rather than silently behaving as a development build.
    """

    DEVELOPMENT = "development"
    STAGING = "staging"
    PRODUCTION = "production"
    TESTING = "testing"


# ---------------------------------------------------------------------------
# Settings
# ---------------------------------------------------------------------------

class Settings(BaseSettings):
    """Application settings loaded from environment variables / ``.env``.

    Fields are grouped by concern.  Required fields (no default) will
    cause a ``ValidationError`` if the corresponding env var is missing,
    making misconfiguration impossible to ignore.
    """

    # ── Application ────────────────────────────────────────────────────
    app_name: str = Field(
        default="Research Agent API",
        min_length=1,
        max_length=100,
        description="Human-readable application name shown in Swagger UI.",
    )
    app_version: str = Field(
        default="0.1.0",
        pattern=r"^\d+\.\d+\.\d+$",
        description="Semantic version string (e.g. 1.2.3).",
    )
    debug: bool = Field(
        default=False,
        description="Enable debug mode. MUST be False in production.",
    )
    environment: EnvironmentType = Field(
        default=EnvironmentType.DEVELOPMENT,
        description="Runtime environment. Controls log format, debug flags, etc.",
    )

    # ── Database ───────────────────────────────────────────────────────
    database_url: str = Field(
        ...,
        min_length=10,
        description="Async PostgreSQL connection string (postgresql+asyncpg://…).",
    )
    database_echo: bool = Field(
        default=False,
        description="Echo all SQL statements to the log. Useful for debugging.",
    )
    database_pool_size: int = Field(
        default=5,
        ge=1,
        le=100,
        description="Number of permanent connections in the pool.",
    )
    database_pool_max_overflow: int = Field(
        default=10,
        ge=0,
        le=100,
        description="Extra connections allowed above pool_size under load.",
    )
    database_pool_timeout: int = Field(
        default=30,
        ge=1,
        le=120,
        description="Seconds to wait for a pool connection before raising.",
    )
    database_pool_recycle: int = Field(
        default=1800,
        ge=60,
        le=7200,
        description="Seconds before a connection is recycled (prevents stale).",
    )
    database_pool_pre_ping: bool = Field(
        default=True,
        description="Test connections before use (detects disconnects).",
    )

    # ── Redis ──────────────────────────────────────────────────────────
    redis_url: str = Field(
        ...,
        min_length=5,
        description="Redis connection string (redis://…).",
    )

    # ── JWT / Auth ─────────────────────────────────────────────────────
    jwt_secret_key: str = Field(
        ...,
        min_length=16,
        description=(
            "HMAC signing key for JWT tokens. "
            "Must be at least 16 characters in production."
        ),
    )
    jwt_algorithm: str = Field(
        default="HS256",
        description="JWT signing algorithm.",
    )
    access_token_expire_minutes: int = Field(
        default=1440,
        ge=1,
        le=43200,
        description="Access-token lifetime in minutes (1 min – 30 days).",
    )
    refresh_token_expire_days: int = Field(
        default=7,
        ge=1,
        le=90,
        description="Refresh-token lifetime in days (1 day – 90 days).",
    )

    # ── Google OAuth ──────────────────────────────────────────────────
    google_client_id: str = Field(
        default="",
        description="Google OAuth2 client ID for server-side ID token verification.",
    )

    # ── CORS ───────────────────────────────────────────────────────────
    cors_origins: List[str] = Field(
        default_factory=list,
        description=(
            "List of allowed CORS origins. "
            "Set to '[\"*\"]' to allow all (NOT recommended in production)."
        ),
    )

    # ── Logging ────────────────────────────────────────────────────────
    log_level: str = Field(
        default="INFO",
        description="Python log level (DEBUG, INFO, WARNING, ERROR, CRITICAL).",
    )

    # ── Rate Limiting ──────────────────────────────────────────────────
    rate_limit_requests: int = Field(
        default=100,
        ge=1,
        le=10000,
        description="Max requests per IP per window (1–10 000).",
    )
    rate_limit_window_seconds: int = Field(
        default=60,
        ge=1,
        le=3600,
        description="Sliding window size in seconds (1 s – 1 hour).",
    )

    # ── AI API Keys ─────────────────────────────────────────────────────
    groq_api_key: str = Field(default="", description="Groq API key")
    tavily_api_key: str = Field(default="", description="Tavily API key")
    gemini_api_key: str = Field(default="", description="Gemini API key")
    openai_api_key: str = Field(default="", description="OpenAI API key")
    anthropic_api_key: str = Field(default="", description="Anthropic API key")

    # ── Compression ────────────────────────────────────────────────────
    gzip_minimum_size: int = Field(
        default=500,
        ge=0,
        description=(
            "Minimum response body size in bytes before GZip compression "
            "kicks in.  Set to 0 to compress everything."
        ),
    )

    # ── Pydantic Settings Configuration ────────────────────────────────
    model_config = SettingsConfigDict(
        # Load variables from a .env file in the project root.
        env_file=".env",
        env_file_encoding="utf-8",
        # Environment variables are case-insensitive
        # (DATABASE_URL, database_url, Database_Url all work).
        case_sensitive=False,
        # Freeze the settings object to prevent accidental mutation.
        frozen=True,
        # Ignore extra fields in the .env file (like groq_api_key) instead of crashing.
        extra="ignore",
    )

    # ── Field-Level Validators ────────────────────────────────────────

    @field_validator("log_level")
    @classmethod
    def validate_log_level(cls, v: str) -> str:
        """Ensure log_level is a recognised Python level."""
        allowed = {"DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"}
        normalised = v.upper().strip()
        if normalised not in allowed:
            raise ValueError(
                f"log_level must be one of {allowed}, got '{v}'"
            )
        return normalised

    @field_validator("database_url")
    @classmethod
    def validate_database_url(cls, v: str) -> str:
        """Ensure the database URL uses the async driver (automatically converts Railway postgres:// and postgresql://)."""
        if v.startswith("postgres://"):
            v = "postgresql+asyncpg://" + v[11:]
        elif v.startswith("postgresql://") and not v.startswith("postgresql+asyncpg://"):
            v = "postgresql+asyncpg://" + v[13:]

        if not v.startswith(("postgresql+asyncpg://", "sqlite+aiosqlite://")):
            raise ValueError(
                "database_url must start with 'postgresql+asyncpg://' "
                "(or 'sqlite+aiosqlite://' for testing). "
                f"Got: '{v[:30]}…'"
            )
        return v

    @field_validator("redis_url")
    @classmethod
    def validate_redis_url(cls, v: str) -> str:
        """Ensure the Redis URL uses a valid scheme."""
        if not v.startswith(("redis://", "rediss://")):
            raise ValueError(
                "redis_url must start with 'redis://' or 'rediss://'. "
                f"Got: '{v[:30]}…'"
            )
        return v

    @field_validator("cors_origins", mode="before")
    @classmethod
    def parse_cors_origins(cls, v):
        """Accept a JSON-encoded string or a Python list.

        This lets the .env file use:
            CORS_ORIGINS='["http://localhost:3000"]'
        while Python code can pass a regular list.
        """
        import json

        if isinstance(v, str):
            try:
                parsed = json.loads(v)
                if isinstance(parsed, list):
                    return parsed
            except json.JSONDecodeError:
                # Treat comma-separated as fallback:
                # CORS_ORIGINS=http://localhost:3000,http://localhost:8080
                return [origin.strip() for origin in v.split(",") if origin.strip()]
        return v

    @field_validator("jwt_algorithm")
    @classmethod
    def validate_jwt_algorithm(cls, v: str) -> str:
        """Only allow known secure algorithms."""
        allowed = {"HS256", "HS384", "HS512", "RS256", "RS384", "RS512", "ES256"}
        if v not in allowed:
            raise ValueError(
                f"jwt_algorithm must be one of {allowed}, got '{v}'"
            )
        return v

    # ── Cross-Field (Model-Level) Validator ────────────────────────────

    @model_validator(mode="after")
    def validate_production_settings(self) -> "Settings":
        """Enforce stricter rules when running in production.

        This is a *model validator* — it runs after all individual fields
        are validated and has access to the fully constructed object.
        """
        if self.environment == EnvironmentType.PRODUCTION:
            if self.debug:
                raise ValueError(
                    "debug must be False in production"
                )
            if self.jwt_secret_key in (
                "super-secret-key-change-me",
                "changeme",
                "secret",
            ):
                raise ValueError(
                    "jwt_secret_key must be changed from the default "
                    "value in production"
                )
            if self.database_echo:
                raise ValueError(
                    "database_echo must be False in production "
                    "(SQL logging is a performance and security risk)"
                )
        return self

    # ── Computed Properties ────────────────────────────────────────────

    @property
    def is_production(self) -> bool:
        """Convenience check used across the codebase."""
        return self.environment == EnvironmentType.PRODUCTION

    @property
    def is_development(self) -> bool:
        """Convenience check used for dev-only features."""
        return self.environment == EnvironmentType.DEVELOPMENT

    @property
    def is_testing(self) -> bool:
        """Convenience check used in test harnesses."""
        return self.environment == EnvironmentType.TESTING

    @property
    def access_token_expire_timedelta(self) -> timedelta:
        """Return access token lifetime as a ``timedelta`` for ``jose.jwt``."""
        return timedelta(minutes=self.access_token_expire_minutes)

    @property
    def refresh_token_expire_timedelta(self) -> timedelta:
        """Return refresh token lifetime as a ``timedelta`` for ``jose.jwt``."""
        return timedelta(days=self.refresh_token_expire_days)


# ---------------------------------------------------------------------------
# Singleton Accessor
# ---------------------------------------------------------------------------

@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """Return a cached ``Settings`` instance.

    Using ``@lru_cache`` ensures the ``.env`` file is read and validated
    exactly once, at first access.  Every subsequent call returns the
    same object with zero overhead.
    """
    return Settings()
