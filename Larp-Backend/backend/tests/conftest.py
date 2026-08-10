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


class FakeRedis:
    """In-memory Redis fake for testing."""

    def __init__(self):
        self.store = {}

    async def setex(self, name: str, time: int, value: str):
        self.store[name] = value

    async def get(self, name: str):
        return self.store.get(name)

    async def delete(self, *names: str):
        count = 0
        for name in names:
            if name in self.store:
                del self.store[name]
                count += 1
        return count


@pytest.fixture
def mock_redis():
    """Yield a fresh FakeRedis instance."""
    return FakeRedis()


@pytest.fixture
async def client(db_session, mock_redis):
    """Yield httpx AsyncClient with FastAPI test app."""
    async def override_get_db():
        yield db_session

    async def override_get_redis():
        return mock_redis

    from app.dependencies import get_db, get_redis_client
    app.dependency_overrides[get_async_session] = override_get_db
    app.dependency_overrides[get_db] = override_get_db
    app.dependency_overrides[get_redis_client] = override_get_redis

    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as c:
        yield c

    app.dependency_overrides.clear()


@pytest.fixture
def auth_headers():
    """Return dictionary with Authorization bearer token for a test user."""
    test_user_id = str(uuid.uuid4())
    token = create_access_token(subject=test_user_id)
    return {"Authorization": f"Bearer {token}"}
