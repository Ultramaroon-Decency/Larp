"""Pytest fixtures for unit and integration testing."""

import asyncio
import uuid
import pytest
from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from app.core.security import create_access_token
from app.database import get_async_session
from app.main import create_app
from app.models.base import Base

import app.database as app_db

TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"

test_engine = create_async_engine(TEST_DATABASE_URL, echo=False)

app_db.engine = test_engine
app_db.async_session_maker = async_sessionmaker(
    bind=test_engine, class_=AsyncSession, expire_on_commit=False, autoflush=False
)

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
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield test_engine
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    await test_engine.dispose()


@pytest.fixture
async def db_session(engine):
    """Yield an AsyncSession for each test."""
    async with app_db.async_session_maker() as session:
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
        await db_session.commit()

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
async def auth_user(db_session):
    """Create and commit an active test user entity in the database."""
    from app.repositories.user_repository import UserRepository
    from app.core.security import hash_password
    user_repo = UserRepository(db_session)
    user = await user_repo.create({
        "email": f"auth_user_{uuid.uuid4()}@example.com",
        "hashed_password": hash_password("password123"),
        "is_active": True,
    })
    await db_session.commit()
    return user


@pytest.fixture
async def auth_headers(auth_user):
    """Return dictionary with Authorization bearer token for an active test user in DB."""
    token = create_access_token(subject=str(auth_user.id))
    return {"Authorization": f"Bearer {token}"}
