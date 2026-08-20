from datetime import datetime, timezone
from uuid import UUID
from redis.asyncio import Redis

from app.config import Settings
from app.core.exceptions import AuthenticationError, ConflictError
from app.core.security import (
    create_access_token,
    create_refresh_token,
    decode_refresh_token,
    hash_password,
    verify_google_token,
    verify_password,
)
from app.core.logging import get_logger
from app.repositories.user_repository import UserRepository
from app.schemas.auth import LoginRequest, RegisterRequest, TokenResponse, UserResponse

logger = get_logger("auth_service")




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
        normalized_email = data.email.lower().strip()
        if await self.user_repo.email_exists(normalized_email):
            raise ConflictError(
                message="A user with this email address already exists",
                errors=["email: Already registered"],
            )

        hashed_pw = hash_password(data.password)
        user_data = {
            "email": normalized_email,
            "hashed_password": hashed_pw,
            "full_name": data.display_name,
            "is_active": True,
            "is_superuser": False,
        }
        user = await self.user_repo.create(user_data)
        return UserResponse.model_validate(user)

    async def login(self, data: LoginRequest) -> TokenResponse:
        """Authenticate credentials and issue JWT access & refresh tokens."""
        normalized_email = data.email.lower().strip()
        user = await self.user_repo.find_user_by_email(normalized_email)

        if user is None:
            raise AuthenticationError(
                message="Invalid email or password",
                error_code="AUTH_INVALID_CREDENTIALS",
            )

        if not user.hashed_password and not getattr(user, "password_hash", None):
            raise AuthenticationError(
                message="Invalid email or password",
                error_code="AUTH_INVALID_CREDENTIALS",
            )

        target_hash = user.hashed_password or getattr(user, "password_hash", None)
        if not verify_password(data.password, target_hash):
            raise AuthenticationError(
                message="Invalid email or password",
                error_code="AUTH_INVALID_CREDENTIALS",
            )

        if not user.is_active:
            raise AuthenticationError(
                message="User account is deactivated",
                error_code="USER_DEACTIVATED",
            )

        # Update last_login_at timestamp
        now = datetime.now(timezone.utc)
        await self.user_repo.update(user.id, {"last_login_at": now})

        # Issue tokens
        access_token = create_access_token(subject=str(user.id))
        refresh_token, jti = create_refresh_token(subject=str(user.id))

        # Store refresh token JTI in Redis with TTL matching refresh_token_expire_timedelta
        try:
            redis_key = f"refresh_token:{user.id}:{jti}"
            ttl_seconds = int(self.settings.refresh_token_expire_timedelta.total_seconds())
            await self.redis.setex(redis_key, ttl_seconds, "valid")
        except Exception as exc:
            logger.warning("Redis store refresh token failed (running in offline mode)", error=str(exc))


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

    async def google_login(self, credential: str) -> TokenResponse:
        """Authenticate user using a verified Google ID token."""
        id_info = verify_google_token(credential, self.settings.google_client_id)

        google_sub = id_info["sub"]
        email = id_info["email"]
        name = id_info.get("name")
        picture = id_info.get("picture")

        now = datetime.now(timezone.utc)
        user = await self.user_repo.find_user_by_google_id(google_sub)

        if user is not None:
            if not user.is_active:
                raise AuthenticationError(
                    message="User account is deactivated",
                    error_code="USER_DEACTIVATED",
                )
            await self.user_repo.update(
                user.id,
                {
                    "full_name": name or user.full_name,
                    "avatar_url": picture or user.avatar_url,
                    "last_login_at": now,
                },
            )
            user = await self.user_repo.get_by_id(user.id)
        else:
            # Do not automatically link Google accounts by email because
            # that could allow unintended account takeover.
            existing_user = await self.user_repo.find_user_by_email(email)
            if existing_user is not None and not existing_user.google_sub:
                raise ConflictError(
                    message="An account with this email address already exists. Account linking is required.",
                    errors=["email: Account linking required"],
                    error_code="AUTH_ACCOUNT_LINKING_REQUIRED",
                )
            user_data = {
                "email": email,
                "google_sub": google_sub,
                "full_name": name,
                "avatar_url": picture,
                "hashed_password": None,
                "is_active": True,
                "is_superuser": False,
                "last_login_at": now,
            }
            user = await self.user_repo.create(user_data)

        if not user or not user.is_active:
            raise AuthenticationError(
                message="User account is inactive",
                error_code="USER_INACTIVE",
            )

        access_token = create_access_token(subject=str(user.id))
        refresh_token, jti = create_refresh_token(subject=str(user.id))

        try:
            redis_key = f"refresh_token:{user.id}:{jti}"
            ttl_seconds = int(self.settings.refresh_token_expire_timedelta.total_seconds())
            await self.redis.setex(redis_key, ttl_seconds, "valid")
        except Exception as exc:
            logger.warning("Redis store refresh token failed (running in offline mode)", error=str(exc))


        return TokenResponse(
            access_token=access_token,
            refresh_token=refresh_token,
            token_type="bearer",
            expires_in=self.settings.access_token_expire_minutes * 60,
        )


