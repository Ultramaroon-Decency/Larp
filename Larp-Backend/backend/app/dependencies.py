"""FastAPI dependency injection module.

Provides injectable dependencies for route handlers via ``Depends()``.
Each dependency is a thin factory that wires infrastructure (DB session,
Redis, settings, auth, repositories) into endpoint functions.

Dependency Graph::

    get_settings_dependency ──→ Settings

    get_db ──→ AsyncSession (from connection pool)
      │
      ├──→ get_user_repository                 ──→ UserRepository(session)
      ├──→ get_research_job_repository          ──→ ResearchJobRepository(session)
      ├──→ get_research_report_repository       ──→ ResearchReportRepository(session)
      ├──→ get_research_source_repository       ──→ ResearchSourceRepository(session)
      ├──→ get_research_history_repository      ──→ ResearchHistoryRepository(session)
      ├──→ get_payment_repository               ──→ PaymentRepository(session)
      └──→ get_agent_execution_log_repository   ──→ AgentExecutionLogRepository(session)

    get_redis_client ──→ Redis

    get_current_user ──→ dict (from AuthenticationMiddleware)
"""

from typing import AsyncGenerator

from fastapi import Depends, HTTPException, Request, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.ext.asyncio import AsyncSession
from redis.asyncio import Redis

from app.config import Settings, get_settings
from app.database import get_async_session
from app.redis import get_redis

from app.repositories.user_repository import UserRepository
from app.repositories.research_job_repository import ResearchJobRepository
from app.repositories.research_report_repository import ResearchReportRepository
from app.repositories.research_source_repository import ResearchSourceRepository
from app.repositories.research_history_repository import ResearchHistoryRepository
from app.repositories.payment_repository import PaymentRepository
from app.repositories.agent_execution_log_repository import AgentExecutionLogRepository
from app.services.auth_service import AuthService
from app.services.user_service import UserService
from app.services.research_service import ResearchService
from app.services.agent_service import AgentService
from app.services.agent_manager import AgentManager
from app.services.report_service import ReportService
from app.services.payment_service import PaymentService

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="api/v1/auth/login")


# ---------------------------------------------------------------------------
# Infrastructure Dependencies
# ---------------------------------------------------------------------------

def get_settings_dependency() -> Settings:
    """Dependency to get application settings."""
    return get_settings()


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """Dependency to get a transactional async database session."""
    async for session in get_async_session():
        yield session


async def get_redis_client() -> Redis:
    """Dependency to get a Redis client."""
    return await get_redis()


# ---------------------------------------------------------------------------
# Repository Dependencies (Session-scoped via Depends)
# ---------------------------------------------------------------------------

async def get_user_repository(
    session: AsyncSession = Depends(get_db),
) -> UserRepository:
    """Inject a ``UserRepository`` bound to the current DB session."""
    return UserRepository(session)


async def get_research_job_repository(
    session: AsyncSession = Depends(get_db),
) -> ResearchJobRepository:
    """Inject a ``ResearchJobRepository`` bound to the current DB session."""
    return ResearchJobRepository(session)


async def get_research_report_repository(
    session: AsyncSession = Depends(get_db),
) -> ResearchReportRepository:
    """Inject a ``ResearchReportRepository`` bound to the current DB session."""
    return ResearchReportRepository(session)


async def get_research_source_repository(
    session: AsyncSession = Depends(get_db),
) -> ResearchSourceRepository:
    """Inject a ``ResearchSourceRepository`` bound to the current DB session."""
    return ResearchSourceRepository(session)


async def get_research_history_repository(
    session: AsyncSession = Depends(get_db),
) -> ResearchHistoryRepository:
    """Inject a ``ResearchHistoryRepository`` bound to the current DB session."""
    return ResearchHistoryRepository(session)


async def get_payment_repository(
    session: AsyncSession = Depends(get_db),
) -> PaymentRepository:
    """Inject a ``PaymentRepository`` bound to the current DB session."""
    return PaymentRepository(session)


async def get_agent_execution_log_repository(
    session: AsyncSession = Depends(get_db),
) -> AgentExecutionLogRepository:
    """Inject an ``AgentExecutionLogRepository`` bound to the current DB session."""
    return AgentExecutionLogRepository(session)


# Legacy alias dependencies
get_research_repository = get_research_job_repository
get_agent_repository = get_agent_execution_log_repository


# ---------------------------------------------------------------------------
# Service Dependencies
# ---------------------------------------------------------------------------

