"""Alembic environment configuration for async PostgreSQL migrations.

This file controls how Alembic connects to the database and discovers
model metadata for auto-generating migrations.

Key features:

- **Async engine** — uses ``async_engine_from_config`` with asyncpg.
- **NullPool** — migrations use short-lived connections, no pooling needed.
- **URL from settings** — database URL comes from ``get_settings()``,
  never hardcoded in ``alembic.ini``.
- **compare_type=True** — detects column type changes (e.g. String(100)
  → String(255)) during ``--autogenerate``.
- **compare_server_default=True** — detects server_default changes.
- **Offline mode** — supports ``alembic upgrade head --sql`` to emit
  raw SQL without connecting.
"""

import asyncio
from logging.config import fileConfig

from sqlalchemy import pool
from sqlalchemy.engine import Connection
from sqlalchemy.ext.asyncio import async_engine_from_config

from alembic import context

# ── Import ALL models so their tables register with Base.metadata ──────
# This is critical: Alembic can only auto-detect tables that are
# imported before target_metadata is read.
from app.models import Base  # noqa: F401 — side-effect import
from app.config import get_settings

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

config = context.config

# Set up Python logging from alembic.ini
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# The MetaData object that Alembic compares against the live database
# to determine what migrations to generate.
target_metadata = Base.metadata

settings = get_settings()


def get_url() -> str:
    """Return the database URL from application settings.

    This keeps credentials out of ``alembic.ini`` — they come from
    ``.env`` via Pydantic settings.
    """
    return settings.database_url


# ---------------------------------------------------------------------------
# Offline mode (--sql)
# ---------------------------------------------------------------------------

def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode.

    Generates SQL statements to stdout without connecting to the
    database.  Useful for:

    - Reviewing SQL before applying (``alembic upgrade head --sql``).
    - Generating migration scripts for DBA review.
    - Environments where direct DB access is restricted.
    """
    url = get_url()
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        compare_type=True,
        compare_server_default=True,
    )

    with context.begin_transaction():
        context.run_migrations()


# ---------------------------------------------------------------------------
# Online mode (default)
# ---------------------------------------------------------------------------

def do_run_migrations(connection: Connection) -> None:
    """Configure the migration context and run migrations.

    ``compare_type=True`` means ``--autogenerate`` will detect type
    changes (e.g. ``String(100)`` → ``String(255)``).
    """
    context.configure(
        connection=connection,
        target_metadata=target_metadata,
        compare_type=True,
        compare_server_default=True,
    )

    with context.begin_transaction():
        context.run_migrations()


async def run_async_migrations() -> None:
    """Create an async engine, connect, and run migrations.

    Uses ``NullPool`` because migrations are short-lived — there's
    no need for connection pooling here.
    """
    configuration = config.get_section(config.config_ini_section, {})
    configuration["sqlalchemy.url"] = get_url()

    connectable = async_engine_from_config(
        configuration,
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    async with connectable.connect() as connection:
        await connection.run_sync(do_run_migrations)

    await connectable.dispose()


def run_migrations_online() -> None:
    """Run migrations in 'online' mode (connects to the live database)."""
    asyncio.run(run_async_migrations())


# ---------------------------------------------------------------------------
# Entry point — Alembic calls this when executing commands
# ---------------------------------------------------------------------------

if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
