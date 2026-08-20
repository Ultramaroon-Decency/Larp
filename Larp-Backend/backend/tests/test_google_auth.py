"""Tests for Google OAuth authentication flow.

Covers all 18 test scenarios specified in the requirements:
1. New Google user
2. Existing Google user (by google_sub)
3. Repeated Google login
4. Existing email/password user + Google linking
5. Google account linking preserves hashed_password
6. Duplicate user prevention
7. Invalid Google token
8. Expired Google token
9. Wrong Google audience
10. Wrong Google issuer
11. Inactive Google user
12. Google login returns Larp access token
13. Google login returns refresh token
14. /auth/me works after Google login
15. Password login still works after linking
16. Wrong password still fails after linking
17. last_login_at updates
18. google_sub persists in database
"""

from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

import pytest

from app.config import get_settings
from app.core.exceptions import AuthenticationError
from app.core.security import create_access_token, verify_password
from app.repositories.user_repository import UserRepository
from app.services.auth_service import AuthService


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

FAKE_GOOGLE_SUB = "google-sub-123456789"
FAKE_EMAIL = "testuser@gmail.com"
FAKE_NAME = "Test User"
FAKE_PICTURE = "https://lh3.googleusercontent.com/photo.jpg"

VERIFIED_GOOGLE_CLAIMS = {
    "sub": FAKE_GOOGLE_SUB,
    "email": FAKE_EMAIL,
    "name": FAKE_NAME,
    "picture": FAKE_PICTURE,
    "iss": "https://accounts.google.com",
    "aud": "test-client-id",
    "email_verified": True,
}


def _make_mock_user(
    user_id=None,
    email=FAKE_EMAIL,
    hashed_password="$2b$12$hashvalue",
    google_sub=None,
    full_name=FAKE_NAME,
    avatar_url=None,
    is_active=True,
    last_login_at=None,
):
    """Create a mock User object."""
    user = MagicMock()
    user.id = user_id or uuid4()
    user.email = email
    user.hashed_password = hashed_password
    user.google_sub = google_sub
    user.full_name = full_name
    user.avatar_url = avatar_url
    user.is_active = is_active
    user.is_superuser = False
    user.role = "user"
    user.last_login_at = last_login_at
    user.created_at = datetime.now(timezone.utc)
    user.updated_at = datetime.now(timezone.utc)
    return user


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


# ---------------------------------------------------------------------------
# Test 1: New Google user → creates user + returns tokens
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
@patch.object(AuthService, "_verify_google_id_token", return_value=VERIFIED_GOOGLE_CLAIMS)
async def test_new_google_user_creates_account(
    mock_verify, auth_service, mock_user_repo, mock_redis
):
    """Brand new Google user should create a new Larp account."""
    mock_user_repo.get_by_google_sub.return_value = None
    mock_user_repo.get_by_email.return_value = None

    new_user = _make_mock_user(google_sub=FAKE_GOOGLE_SUB, hashed_password=None)
    mock_user_repo.create.return_value = new_user
    mock_user_repo.update.return_value = new_user

    tokens = await auth_service.google_login("fake-id-token")

    assert tokens.access_token is not None
    assert tokens.refresh_token is not None
    assert tokens.token_type == "bearer"
    mock_user_repo.create.assert_called_once()
    create_call = mock_user_repo.create.call_args[0][0]
    assert create_call["google_sub"] == FAKE_GOOGLE_SUB
    assert create_call["email"] == FAKE_EMAIL
    assert create_call["hashed_password"] is None


# ---------------------------------------------------------------------------
# Test 2: Existing Google user (by google_sub) → returns tokens
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
@patch.object(AuthService, "_verify_google_id_token", return_value=VERIFIED_GOOGLE_CLAIMS)
async def test_existing_google_user_login(
    mock_verify, auth_service, mock_user_repo, mock_redis
):
    """Existing user with google_sub should log in without creating new account."""
    existing_user = _make_mock_user(google_sub=FAKE_GOOGLE_SUB)
    mock_user_repo.get_by_google_sub.return_value = existing_user
    mock_user_repo.update.return_value = existing_user

    tokens = await auth_service.google_login("fake-id-token")

    assert tokens.access_token is not None
    mock_user_repo.create.assert_not_called()
    mock_user_repo.get_by_email.assert_not_called()


