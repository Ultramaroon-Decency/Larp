"""Pytest fixtures for unit and integration testing."""

import asyncio
import uuid
import pytest
from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

from app.core.security import create_access_token
from app.database import get_async_session
from app.main import create_app
from app.models.base import Base

TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"

app = create_app()


@pytest.fixture(scope="session")
def event_loop():
    """Create session-wide event loop for async tests."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()






@pytest.fixture(scope="session")
async def engine():
    """Create async SQLite engine and initialize tables."""
    test_engine = create_async_engine(TEST_DATABASE_URL, echo=False)
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield test_engine
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    await test_engine.dispose()


@pytest.fixture
async def db_session(engine):
    """Yield an AsyncSession for each test."""
    async_session = sessionmaker(
        engine, class_=AsyncSession, expire_on_commit=False
    )
    async with async_session() as session:
        yield session


@pytest.fixture
async def client(db_session):
    """Yield httpx AsyncClient with FastAPI test app."""
    from unittest.mock import AsyncMock
    from app.dependencies import get_db, get_redis_client

    async def override_get_db():
        yield db_session

    mock_redis = AsyncMock()
    app.dependency_overrides[get_async_session] = override_get_db
    app.dependency_overrides[get_db] = override_get_db
    app.dependency_overrides[get_redis_client] = lambda: mock_redis

    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as c:
        yield c

    app.dependency_overrides.clear()


@pytest.fixture
async def auth_headers(db_session):
    """Return dictionary with Authorization bearer token for an active test user."""
    from app.repositories.user_repository import UserRepository
    user_repo = UserRepository(db_session)
    user = await user_repo.create({
        "email": f"test_{uuid.uuid4()}@example.com",
        "is_active": True,
    })
    token = create_access_token(subject=str(user.id))
    return {"Authorization": f"Bearer {token}"}