async def get_auth_service(
    user_repo: UserRepository = Depends(get_user_repository),
    redis: Redis = Depends(get_redis_client),
    settings: Settings = Depends(get_settings_dependency),
) -> AuthService:
    """Inject an ``AuthService`` instance."""
    return AuthService(user_repo=user_repo, redis=redis, settings=settings)


async def get_user_service(
    user_repo: UserRepository = Depends(get_user_repository),
) -> UserService:
    """Inject a ``UserService`` instance."""
    return UserService(user_repo)


async def get_research_service(
    job_repo: ResearchJobRepository = Depends(get_research_job_repository),
    report_repo: ResearchReportRepository = Depends(get_research_report_repository),
    source_repo: ResearchSourceRepository = Depends(get_research_source_repository),
    history_repo: ResearchHistoryRepository = Depends(get_research_history_repository),
) -> ResearchService:
    """Inject a ``ResearchService`` instance."""
    return ResearchService(job_repo, report_repo, source_repo, history_repo)


async def get_agent_service(
    agent_log_repo: AgentExecutionLogRepository = Depends(get_agent_execution_log_repository),
) -> AgentService:
    """Inject an ``AgentService`` instance."""
    return AgentService(agent_log_repo)


async def get_agent_manager(
    job_repo: ResearchJobRepository = Depends(get_research_job_repository),
    report_repo: ResearchReportRepository = Depends(get_research_report_repository),
    source_repo: ResearchSourceRepository = Depends(get_research_source_repository),
    agent_log_repo: AgentExecutionLogRepository = Depends(get_agent_execution_log_repository),
) -> AgentManager:
    """Inject an ``AgentManager`` instance."""
    return AgentManager(job_repo, report_repo, source_repo, agent_log_repo)


async def get_report_service(
    report_repo: ResearchReportRepository = Depends(get_research_report_repository),
    source_repo: ResearchSourceRepository = Depends(get_research_source_repository),
) -> ReportService:
    """Inject a ``ReportService`` instance."""
    return ReportService(report_repo, source_repo)


async def get_payment_service(
    payment_repo: PaymentRepository = Depends(get_payment_repository),
) -> PaymentService:
    """Inject a ``PaymentService`` instance."""
    return PaymentService(payment_repo)


# ---------------------------------------------------------------------------
# Auth Dependency
# ---------------------------------------------------------------------------

async def get_current_user(
    request: Request,
    token: str = Depends(oauth2_scheme),
) -> dict:
    """Return the authenticated user from ``request.state``.

    Includes ``OAuth2PasswordBearer`` dependency to display the Authorize
    lock button in Swagger UI (/docs).
    """
    user = getattr(request.state, "user", None)
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return user


async def get_current_active_user(
    current_user: dict = Depends(get_current_user),
    user_repo: UserRepository = Depends(get_user_repository),
):
    """Dependency verifying that the authenticated user exists and is active."""
    from uuid import UUID
    from app.core.exceptions import AuthenticationError

    user_id = UUID(current_user["id"])
    user = await user_repo.get_by_id(user_id)
    if user is None or not user.is_active:
        raise AuthenticationError(
            message="User account is deactivated or missing",
            error_code="USER_INACTIVE",
        )
    return user


async def get_current_admin_user(
    user=Depends(get_current_active_user),
):
    """Dependency enforcing that the authenticated user has Admin role or Superuser privileges."""
    from app.core.exceptions import AuthorizationError

    if not getattr(user, "is_admin", False):
        raise AuthorizationError(
            message="Admin role required for this operation",
            error_code="FORBIDDEN_REQUIRES_ADMIN",
        )
    return user


async def get_current_superuser(
    user=Depends(get_current_active_user),
):
    """Dependency enforcing that the authenticated user has Superuser privileges."""
    from app.core.exceptions import AuthorizationError

    if not getattr(user, "is_superuser", False):
        raise AuthorizationError(
            message="Superuser privileges required for this operation",
            error_code="FORBIDDEN_REQUIRES_SUPERUSER",
        )
    return user


def require_roles(*allowed_roles: str):
    """Factory creating a dependency that enforces any of the specified RBAC roles."""
    async def role_checker(user=Depends(get_current_active_user)):
        from app.core.exceptions import AuthorizationError

        user_role = getattr(user, "role", "user")
        if user_role not in allowed_roles and not getattr(user, "is_superuser", False):
            raise AuthorizationError(
                message=f"Access denied. Requires one of roles: {list(allowed_roles)}",
                error_code="FORBIDDEN_ROLE_MISMATCH",
            )
        return user

    return role_checker