# ---------------------------------------------------------------------------
# Test 3: Repeated Google login → no duplicate, no error
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
@patch.object(AuthService, "_verify_google_id_token", return_value=VERIFIED_GOOGLE_CLAIMS)
async def test_repeated_google_login_no_duplicate(
    mock_verify, auth_service, mock_user_repo, mock_redis
):
    """Multiple Google logins with same account must not create duplicates."""
    existing_user = _make_mock_user(google_sub=FAKE_GOOGLE_SUB)
    mock_user_repo.get_by_google_sub.return_value = existing_user
    mock_user_repo.update.return_value = existing_user

    # Login three times
    for _ in range(3):
        tokens = await auth_service.google_login("fake-id-token")
        assert tokens.access_token is not None

    mock_user_repo.create.assert_not_called()


# ---------------------------------------------------------------------------
# Test 4: Existing email/password user + Google → links accounts
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
@patch.object(AuthService, "_verify_google_id_token", return_value=VERIFIED_GOOGLE_CLAIMS)
async def test_google_links_existing_email_account(
    mock_verify, auth_service, mock_user_repo, mock_redis
):
    """Existing email/password user should be linked to Google, not duplicated."""
    existing_user = _make_mock_user(
        email=FAKE_EMAIL, hashed_password="$2b$12$existing_hash", google_sub=None
    )
    mock_user_repo.get_by_google_sub.return_value = None
    mock_user_repo.get_by_email.return_value = existing_user
    mock_user_repo.update.return_value = existing_user

    tokens = await auth_service.google_login("fake-id-token")

    assert tokens.access_token is not None
    mock_user_repo.create.assert_not_called()
    # Verify update was called to set google_sub
    update_calls = mock_user_repo.update.call_args_list
    # First call should be linking (setting google_sub)
    link_call = update_calls[0]
    link_data = link_call[0][1]  # second arg is the update dict
    assert link_data["google_sub"] == FAKE_GOOGLE_SUB


# ---------------------------------------------------------------------------
# Test 5: Google account linking preserves hashed_password
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
@patch.object(AuthService, "_verify_google_id_token", return_value=VERIFIED_GOOGLE_CLAIMS)
async def test_google_linking_preserves_password(
    mock_verify, auth_service, mock_user_repo, mock_redis
):
    """Linking Google must NOT overwrite existing password_hash."""
    existing_user = _make_mock_user(
        email=FAKE_EMAIL, hashed_password="$2b$12$existing_hash", google_sub=None
    )
    mock_user_repo.get_by_google_sub.return_value = None
    mock_user_repo.get_by_email.return_value = existing_user
    mock_user_repo.update.return_value = existing_user

    await auth_service.google_login("fake-id-token")

    # Verify that hashed_password is never in the update dict
    link_call = mock_user_repo.update.call_args_list[0]
    link_data = link_call[0][1]
    assert "hashed_password" not in link_data


# ---------------------------------------------------------------------------
# Test 6: Duplicate user prevention
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
@patch.object(AuthService, "_verify_google_id_token", return_value=VERIFIED_GOOGLE_CLAIMS)
async def test_no_duplicate_user_creation(
    mock_verify, auth_service, mock_user_repo, mock_redis
):
    """When google_sub matches, must not create another user."""
    existing_user = _make_mock_user(google_sub=FAKE_GOOGLE_SUB)
    mock_user_repo.get_by_google_sub.return_value = existing_user
    mock_user_repo.update.return_value = existing_user

    await auth_service.google_login("fake-id-token")

    mock_user_repo.create.assert_not_called()


# ---------------------------------------------------------------------------
# Test 7: Invalid Google token → 401
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_invalid_google_token_raises_401(auth_service):
    """Invalid Google ID token must raise AuthenticationError."""
    with patch.object(
        AuthService, "_verify_google_id_token",
        side_effect=AuthenticationError(
            message="Invalid Google ID token: Token is invalid",
            error_code="AUTH_GOOGLE_TOKEN_INVALID",
        ),
    ):
        with pytest.raises(AuthenticationError) as exc_info:
            await auth_service.google_login("invalid-token")
        assert exc_info.value.error_code == "AUTH_GOOGLE_TOKEN_INVALID"


# ---------------------------------------------------------------------------
# Test 8: Expired Google token → 401
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_expired_google_token_raises_401(auth_service):
    """Expired Google ID token must raise AuthenticationError."""
    with patch.object(
        AuthService, "_verify_google_id_token",
        side_effect=AuthenticationError(
            message="Invalid Google ID token: Token has expired",
            error_code="AUTH_GOOGLE_TOKEN_INVALID",
        ),
    ):
        with pytest.raises(AuthenticationError) as exc_info:
            await auth_service.google_login("expired-token")
        assert exc_info.value.error_code == "AUTH_GOOGLE_TOKEN_INVALID"


