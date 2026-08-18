import os
from typing import Literal
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    """
    Application Settings configured via environment variables.
    Provides fallback defaults for development configurations.
    """
    APP_NAME: str = "Larp AI"
    APP_ENV: Literal["development", "production", "testing"] = "development"
    DEBUG: bool = True
    PORT: int = 8000
    HOST: str = "0.0.0.0"
    
    # Cloud-based LLM API Keys (optional at startup, verified at service instantiation)
    OPENAI_API_KEY: str | None = None
    GEMINI_API_KEY: str | None = None
    ANTHROPIC_API_KEY: str | None = None
    
    # Third-party Integrations
    SERPER_API_KEY: str | None = None
    TAVILY_API_KEY: str | None = None

    # Cache / Persistence
    REDIS_URL: str | None = None
    SQLITE_DB_PATH: str = "research_cache.db"

    # Load from .env file if it exists
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )

# Singleton configuration instance
settings = Settings()
