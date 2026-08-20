"""Database connection, pool management, and session lifecycle.

This module is the **single entry point** for all database access.
It creates a connection-pooled async engine, a session factory, and
exposes helpers for startup / shutdown / health checks.

Architecture::

    ┌─────────────────────────────────────────────────────┐
    │               create_async_engine                    │
    │  ┌────────────────────────────────────────────────┐  │
    │  │          QueuePool (connection pool)            │  │
    │  │                                                │  │
    │  │   pool_size=5 permanent connections             │  │
    │  │   max_overflow=10 burst connections             │  │
    │  │   pool_timeout=30s wait before TimeoutError     │  │
    │  │   pool_recycle=1800s prevent stale connections  │  │
    │  │   pool_pre_ping=True detect disconnects         │  │
    │  └────────────────────────────────────────────────┘  │
    └─────────────────────────────────────────────────────┘
                          │
                          ▼
    ┌─────────────────────────────────────────────────────┐
    │           async_sessionmaker → AsyncSession          │
    │                                                      │
    │   expire_on_commit=False  (safe for response data)  │
    │   autoflush=False         (explicit flush control)  │
    └─────────────────────────────────────────────────────┘
"""

from typing import AsyncGenerator

from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from app.config import get_settings
from app.core.logging import get_logger

logger = get_logger("database")

# ---------------------------------------------------------------------------
# Engine & Session Factory (module-level singletons)
# ---------------------------------------------------------------------------

settings = get_settings()

engine_kwargs = {
    "echo": settings.database_echo,
    "future": True,
}
if not settings.database_url.startswith("sqlite"):
    engine_kwargs.update({
        "pool_size": settings.database_pool_size,
        "max_overflow": settings.database_pool_max_overflow,
        "pool_timeout": settings.database_pool_timeout,
        "pool_recycle": settings.database_pool_recycle,
        "pool_pre_ping": settings.database_pool_pre_ping,
    })

engine: AsyncEngine = create_async_engine(settings.database_url, **engine_kwargs)

async_session_maker = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autoflush=False,
    autocommit=False,
)


# ---------------------------------------------------------------------------
# Lifecycle Hooks (called from main.py lifespan)
# ---------------------------------------------------------------------------

async def init_db() -> None:
    """Verify database connectivity at startup and create tables if needed."""
    try:
        from app.models.base import Base
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
            await conn.execute(text("SELECT 1"))
        logger.info(
            "Database connected",
            url=settings.database_url.split("@")[-1],
        )
    except Exception as exc:
        logger.warning(
            "Database connection failed — running in offline mode",
            error=str(exc),
        )



async def close_db() -> None:
    """Dispose of all pooled connections at shutdown."""
    await engine.dispose()
    logger.info("Database connections closed")


# ---------------------------------------------------------------------------
# Health Check
# ---------------------------------------------------------------------------

async def check_db_health() -> dict:
    """Run a lightweight health check against the database.

    Returns a dict with ``"status": "healthy"`` or ``"unhealthy"``
    plus pool statistics.  Used by the ``/health/ready`` endpoint.
    """
    pool = engine.pool
    try:
        async with engine.connect() as conn:
            await conn.execute(text("SELECT 1"))
        return {
            "status": "healthy",
            "pool_size": pool.size(),
            "checked_in": pool.checkedin(),
            "checked_out": pool.checkedout(),
            "overflow": pool.overflow(),
        }
    except SQLAlchemyError as exc:
        return {
            "status": "unhealthy",
            "error": str(exc),
        }


# ---------------------------------------------------------------------------
# Session Provider (used by dependencies.py)
# ---------------------------------------------------------------------------

async def get_async_session() -> AsyncGenerator[AsyncSession, None]:
    """Provide a transactional async database session.

    This generator is consumed by the ``get_db()`` FastAPI dependency.
    It implements the **Unit of Work** pattern:

    - Opens a session (checks out a pooled connection).
    - Yields it to the route handler.
    - **Commits** on success.
    - **Rolls back** on any exception.
    - Always closes the session (returns the connection to the pool).
    """
    async with async_session_maker() as session:
        try:
            yield session
            await session.commit()
        except SQLAlchemyError:
            await session.rollback()
            raise
        except Exception:
            await session.rollback()
            raise