# ---------------------------------------------------------------------------
# Test 9: Wrong Google audience → 401
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_wrong_google_audience_raises_401(auth_service):
    """Google token with wrong audience must raise AuthenticationError."""
    with patch.object(
        AuthService, "_verify_google_id_token",
        side_effect=AuthenticationError(
            message="Invalid Google ID token: Token has wrong audience",
            error_code="AUTH_GOOGLE_TOKEN_INVALID",
        ),
    ):
        with pytest.raises(AuthenticationError) as exc_info:
            await auth_service.google_login("wrong-audience-token")
        assert exc_info.value.error_code == "AUTH_GOOGLE_TOKEN_INVALID"


# ---------------------------------------------------------------------------
# Test 10: Wrong Google issuer → 401
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_wrong_google_issuer_raises_401(auth_service, mock_user_repo):
    """Google token with wrong issuer must raise AuthenticationError."""
    bad_claims = {**VERIFIED_GOOGLE_CLAIMS, "iss": "https://evil.example.com"}

    with patch(
        "app.services.auth_service.google_id_token.verify_oauth2_token",
        return_value=bad_claims,
    ):
        with pytest.raises(AuthenticationError) as exc_info:
            await auth_service.google_login("wrong-issuer-token")
        assert exc_info.value.error_code == "AUTH_GOOGLE_INVALID_ISSUER"


# ---------------------------------------------------------------------------
# Test 11: Inactive Google user → 401
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
@patch.object(AuthService, "_verify_google_id_token", return_value=VERIFIED_GOOGLE_CLAIMS)
async def test_inactive_google_user_raises_401(
    mock_verify, auth_service, mock_user_repo, mock_redis
):
    """Deactivated user logging in via Google must get 401."""
    inactive_user = _make_mock_user(google_sub=FAKE_GOOGLE_SUB, is_active=False)
    mock_user_repo.get_by_google_sub.return_value = inactive_user

    with pytest.raises(AuthenticationError) as exc_info:
        await auth_service.google_login("fake-id-token")
    assert exc_info.value.error_code == "USER_DEACTIVATED"


# ---------------------------------------------------------------------------
# Test 12: Google login returns Larp access token
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
@patch.object(AuthService, "_verify_google_id_token", return_value=VERIFIED_GOOGLE_CLAIMS)
async def test_google_login_returns_access_token(
    mock_verify, auth_service, mock_user_repo, mock_redis
):
    """Google login must return a valid Larp access token (not a Google token)."""
    user = _make_mock_user(google_sub=FAKE_GOOGLE_SUB)
    mock_user_repo.get_by_google_sub.return_value = user
    mock_user_repo.update.return_value = user

    tokens = await auth_service.google_login("fake-id-token")

    assert tokens.access_token is not None
    assert len(tokens.access_token) > 50  # JWT is longer than a short string
    assert tokens.token_type == "bearer"

    # Verify it's a real Larp JWT by decoding it
    from app.core.security import decode_access_token
    payload = decode_access_token(tokens.access_token)
    assert payload.sub == str(user.id)
    assert payload.type == "access"


# ---------------------------------------------------------------------------
# Test 13: Google login returns refresh token
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
@patch.object(AuthService, "_verify_google_id_token", return_value=VERIFIED_GOOGLE_CLAIMS)
async def test_google_login_returns_refresh_token(
    mock_verify, auth_service, mock_user_repo, mock_redis
):
    """Google login must return a Larp refresh token stored in Redis."""
    user = _make_mock_user(google_sub=FAKE_GOOGLE_SUB)
    mock_user_repo.get_by_google_sub.return_value = user
    mock_user_repo.update.return_value = user

    tokens = await auth_service.google_login("fake-id-token")

    assert tokens.refresh_token is not None
    assert len(tokens.refresh_token) > 50
    mock_redis.setex.assert_called_once()  # Refresh JTI stored in Redis


# ---------------------------------------------------------------------------
# Test 14: /auth/me works after Google login (token validation)
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
@patch.object(AuthService, "_verify_google_id_token", return_value=VERIFIED_GOOGLE_CLAIMS)
async def test_auth_me_works_after_google_login(
    mock_verify, auth_service, mock_user_repo, mock_redis
):
    """Access token from Google login must be decodeable as Larp token for /auth/me."""
    user = _make_mock_user(google_sub=FAKE_GOOGLE_SUB)
    mock_user_repo.get_by_google_sub.return_value = user
    mock_user_repo.update.return_value = user

    tokens = await auth_service.google_login("fake-id-token")

    # Simulate what /auth/me does
    from app.core.security import decode_access_token
    payload = decode_access_token(tokens.access_token)
    assert payload.sub == str(user.id)


