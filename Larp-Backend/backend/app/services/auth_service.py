"""Authentication service."""

from uuid import UUID
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

    Orchestrates user registration, login, and token refresh by
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

        # Issue tokens
        access_token = create_access_token(subject=str(user.id))
        refresh_token, jti = create_refresh_token(subject=str(user.id))

        # Store refresh token JTI in Redis with TTL matching refresh_token_expire_timedelta
        redis_key = f"refresh_token:{user.id}:{jti}"
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
        new_access_token = create_access_token(subject=str(user.id))
        new_refresh_token, new_jti = create_refresh_token(subject=str(user.id))

        # Store new refresh token JTI in Redis
        new_redis_key = f"refresh_token:{user.id}:{new_jti}"
        ttl_seconds = int(self.settings.refresh_token_expire_timedelta.total_seconds())
        await self.redis.setex(new_redis_key, ttl_seconds, "valid")

        return TokenResponse(
            access_token=new_access_token,
            refresh_token=new_refresh_token,
            token_type="bearer",
            expires_in=self.settings.access_token_expire_minutes * 60,
        )

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
