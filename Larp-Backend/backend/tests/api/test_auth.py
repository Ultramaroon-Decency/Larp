"""Tests for AuthService and authentication endpoints."""

import pytest
from httpx import AsyncClient

from app.config import get_settings
from app.core.exceptions import AuthenticationError, ConflictError
from app.core.security import create_access_token, hash_password
from app.repositories.user_repository import UserRepository
from app.schemas.auth import LoginRequest, RegisterRequest
from app.services.auth_service import AuthService

settings = get_settings()


@pytest.mark.asyncio
async def test_auth_service_register_success(db_session, mock_redis):
    """Test successful user registration using AuthService directly."""
    user_repo = UserRepository(db_session)
    auth_service = AuthService(user_repo=user_repo, settings=settings, redis=mock_redis)

    req = RegisterRequest(
        email="service_register@example.com",
        password="securepassword123",
        full_name="Service Register",
    )
    user_resp = await auth_service.register(req)

    assert user_resp.email == "service_register@example.com"
    assert user_resp.full_name == "Service Register"
    assert user_resp.is_active is True
    assert await user_repo.email_exists("service_register@example.com") is True


@pytest.mark.asyncio
async def test_auth_service_register_duplicate(db_session, mock_redis):
    """Test duplicate registration raises ConflictError in AuthService."""
    user_repo = UserRepository(db_session)
    auth_service = AuthService(user_repo=user_repo, settings=settings, redis=mock_redis)

    req = RegisterRequest(
        email="dup_service@example.com",
        password="securepassword123",
    )
    await auth_service.register(req)

    with pytest.raises(ConflictError) as exc_info:
        await auth_service.register(req)
    assert exc_info.value.status_code == 409


@pytest.mark.asyncio
async def test_auth_service_login_success(db_session, mock_redis):
    """Test successful login returns access & refresh tokens via AuthService."""
    user_repo = UserRepository(db_session)
    auth_service = AuthService(user_repo=user_repo, settings=settings, redis=mock_redis)

    # Register user first
    await auth_service.register(
        RegisterRequest(email="login_service@example.com", password="password123")
    )

    login_req = LoginRequest(email="login_service@example.com", password="password123")
    token_resp = await auth_service.login(login_req)

    assert token_resp.access_token is not None
    assert token_resp.refresh_token is not None
    assert token_resp.token_type == "bearer"
    assert token_resp.expires_in == settings.access_token_expire_minutes * 60


@pytest.mark.asyncio
async def test_auth_service_login_invalid_password(db_session, mock_redis):
    """Test login with incorrect password raises AuthenticationError."""
    user_repo = UserRepository(db_session)
    auth_service = AuthService(user_repo=user_repo, settings=settings, redis=mock_redis)

    await auth_service.register(
        RegisterRequest(email="wrong_pass@example.com", password="password123")
    )

    login_req = LoginRequest(email="wrong_pass@example.com", password="wrongpassword")
    with pytest.raises(AuthenticationError) as exc_info:
        await auth_service.login(login_req)
    assert exc_info.value.error_code == "AUTH_INVALID_CREDENTIALS"


@pytest.mark.asyncio
async def test_auth_service_login_unknown_user(db_session, mock_redis):
    """Test login with non-existent email raises AuthenticationError."""
    user_repo = UserRepository(db_session)
    auth_service = AuthService(user_repo=user_repo, settings=settings, redis=mock_redis)

    login_req = LoginRequest(email="nonexistent@example.com", password="password123")
    with pytest.raises(AuthenticationError) as exc_info:
        await auth_service.login(login_req)
    assert exc_info.value.error_code == "AUTH_INVALID_CREDENTIALS"


@pytest.mark.asyncio
async def test_auth_service_login_deactivated_user(db_session, mock_redis):
    """Test login for deactivated account raises USER_DEACTIVATED."""
    user_repo = UserRepository(db_session)
    auth_service = AuthService(user_repo=user_repo, settings=settings, redis=mock_redis)

    await user_repo.create({
        "email": "deactivated@example.com",
        "hashed_password": hash_password("password123"),
        "is_active": False,
    })

    login_req = LoginRequest(email="deactivated@example.com", password="password123")
    with pytest.raises(AuthenticationError) as exc_info:
        await auth_service.login(login_req)
    assert exc_info.value.error_code == "USER_DEACTIVATED"