# ---------------------------------------------------------------------------
# Test 15: Password login still works after Google linking
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
@patch("app.services.auth_service.verify_password", return_value=True)
@patch.object(AuthService, "_verify_google_id_token", return_value=VERIFIED_GOOGLE_CLAIMS)
async def test_password_login_works_after_google_linking(
    mock_verify_google, mock_verify_pw, auth_service, mock_user_repo, mock_redis
):
    """After linking Google, email/password login must still work."""
    user = _make_mock_user(
        email=FAKE_EMAIL,
        hashed_password="$2b$12$existing_hash",
        google_sub=FAKE_GOOGLE_SUB,
    )
    mock_user_repo.get_by_email.return_value = user
    mock_user_repo.update.return_value = user

    from app.schemas.auth import LoginRequest
    tokens = await auth_service.login(LoginRequest(email=FAKE_EMAIL, password="password123"))

    assert tokens.access_token is not None
    assert tokens.refresh_token is not None


# ---------------------------------------------------------------------------
# Test 16: Wrong password still fails after linking
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
@patch("app.services.auth_service.verify_password", return_value=False)
async def test_wrong_password_fails_after_linking(
    mock_verify_pw, auth_service, mock_user_repo
):
    """After linking Google, wrong password must still return 401."""
    user = _make_mock_user(
        email=FAKE_EMAIL,
        hashed_password="$2b$12$existing_hash",
        google_sub=FAKE_GOOGLE_SUB,
    )
    mock_user_repo.get_by_email.return_value = user

    from app.schemas.auth import LoginRequest
    with pytest.raises(AuthenticationError) as exc_info:
        await auth_service.login(LoginRequest(email=FAKE_EMAIL, password="wrong"))
    assert exc_info.value.error_code == "AUTH_INVALID_CREDENTIALS"


# ---------------------------------------------------------------------------
# Test 17: last_login_at updates
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
@patch.object(AuthService, "_verify_google_id_token", return_value=VERIFIED_GOOGLE_CLAIMS)
async def test_last_login_at_updates_on_google_login(
    mock_verify, auth_service, mock_user_repo, mock_redis
):
    """Google login must update last_login_at."""
    user = _make_mock_user(google_sub=FAKE_GOOGLE_SUB, last_login_at=None)
    mock_user_repo.get_by_google_sub.return_value = user
    mock_user_repo.update.return_value = user

    await auth_service.google_login("fake-id-token")

    # update should be called with last_login_at
    update_call = mock_user_repo.update.call_args
    update_data = update_call[0][1]
    assert "last_login_at" in update_data
    assert isinstance(update_data["last_login_at"], datetime)


# ---------------------------------------------------------------------------
# Test 18: google_sub persists (verified via create call data)
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
@patch.object(AuthService, "_verify_google_id_token", return_value=VERIFIED_GOOGLE_CLAIMS)
async def test_google_sub_persists_in_create(
    mock_verify, auth_service, mock_user_repo, mock_redis
):
    """New Google user's google_sub must be stored in the database."""
    mock_user_repo.get_by_google_sub.return_value = None
    mock_user_repo.get_by_email.return_value = None

    new_user = _make_mock_user(google_sub=FAKE_GOOGLE_SUB, hashed_password=None)
    mock_user_repo.create.return_value = new_user
    mock_user_repo.update.return_value = new_user

    await auth_service.google_login("fake-id-token")

    create_data = mock_user_repo.create.call_args[0][0]
    assert create_data["google_sub"] == FAKE_GOOGLE_SUB


# ---------------------------------------------------------------------------
# Additional: verify_password handles None hashed_password
# ---------------------------------------------------------------------------

def test_verify_password_handles_none():
    """verify_password must return False for None hashed_password (Google-only users)."""
    assert verify_password("anypassword", None) is False


# ---------------------------------------------------------------------------
# Additional: Google auth not configured raises error
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_google_auth_not_configured(mock_user_repo, mock_redis):
    """If GOOGLE_CLIENT_ID is empty, google_login must raise error."""
    from unittest.mock import PropertyMock

    settings = MagicMock()
    type(settings).google_client_id = PropertyMock(return_value="")
    type(settings).access_token_expire_minutes = PropertyMock(return_value=1440)
    type(settings).refresh_token_expire_timedelta = PropertyMock(
        return_value=get_settings().refresh_token_expire_timedelta
    )

    service = AuthService(user_repo=mock_user_repo, redis=mock_redis, settings=settings)

    with pytest.raises(AuthenticationError) as exc_info:
        await service.google_login("fake-id-token")
    assert exc_info.value.error_code == "AUTH_GOOGLE_NOT_CONFIGURED"
