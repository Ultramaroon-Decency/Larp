"""Unit tests for AuthService."""

from datetime import datetime, timezone
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

from app.config import get_settings
from app.core.exceptions import AuthenticationError, ConflictError
from app.repositories.user_repository import UserRepository
from app.schemas.auth import LoginRequest, RegisterRequest
from app.services.auth_service import AuthService


@pytest.fixture
def mock_user_repo():
    repo = AsyncMock(spec=UserRepository)
    return repo


@pytest.fixture
def mock_redis():
    redis = AsyncMock()
    return redis


@pytest.fixture
def auth_service(mock_user_repo, mock_redis):
    settings = get_settings()
    return AuthService(user_repo=mock_user_repo, redis=mock_redis, settings=settings)


@pytest.mark.asyncio
@patch("app.services.auth_service.hash_password", return_value="hashed_secret_pw")
async def test_register_success(mock_hash, auth_service, mock_user_repo):
    mock_user_repo.email_exists.return_value = False
    mock_user = MagicMock()
    mock_user.id = uuid4()
    mock_user.email = "test@example.com"
    mock_user.full_name = "Test User"
    mock_user.name = "Test User"
    mock_user.avatar_url = None
    mock_user.last_login_at = None
    mock_user.role = "user"
    mock_user.is_active = True
    mock_user.is_superuser = False
    mock_user.created_at = datetime.now(timezone.utc)
    mock_user.updated_at = datetime.now(timezone.utc)
    mock_user_repo.create.return_value = mock_user


    req = RegisterRequest(email="test@example.com", password="password123", full_name="Test User")
    response = await auth_service.register(req)

    assert response.email == "test@example.com"
    mock_user_repo.email_exists.assert_called_once_with("test@example.com")
    mock_user_repo.create.assert_called_once()


@pytest.mark.asyncio
async def test_register_duplicate_email(auth_service, mock_user_repo):
    mock_user_repo.email_exists.return_value = True

    req = RegisterRequest(email="existing@example.com", password="password123", full_name="Test User")
    with pytest.raises(ConflictError):
        await auth_service.register(req)


@pytest.mark.asyncio
async def test_login_invalid_credentials(auth_service, mock_user_repo):
    mock_user_repo.get_by_email.return_value = None

    req = LoginRequest(email="nonexistent@example.com", password="password123")
    with pytest.raises(AuthenticationError) as exc_info:
        await auth_service.login(req)
    assert exc_info.value.error_code == "AUTH_INVALID_CREDENTIALS"


@pytest.mark.asyncio
@patch("app.services.auth_service.verify_password", return_value=True)
async def test_login_success(mock_verify, auth_service, mock_user_repo, mock_redis):
    mock_user = MagicMock()
    user_id = uuid4()
    mock_user.id = user_id
    mock_user.email = "test@example.com"
    mock_user.hashed_password = "hashed_password"
    mock_user.is_active = True
    mock_user_repo.get_by_email.return_value = mock_user

    req = LoginRequest(email="test@example.com", password="password123")
    tokens = await auth_service.login(req)

    assert tokens.access_token is not None
    assert tokens.refresh_token is not None
    assert tokens.token_type == "bearer"
    mock_redis.setex.assert_called_once()


@pytest.mark.asyncio
async def test_registration_normalizes_email(auth_service, mock_user_repo):
    """Email normalization converts uppercase input email to lowercase."""
    mock_user_repo.email_exists.return_value = False
    mock_user = MagicMock()
    mock_user.id = uuid4()
    mock_user.email = "uppercase@example.com"
    mock_user.full_name = "Uppercase User"
    mock_user.name = "Uppercase User"
    mock_user.avatar_url = None
    mock_user.last_login_at = None
    mock_user.role = "user"
    mock_user.is_active = True
    mock_user.is_superuser = False
    mock_user.created_at = datetime.now(timezone.utc)
    mock_user_repo.create.return_value = mock_user

    req = RegisterRequest(email="UPPERCASE@EXAMPLE.COM", password="password123", name="Uppercase User")
    response = await auth_service.register(req)

    mock_user_repo.email_exists.assert_called_once_with("uppercase@example.com")


@pytest.mark.asyncio
async def test_password_stored_as_secure_hash(db_session):
    """Plaintext password is never stored; hashed_password is a bcrypt hash."""
    from app.core.security import hash_password, verify_password
    plain_pw = "supersecretpassword123"
    hashed = hash_password(plain_pw)

    assert hashed != plain_pw
    assert hashed.startswith("$2b$")
    assert verify_password(plain_pw, hashed) is True
    assert verify_password("wrongpassword", hashed) is False


@pytest.mark.asyncio
async def test_login_wrong_password_rejected(auth_service, mock_user_repo):
    """Wrong password for existing user must be rejected with 401 AUTH_INVALID_CREDENTIALS."""
    from app.core.security import hash_password
    mock_user = MagicMock()
    mock_user.id = uuid4()
    mock_user.email = "test@example.com"
    mock_user.hashed_password = hash_password("correctpassword123")
    mock_user.is_active = True
    mock_user_repo.find_user_by_email.return_value = mock_user

    req = LoginRequest(email="test@example.com", password="WRONGpassword456")
    with pytest.raises(AuthenticationError) as exc_info:
        await auth_service.login(req)

    assert exc_info.value.status_code == 401
    assert exc_info.value.error_code == "AUTH_INVALID_CREDENTIALS"


@pytest.mark.asyncio
async def test_login_user_without_password_hash_rejected(auth_service, mock_user_repo):
    """Google-only user (hashed_password is None) cannot log in with password."""
    mock_user = MagicMock()
    mock_user.id = uuid4()
    mock_user.email = "googleuser@example.com"
    mock_user.hashed_password = None
    mock_user.password_hash = None
    mock_user.is_active = True
    mock_user_repo.find_user_by_email.return_value = mock_user

    req = LoginRequest(email="googleuser@example.com", password="anypassword123")
    with pytest.raises(AuthenticationError) as exc_info:
        await auth_service.login(req)

    assert exc_info.value.status_code == 401
    assert exc_info.value.error_code == "AUTH_INVALID_CREDENTIALS"


@pytest.mark.asyncio
async def test_login_deactivated_user_rejected(auth_service, mock_user_repo):
    """Deactivated user account cannot log in even with correct password."""
    from app.core.security import hash_password
    mock_user = MagicMock()
    mock_user.id = uuid4()
    mock_user.email = "deactivated@example.com"
    mock_user.hashed_password = hash_password("correctpassword123")
    mock_user.is_active = False
    mock_user_repo.find_user_by_email.return_value = mock_user

    req = LoginRequest(email="deactivated@example.com", password="correctpassword123")
    with pytest.raises(AuthenticationError) as exc_info:
        await auth_service.login(req)

    assert exc_info.value.status_code == 401
    assert exc_info.value.error_code == "USER_DEACTIVATED"