@pytest.mark.asyncio
async def test_auth_service_refresh_token_success(db_session, mock_redis):
    """Test token refresh and rotation via AuthService."""
    user_repo = UserRepository(db_session)
    auth_service = AuthService(user_repo=user_repo, settings=settings, redis=mock_redis)

    await auth_service.register(
        RegisterRequest(email="refresh_service@example.com", password="password123")
    )
    tokens = await auth_service.login(
        LoginRequest(email="refresh_service@example.com", password="password123")
    )

    new_tokens = await auth_service.refresh_token(tokens.refresh_token)
    assert new_tokens.access_token is not None
    assert new_tokens.refresh_token is not None
    assert new_tokens.refresh_token != tokens.refresh_token

    # Verify old refresh token is revoked
    with pytest.raises(AuthenticationError) as exc_info:
        await auth_service.refresh_token(tokens.refresh_token)
    assert exc_info.value.error_code == "AUTH_REFRESH_TOKEN_REVOKED"


@pytest.mark.asyncio
async def test_auth_service_refresh_token_invalid(db_session, mock_redis):
    """Test refreshing with malformed/access token raises AuthenticationError."""
    user_repo = UserRepository(db_session)
    auth_service = AuthService(user_repo=user_repo, settings=settings, redis=mock_redis)

    access_token = create_access_token("some-id")
    with pytest.raises(AuthenticationError) as exc_info:
        await auth_service.refresh_token(access_token)
    assert exc_info.value.error_code == "AUTH_TOKEN_INVALID_TYPE"


# API Endpoint Integration Tests


@pytest.mark.asyncio
async def test_api_register_endpoint_uses_auth_service(client: AsyncClient):
    """Test /api/v1/auth/register endpoint via HTTP client."""
    payload = {
        "email": "api_register@example.com",
        "password": "securepassword123",
        "full_name": "API Register User",
    }
    response = await client.post("/api/v1/auth/register", json=payload)
    assert response.status_code == 201
    data = response.json()
    assert data["success"] is True
    assert data["data"]["email"] == "api_register@example.com"


