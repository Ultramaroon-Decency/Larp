"""Main application module — FastAPI application factory.

Creates and configures the FastAPI instance with the full middleware
stack, exception handlers, and API routers.

Middleware execution order (outermost → innermost):

    Request → CORS → GZip → CorrelationId → RateLimit → Authentication → RequestLogging → Route
    Response ← CORS ← GZip ← CorrelationId ← RateLimit ← Authentication ← RequestLogging ← Route

Starlette applies ``add_middleware()`` in **LIFO** order, so the
*last* call becomes the *outermost* wrapper.
"""

from contextlib import asynccontextmanager
from typing import AsyncGenerator

from fastapi import FastAPI
from starlette.middleware.gzip import GZipMiddleware

from app.config import get_settings
from app.database import close_db, init_db
from app.redis import close_redis, init_redis
from app.api.v1.router import api_router
from app.core.logging import setup_logging, get_logger
from app.middleware.cors import setup_cors
from app.middleware.correlation_id import CorrelationIdMiddleware
from app.middleware.authentication import AuthenticationMiddleware
from app.middleware.rate_limiter import RateLimitMiddleware
from app.middleware.request_logging import RequestLoggingMiddleware
from app.middleware.error_handler import setup_error_handlers

settings = get_settings()
logger = get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Manage application startup and shutdown lifecycle events."""
    logger.info("Starting up application", version=settings.app_version)
    await init_db()
    await init_redis()

    yield

    logger.info("Shutting down application")
    await close_db()
    await close_redis()


def create_app() -> FastAPI:
    """Create and configure the FastAPI application instance.

    This factory wires up:
    - Structured logging (structlog)
    - CORS middleware
    - GZip compression middleware
    - Correlation ID (X-Request-ID) middleware
    - Redis-backed rate limiting middleware
    - JWT authentication middleware
    - Request/response logging middleware
    - Global exception handlers
    - API v1 router under ``/api/v1``
    """
    # Initialise structured logging before anything else
    setup_logging(log_level=settings.log_level)

    app = FastAPI(
        title=settings.app_name,
        version=settings.app_version,
        description="Backend API for the AI-Powered Multi-Step Research Agent",
        docs_url="/docs",
        redoc_url="/redoc",
        openapi_url="/api/v1/openapi.json",
        lifespan=lifespan,
    )

    # ── Middleware stack ────────────────────────────────────────────────
    # Starlette applies add_middleware() in LIFO order.
    # We add them bottom-up so the FIRST call is the INNERMOST layer:
    #
    #   Outermost → CORS → GZip → CorrelationId → RateLimit
    #            → Authentication → RequestLogging → Route (innermost)

    # 1. RequestLogging (innermost — logs after auth, has correlation ID)
    app.add_middleware(RequestLoggingMiddleware)

    # 2. Payment Middleware (runs after authentication, verifies pre-execution budget)
    from app.middleware.payment import PaymentMiddleware
    app.add_middleware(PaymentMiddleware)

    # 3. Authentication (runs after correlation ID is set)
    app.add_middleware(AuthenticationMiddleware)

    # 3. Rate Limiter (runs after correlation ID, before auth)
    app.add_middleware(
        RateLimitMiddleware,
        max_requests=settings.rate_limit_requests,
        window_seconds=settings.rate_limit_window_seconds,
    )

    # 4. Correlation ID (must be early — everything after needs it)
    app.add_middleware(CorrelationIdMiddleware)

    # 5. GZip Compression (compresses response bodies)
    app.add_middleware(GZipMiddleware, minimum_size=settings.gzip_minimum_size)

    # 6. CORS (outermost — must handle preflight before anything else)
    setup_cors(app)

    # ── Exception handlers ─────────────────────────────────────────────
    setup_error_handlers(app)

    # ── Routers ────────────────────────────────────────────────────────
    app.include_router(api_router, prefix="/api/v1")

    # Frontend compatibility routes
    from app.api.v1.endpoints.export import router as export_router
    from app.api.v1.endpoints.payments import router as payments_router
    app.include_router(export_router, prefix="/api/export", tags=["Frontend Compatibility Export"])
    app.include_router(payments_router, prefix="/api/payments", tags=["Frontend Compatibility Payments"])

    return app



app = create_app()
