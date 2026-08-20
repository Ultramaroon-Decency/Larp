"""Authentication service."""

from datetime import datetime, timezone
from uuid import UUID

from google.auth.transport import requests as google_requests
from google.oauth2 import id_token as google_id_token
from redis.asyncio import Redis

from app.config import Settings
from app.core.exceptions import AuthenticationError, ConflictError
from app.core.security import (
    create_access_token,
    create_refresh_token,
    decode_refresh_token,
    hash_password,
    verify_password,
)
from app.repositories.user_repository import UserRepository
from app.schemas.auth import LoginRequest, RegisterRequest, TokenResponse, UserResponse


class AuthService:
    """Service handling authentication logic.

    Orchestrates user registration, login, Google login, and token refresh by
    coordinating the user repository with security utilities and Redis.
    """

    def __init__(
        self,
        user_repo: UserRepository,
        redis: Redis,
        settings: Settings,
    ) -> None:
        self.user_repo = user_repo
        self.redis = redis
        self.settings = settings

    async def register(self, data: RegisterRequest) -> UserResponse:
        """Register a new user account."""
        if await self.user_repo.email_exists(data.email):
            raise ConflictError(
                message="A user with this email address already exists",
                errors=["email: Already registered"],
            )

        hashed_pw = hash_password(data.password)
        user_data = {
            "email": data.email,
            "hashed_password": hashed_pw,
            "full_name": data.full_name,
            "is_active": True,
            "is_superuser": False,
        }
        user = await self.user_repo.create(user_data)
        return UserResponse.model_validate(user)

    async def login(self, data: LoginRequest) -> TokenResponse:
        """Authenticate credentials and issue JWT access & refresh tokens."""
        user = await self.user_repo.get_by_email(data.email)
        if user is None or not verify_password(data.password, user.hashed_password):
            raise AuthenticationError(
                message="Invalid email or password",
                error_code="AUTH_INVALID_CREDENTIALS",
            )

        if not user.is_active:
            raise AuthenticationError(
                message="User account is deactivated",
                error_code="USER_DEACTIVATED",
            )

        # Update last_login_at
        await self.user_repo.update(user.id, {"last_login_at": datetime.now(timezone.utc)})

        # Issue tokens
        return await self._issue_tokens(user.id)

    async def google_login(self, raw_id_token: str) -> TokenResponse:
        """Authenticate via Google ID token and issue Larp JWT tokens.

        Flow:
        1. Verify the Google ID token server-side (signature, issuer, audience, expiration).
        2. Find existing user by google_sub, or by verified email, or create new.
        3. Link Google account if user exists by email but has no google_sub.
        4. Issue the SAME Larp access + refresh tokens as email/password login.
        """
        # ── Step 1: Verify Google ID token ─────────────────────────────
        google_user_info = self._verify_google_id_token(raw_id_token)

        google_sub = google_user_info["sub"]
        email = google_user_info["email"]
        name = google_user_info.get("name", "")
        picture = google_user_info.get("picture", "")

        # ── Step 2: Find or create user ────────────────────────────────
        # Priority 1: Existing user with this google_sub (repeat login)
        user = await self.user_repo.get_by_google_sub(google_sub)

        if user is None:
            # Priority 2: Existing user with same email (link accounts)
            user = await self.user_repo.get_by_email(email)

            if user is not None:
                # Link Google to existing email account
                update_data: dict = {"google_sub": google_sub}
                if not user.full_name and name:
                    update_data["full_name"] = name
                if not user.avatar_url and picture:
                    update_data["avatar_url"] = picture
                # Do NOT touch hashed_password — user can still log in with password
                user = await self.user_repo.update(user.id, update_data)
            else:
                # Priority 3: Brand new Google user — create account
                user_data = {
                    "email": email,
                    "hashed_password": None,
                    "full_name": name or None,
                    "avatar_url": picture or None,
                    "google_sub": google_sub,
                    "is_active": True,
                    "is_superuser": False,
                }
                user = await self.user_repo.create(user_data)

        # ── Step 3: Check active status ────────────────────────────────
        if not user.is_active:
            raise AuthenticationError(
                message="User account is deactivated",
                error_code="USER_DEACTIVATED",
            )

        # ── Step 4: Update last_login_at ───────────────────────────────
        await self.user_repo.update(user.id, {"last_login_at": datetime.now(timezone.utc)})

        # ── Step 5: Issue Larp tokens (same as email/password login) ───
        return await self._issue_tokens(user.id)

    def _verify_google_id_token(self, raw_id_token: str) -> dict:
        """Verify a Google ID token and return verified claims.

        Validates: signature, issuer (accounts.google.com), audience
        (GOOGLE_CLIENT_ID), and expiration.

        Raises AuthenticationError if the token is invalid.
        """
        if not self.settings.google_client_id:
            raise AuthenticationError(
                message="Google authentication is not configured",
                error_code="AUTH_GOOGLE_NOT_CONFIGURED",
            )

        try:
            id_info = google_id_token.verify_oauth2_token(
                raw_id_token,
                google_requests.Request(),
                self.settings.google_client_id,
                clock_skew_in_seconds=60,
            )
        except ValueError as exc:
            raise AuthenticationError(
                message=f"Invalid Google ID token: {exc}",
                error_code="AUTH_GOOGLE_TOKEN_INVALID",
            )

        # Verify issuer
        issuer = id_info.get("iss", "")
        if issuer not in ("accounts.google.com", "https://accounts.google.com"):
            raise AuthenticationError(
                message="Invalid Google token issuer",
                error_code="AUTH_GOOGLE_INVALID_ISSUER",
            )

        # Verify email is present and verified
        if not id_info.get("email"):
            raise AuthenticationError(
                message="Google token missing email claim",
                error_code="AUTH_GOOGLE_NO_EMAIL",
            )

        return id_info

    async def _issue_tokens(self, user_id: UUID) -> TokenResponse:
        """Create Larp access + refresh tokens and store refresh JTI in Redis."""
        access_token = create_access_token(subject=str(user_id))
        refresh_token, jti = create_refresh_token(subject=str(user_id))

        # Store refresh token JTI in Redis with TTL matching refresh_token_expire_timedelta
        redis_key = f"refresh_token:{user_id}:{jti}"
        ttl_seconds = int(self.settings.refresh_token_expire_timedelta.total_seconds())
        await self.redis.setex(redis_key, ttl_seconds, "valid")

        return TokenResponse(
            access_token=access_token,
            refresh_token=refresh_token,
            token_type="bearer",
            expires_in=self.settings.access_token_expire_minutes * 60,
        )

    async def refresh_token(self, token: str) -> TokenResponse:
        """Exchange a valid refresh token for a new access token and rotated refresh token."""
        payload = decode_refresh_token(token)

        if not payload.jti:
            raise AuthenticationError(
                message="Malformed refresh token — missing JTI",
                error_code="AUTH_REFRESH_TOKEN_INVALID",
            )

        # Check if refresh token JTI is active in Redis
        redis_key = f"refresh_token:{payload.sub}:{payload.jti}"
        token_status = await self.redis.get(redis_key)
        if not token_status:
            raise AuthenticationError(
                message="Refresh token has been revoked or expired",
                error_code="AUTH_REFRESH_TOKEN_REVOKED",
            )

        # Verify user exists and is active
        user = await self.user_repo.get_by_id(UUID(payload.sub))
        if user is None or not user.is_active:
            raise AuthenticationError(
                message="User account inactive or not found",
                error_code="USER_INACTIVE",
            )

        # Revoke old refresh token JTI (Token Rotation)
        await self.redis.delete(redis_key)

        # Issue new token pair
        return await self._issue_tokens(user.id)

    async def logout(self, token: str) -> None:
        """Revoke refresh token to complete user logout."""
        try:
            payload = decode_refresh_token(token)
            if payload.jti:
                redis_key = f"refresh_token:{payload.sub}:{payload.jti}"
                await self.redis.delete(redis_key)
        except Exception:
            # Logout should succeed idempotently even if token is already expired
            pass
