"""Comprehensive unit and integration tests for Google Sign-In authentication."""

from datetime import datetime, timezone
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

from app.config import get_settings
from app.core.exceptions import AuthenticationError, ConflictError
from app.models.user import User
from app.models.research_job import ResearchJob
from app.models.payment import Payment
from app.repositories.user_repository import UserRepository
from app.services.auth_service import AuthService
from app.core.security import create_access_token


@pytest.fixture
def mock_redis():
    redis = AsyncMock()
    return redis


@pytest.fixture
def auth_service(db_session, mock_redis):
    user_repo = UserRepository(db_session)
    settings = get_settings()
    return AuthService(user_repo=user_repo, redis=mock_redis, settings=settings)


@pytest.mark.asyncio
@patch("google.oauth2.id_token.verify_oauth2_token")

async def test_google_login_first_time_user_success(mock_verify, auth_service, db_session, mock_redis):
    """First-time Google login creates user, stores google_sub, and issues JWT tokens."""
    mock_verify.return_value = {
        "iss": "https://accounts.google.com",
        "sub": "google-sub-12345",
        "email": "newuser@example.com",
        "name": "New Google User",
        "picture": "https://example.com/avatar.jpg",
    }

    tokens = await auth_service.google_login("valid-google-credential-token")

    assert tokens.access_token is not None
    assert tokens.refresh_token is not None
    assert tokens.token_type == "bearer"
    assert tokens.expires_in > 0

    # Verify user saved in DB
    user_repo = UserRepository(db_session)
    user = await user_repo.get_by_google_sub("google-sub-12345")
    assert user is not None
    assert user.email == "newuser@example.com"
    assert user.full_name == "New Google User"
    assert user.name == "New Google User"
    assert user.avatar_url == "https://example.com/avatar.jpg"
    assert user.is_active is True
    assert user.hashed_password is None
    assert user.last_login_at is not None
    mock_redis.setex.assert_called_once()


@pytest.mark.asyncio
@patch("google.oauth2.id_token.verify_oauth2_token")

async def test_google_login_returning_user_success(mock_verify, auth_service, db_session):
    """Returning Google login reuses existing user and updates last_login_at."""
    user_repo = UserRepository(db_session)
    existing_user = await user_repo.create({
        "email": "returning@example.com",
        "google_sub": "google-sub-67890",
        "full_name": "Old Name",
        "avatar_url": "https://example.com/old.jpg",
        "is_active": True,
    })

    mock_verify.return_value = {
        "iss": "https://accounts.google.com",
        "sub": "google-sub-67890",
        "email": "returning@example.com",
        "name": "Updated Name",
        "picture": "https://example.com/new.jpg",
    }

    tokens = await auth_service.google_login("valid-google-credential-token")
    assert tokens.access_token is not None

    updated_user = await user_repo.get_by_google_sub("google-sub-67890")
    assert updated_user.id == existing_user.id
    assert updated_user.full_name == "Updated Name"
    assert updated_user.avatar_url == "https://example.com/new.jpg"
    assert updated_user.last_login_at is not None


@pytest.mark.asyncio
@patch("google.oauth2.id_token.verify_oauth2_token")

async def test_google_login_invalid_token_raises_401(mock_verify, auth_service):
    """Invalid Google ID token raises AuthenticationError 401."""
    mock_verify.side_effect = ValueError("Token expired or invalid signature")

    with pytest.raises(AuthenticationError) as exc_info:
        await auth_service.google_login("invalid-token")

    assert exc_info.value.status_code == 401
    assert exc_info.value.error_code == "AUTH_GOOGLE_TOKEN_INVALID"


@pytest.mark.asyncio
@patch("google.oauth2.id_token.verify_oauth2_token")

async def test_google_login_wrong_issuer_raises_401(mock_verify, auth_service):
    """Token with untrusted issuer is rejected."""
    mock_verify.return_value = {
        "iss": "https://fake-google-issuer.com",
        "sub": "google-sub-fake",
        "email": "hacker@example.com",
    }

    with pytest.raises(AuthenticationError) as exc_info:
        await auth_service.google_login("fake-issuer-token")

    assert exc_info.value.status_code == 401
    assert exc_info.value.error_code == "AUTH_GOOGLE_INVALID_ISSUER"


@pytest.mark.asyncio
@patch("google.oauth2.id_token.verify_oauth2_token")

async def test_google_login_missing_identity_claims_raises_401(mock_verify, auth_service):
    """Token missing sub or email claims is rejected."""
    mock_verify.return_value = {
        "iss": "https://accounts.google.com",
        "sub": "google-sub-only",
        # missing email
    }

    with pytest.raises(AuthenticationError) as exc_info:
        await auth_service.google_login("incomplete-claims-token")

    assert exc_info.value.error_code == "AUTH_GOOGLE_CLAIMS_MISSING"


@pytest.mark.asyncio
@patch("google.oauth2.id_token.verify_oauth2_token")

