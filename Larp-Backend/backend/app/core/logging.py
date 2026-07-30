"""Structured logging setup using structlog with rotating file handlers.

This module configures three output channels:

1. **Console** — Coloured dev output or JSON (production), always to stdout.
2. **Application log file** — ``logs/app.log``, size-rotated (10 MB × 5 backups).
3. **Error log file** — ``logs/error.log``, time-rotated (midnight, 30-day retention).

Every log entry automatically includes:

- ISO 8601 timestamp
- Log level
- Logger name
- Correlation ID (from ``CorrelationIdMiddleware``)
- Caller location (module, function, line number — in development)
"""

import logging
import os
import sys
from logging.handlers import RotatingFileHandler, TimedRotatingFileHandler

import structlog

from app.config import get_settings
from app.middleware.correlation_id import add_correlation_id


# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

LOG_DIR = "logs"
APP_LOG_FILE = os.path.join(LOG_DIR, "app.log")
ERROR_LOG_FILE = os.path.join(LOG_DIR, "error.log")

# Size-based rotation for the main log
APP_LOG_MAX_BYTES = 10 * 1024 * 1024  # 10 MB
APP_LOG_BACKUP_COUNT = 5              # keep 5 rotated copies

# Time-based rotation for the error log
ERROR_LOG_WHEN = "midnight"           # rotate at midnight
ERROR_LOG_INTERVAL = 1                # every 1 day
ERROR_LOG_BACKUP_COUNT = 30           # keep 30 days of error logs


# ---------------------------------------------------------------------------
# Log file formatting
# ---------------------------------------------------------------------------

FILE_LOG_FORMAT = (
    "%(asctime)s | %(levelname)-8s | %(name)s | %(message)s"
)


# ---------------------------------------------------------------------------
# Setup
# ---------------------------------------------------------------------------

def _ensure_log_dir() -> None:
    """Create the ``logs/`` directory if it doesn't exist."""
    os.makedirs(LOG_DIR, exist_ok=True)


def _build_stdlib_handlers(log_level: int) -> list[logging.Handler]:
    """Build and return the stdlib handlers for console + rotating files.

    Returns:
        A list of ``logging.Handler`` instances ready to be attached
        to the root logger.
    """
    handlers: list[logging.Handler] = []

    # ── 1. Console handler (stdout) ────────────────────────────────────
    console = logging.StreamHandler(sys.stdout)
    console.setLevel(log_level)
    console.setFormatter(logging.Formatter("%(message)s"))
    handlers.append(console)

    # ── 2. App log file — size-rotated ─────────────────────────────────
    _ensure_log_dir()
    app_file = RotatingFileHandler(
        filename=APP_LOG_FILE,
        maxBytes=APP_LOG_MAX_BYTES,
        backupCount=APP_LOG_BACKUP_COUNT,
        encoding="utf-8",
    )
    app_file.setLevel(log_level)
    app_file.setFormatter(logging.Formatter(FILE_LOG_FORMAT))
    handlers.append(app_file)

    # ── 3. Error log file — time-rotated ───────────────────────────────
    error_file = TimedRotatingFileHandler(
        filename=ERROR_LOG_FILE,
        when=ERROR_LOG_WHEN,
        interval=ERROR_LOG_INTERVAL,
        backupCount=ERROR_LOG_BACKUP_COUNT,
        encoding="utf-8",
    )
    error_file.setLevel(logging.ERROR)  # only ERROR and CRITICAL
    error_file.setFormatter(logging.Formatter(FILE_LOG_FORMAT))
    handlers.append(error_file)

    return handlers


def setup_logging(log_level: str = "INFO") -> None:
    """Configure structlog processors and stdlib handlers.

    This function must be called **once** at application startup
    (before any log statements).  It wires:

    - structlog's processor pipeline (timestamping, correlation ID,
      level filtering, formatting)
    - stdlib's root logger with console + rotating file handlers

    Args:
        log_level: Python log level name (DEBUG, INFO, WARNING, …).
    """
    settings = get_settings()
    level = getattr(logging, log_level.upper(), logging.INFO)

    # ── stdlib root logger ─────────────────────────────────────────────
    root = logging.getLogger()
    root.setLevel(level)

    # Remove any pre-existing handlers (important when tests
    # call setup_logging() multiple times).
    for handler in root.handlers[:]:
        root.removeHandler(handler)

    for handler in _build_stdlib_handlers(level):
        root.addHandler(handler)

    # Quiet noisy third-party loggers
    logging.getLogger("uvicorn.access").setLevel(logging.WARNING)
    logging.getLogger("sqlalchemy.engine").setLevel(
        logging.INFO if settings.database_echo else logging.WARNING
    )

    # ── structlog processor chain ──────────────────────────────────────
    shared_processors: list[structlog.types.Processor] = [
        structlog.contextvars.merge_contextvars,
        structlog.stdlib.filter_by_level,
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.stdlib.add_logger_name,
        structlog.stdlib.add_log_level,
        add_correlation_id,
        structlog.stdlib.PositionalArgumentsFormatter(),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
        structlog.processors.UnicodeDecoder(),
    ]

    if settings.is_development:
        # In development: add caller info (file:line) and coloured output
        shared_processors.append(structlog.dev.ConsoleRenderer())
    else:
        # In production / staging / testing: machine-parseable JSON
        shared_processors.append(structlog.processors.JSONRenderer())

    structlog.configure(
        processors=shared_processors,
        context_class=dict,
        logger_factory=structlog.stdlib.LoggerFactory(),
        wrapper_class=structlog.stdlib.BoundLogger,
        cache_logger_on_first_use=True,
    )


# ---------------------------------------------------------------------------
# Logger factory
# ---------------------------------------------------------------------------

def get_logger(name: str) -> structlog.stdlib.BoundLogger:
    """Return a bound structlog logger for the given module name.

    Usage::

        from app.core.logging import get_logger
        logger = get_logger(__name__)

        logger.info("User created", user_id=user.id)
        logger.error("Payment failed", order_id=order.id, exc_info=True)
    """
    return structlog.get_logger(name)