@pytest.mark.asyncio
async def test_api_login_endpoint_uses_auth_service(client: AsyncClient):
    """Test /api/v1/auth/login endpoint via HTTP client."""
    # Register user first
    await client.post(
        "/api/v1/auth/register",
        json={"email": "api_login@example.com", "password": "password123"},
    )

    response = await client.post(
        "/api/v1/auth/login",
        json={"email": "api_login@example.com", "password": "password123"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert "access_token" in data["data"]
    assert "refresh_token" in data["data"]


@pytest.mark.asyncio
async def test_api_refresh_endpoint_uses_auth_service(client: AsyncClient):
    """Test /api/v1/auth/refresh endpoint via HTTP client."""
    await client.post(
        "/api/v1/auth/register",
        json={"email": "api_refresh@example.com", "password": "password123"},
    )
    login_resp = await client.post(
        "/api/v1/auth/login",
        json={"email": "api_refresh@example.com", "password": "password123"},
    )
    data = login_resp.json()["data"]
    access_token = data["access_token"]
    refresh_token = data["refresh_token"]

    response = await client.post(
        "/api/v1/auth/refresh",
        json={"refresh_token": refresh_token},
        headers={"Authorization": f"Bearer {access_token}"},
    )
    assert response.status_code == 200
    res_data = response.json()
    assert res_data["success"] is True
    assert "access_token" in res_data["data"]


@pytest.mark.asyncio
async def test_api_logout_endpoint_uses_auth_service(client: AsyncClient):
    """Test /api/v1/auth/logout endpoint via HTTP client."""
    await client.post(
        "/api/v1/auth/register",
        json={"email": "api_logout@example.com", "password": "password123"},
    )
    login_resp = await client.post(
        "/api/v1/auth/login",
        json={"email": "api_logout@example.com", "password": "password123"},
    )
    data = login_resp.json()["data"]
    access_token = data["access_token"]
    refresh_token = data["refresh_token"]

    response = await client.post(
        "/api/v1/auth/logout",
        json={"refresh_token": refresh_token},
        headers={"Authorization": f"Bearer {access_token}"},
    )
    assert response.status_code == 200
    assert response.json()["success"] is True

    # Refresh should fail now that token was revoked on logout
    ref_resp = await client.post(
        "/api/v1/auth/refresh",
        json={"refresh_token": refresh_token},
        headers={"Authorization": f"Bearer {access_token}"},
    )
    assert ref_resp.status_code == 401


# Middleware Database Verification Tests


@pytest.mark.asyncio
async def test_middleware_valid_jwt_nonexistent_user(client: AsyncClient):
    """Test valid JWT for deleted/nonexistent user is rejected with 401."""
    import uuid
    fake_user_id = str(uuid.uuid4())
    token = create_access_token(subject=fake_user_id)

    response = await client.get(
        "/api/v1/users/me",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 401
    assert response.json()["message"] == "User no longer exists"


@pytest.mark.asyncio
async def test_middleware_valid_jwt_deactivated_user(client: AsyncClient, db_session):
    """Test valid JWT for deactivated user is rejected with 403."""
    user_repo = UserRepository(db_session)
    user = await user_repo.create({
        "email": "middleware_deactive@example.com",
        "hashed_password": hash_password("password123"),
        "is_active": False,
    })
    await db_session.commit()

    token = create_access_token(subject=str(user.id))

    response = await client.get(
        "/api/v1/users/me",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 403
    assert response.json()["message"] == "User account is deactivated"


@pytest.mark.asyncio
async def test_middleware_user_deactivation_regression(client: AsyncClient, db_session):
    """Regression test: User gets JWT -> user is deactivated -> JWT is rejected on protected route."""
    # 1. Register and login to get JWT
    await client.post(
        "/api/v1/auth/register",
        json={"email": "deact_regression@example.com", "password": "password123"},
    )
    login_resp = await client.post(
        "/api/v1/auth/login",
        json={"email": "deact_regression@example.com", "password": "password123"},
    )
    access_token = login_resp.json()["data"]["access_token"]

    # 2. Access protected endpoint -> succeeds
    me_resp1 = await client.get(
        "/api/v1/users/me",
        headers={"Authorization": f"Bearer {access_token}"},
    )
    assert me_resp1.status_code == 200

    # 3. Deactivate user in database
    user_repo = UserRepository(db_session)
    user = await user_repo.get_by_email("deact_regression@example.com")
    await user_repo.update(user.id, {"is_active": False})
    await db_session.commit()

    # 4. Access protected endpoint with SAME JWT -> now rejected with 403
    me_resp2 = await client.get(
        "/api/v1/users/me",
        headers={"Authorization": f"Bearer {access_token}"},
    )
    assert me_resp2.status_code == 403
    assert me_resp2.json()["message"] == "User account is deactivated"


@pytest.mark.asyncio
async def test_middleware_user_deletion_regression(client: AsyncClient, db_session):
    """Regression test: User gets JWT -> user is deleted -> JWT is rejected on protected route."""
    await client.post(
        "/api/v1/auth/register",
        json={"email": "del_regression@example.com", "password": "password123"},
    )
    login_resp = await client.post(
        "/api/v1/auth/login",
        json={"email": "del_regression@example.com", "password": "password123"},
    )
    access_token = login_resp.json()["data"]["access_token"]

    # Delete user from DB
    user_repo = UserRepository(db_session)
    user = await user_repo.get_by_email("del_regression@example.com")
    await user_repo.delete(user.id)
    await db_session.commit()

    # Protected endpoint call with old JWT -> rejected with 401
    me_resp = await client.get(
        "/api/v1/users/me",
        headers={"Authorization": f"Bearer {access_token}"},
    )
    assert me_resp.status_code == 401
    assert me_resp.json()["message"] == "User no longer exists"