async def test_google_login_deactivated_user_rejected(mock_verify, auth_service, db_session):
    """Deactivated Google user cannot log in."""
    user_repo = UserRepository(db_session)
    await user_repo.create({
        "email": "deactivated@example.com",
        "google_sub": "google-sub-inactive",
        "is_active": False,
    })

    mock_verify.return_value = {
        "iss": "https://accounts.google.com",
        "sub": "google-sub-inactive",
        "email": "deactivated@example.com",
    }

    with pytest.raises(AuthenticationError) as exc_info:
        await auth_service.google_login("inactive-user-token")

    assert exc_info.value.error_code == "USER_DEACTIVATED"


@pytest.mark.asyncio
@patch("google.oauth2.id_token.verify_oauth2_token")

async def test_google_login_email_collision_requires_account_linking(mock_verify, auth_service, db_session):
    """Email registered via password without google_sub requires account linking."""
    user_repo = UserRepository(db_session)
    await user_repo.create({
        "email": "passworduser@example.com",
        "hashed_password": "somepasswordhash",
        "google_sub": None,
        "is_active": True,
    })

    mock_verify.return_value = {
        "iss": "https://accounts.google.com",
        "sub": "google-sub-new",
        "email": "passworduser@example.com",
    }

    with pytest.raises(ConflictError) as exc_info:
        await auth_service.google_login("colliding-email-token")

    assert exc_info.value.error_code == "AUTH_ACCOUNT_LINKING_REQUIRED"


@pytest.mark.asyncio
@patch("google.oauth2.id_token.verify_oauth2_token")

async def test_google_login_api_endpoint_success(mock_verify, client):
    """POST /api/v1/auth/google endpoint returns 200 and Larp tokens."""
    mock_verify.return_value = {
        "iss": "https://accounts.google.com",
        "sub": "google-sub-api-test",
        "email": "apiuser@example.com",
        "name": "API Google User",
    }

    response = await client.post(
        "/api/v1/auth/google",
        json={"credential": "mocked-valid-google-id-token"}
    )

    assert response.status_code == 200
    json_data = response.json()
    assert json_data["success"] is True
    assert "access_token" in json_data["data"]
    assert "refresh_token" in json_data["data"]


@pytest.mark.asyncio
async def test_auth_me_endpoint(client, db_session):
    """GET /api/v1/auth/me returns profile of authenticated active user."""
    user_repo = UserRepository(db_session)
    user = await user_repo.create({
        "email": "me_test@example.com",
        "full_name": "Me Test User",
        "google_sub": "google-sub-me",
        "is_active": True,
    })

    token = create_access_token(subject=str(user.id))
    headers = {"Authorization": f"Bearer {token}"}

    response = await client.get("/api/v1/auth/me", headers=headers)
    assert response.status_code == 200
    json_data = response.json()
    assert json_data["success"] is True
    assert json_data["data"]["email"] == "me_test@example.com"
    assert json_data["data"]["id"] == str(user.id)


@pytest.mark.asyncio
async def test_auth_me_deactivated_user_blocked(client, db_session):
    """Deactivated user with unexpired JWT is blocked on protected endpoint."""
    user_repo = UserRepository(db_session)
    user = await user_repo.create({
        "email": "blocked@example.com",
        "is_active": False,
    })

    token = create_access_token(subject=str(user.id))
    headers = {"Authorization": f"Bearer {token}"}

    response = await client.get("/api/v1/auth/me", headers=headers)
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_user_research_job_relationship(db_session):
    """Verify ResearchJob can be associated with User."""
    from sqlalchemy import select
    from sqlalchemy.orm import selectinload

    user_repo = UserRepository(db_session)
    user = await user_repo.create({
        "email": "jobuser@example.com",
        "is_active": True,
    })

    job = ResearchJob(
        id=uuid4(),
        user_id=user.id,
        title="Test Quantum Computing",
        query="Quantum Computing Applications",
        status="pending",
        depth="standard",
    )
    db_session.add(job)
    await db_session.commit()

    stmt = select(User).where(User.id == user.id).options(selectinload(User.jobs))
    res = await db_session.execute(stmt)
    saved_user = res.scalar_one()
    assert len(saved_user.jobs) == 1
    assert saved_user.jobs[0].title == "Test Quantum Computing"


@pytest.mark.asyncio
async def test_user_payment_relationship(db_session):
    """Verify Payment can be associated with User."""
    from sqlalchemy import select
    from sqlalchemy.orm import selectinload

    user_repo = UserRepository(db_session)
    user = await user_repo.create({
        "email": "paymentuser@example.com",
        "is_active": True,
    })

    payment = Payment(
        id=uuid4(),
        user_id=user.id,
        amount_cents=1000,
        currency="usd",
        status="succeeded",
        credits_awarded=100,
    )
    db_session.add(payment)
    await db_session.commit()

    stmt = select(User).where(User.id == user.id).options(selectinload(User.payments))
    res = await db_session.execute(stmt)
    saved_user = res.scalar_one()
    assert len(saved_user.payments) == 1
    assert saved_user.payments[0].amount_cents == 1000

