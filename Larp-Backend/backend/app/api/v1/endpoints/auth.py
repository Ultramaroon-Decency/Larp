"""Authentication endpoints: Register, Login, Refresh Token, Logout."""

from uuid import UUID

from fastapi import APIRouter, Depends, status
from redis.asyncio import Redis

from app.config import get_settings
from app.core.exceptions import AuthenticationError, ConflictError
from app.core.security import (
    create_access_token,
    create_refresh_token,
    decode_refresh_token,
    hash_password,
    verify_password,
)
from app.dependencies import get_current_user, get_redis_client, get_user_repository
from app.repositories.user_repository import UserRepository
from app.schemas.auth import (
    LoginRequest,
    RefreshTokenRequest,
    RegisterRequest,
    TokenResponse,
    UserResponse,
)
from app.schemas.common import ResponseEnvelope

router = APIRouter()
settings = get_settings()


@router.post(
    "/register",
    response_model=ResponseEnvelope[UserResponse],
    status_code=status.HTTP_201_CREATED,
)
async def register(
    body: RegisterRequest,
    user_repo: UserRepository = Depends(get_user_repository),
) -> ResponseEnvelope[UserResponse]:
    """Register a new user account."""
    if await user_repo.email_exists(body.email):
        raise ConflictError(
            message="A user with this email address already exists",
            errors=["email: Already registered"],
        )

    hashed_pw = hash_password(body.password)
    user_data = {
        "email": body.email,
        "hashed_password": hashed_pw,
        "full_name": body.full_name,
        "is_active": True,
        "is_superuser": False,
    }
    user = await user_repo.create(user_data)
    user_response = UserResponse.model_validate(user)

    return ResponseEnvelope(
        success=True,
        message="User account registered successfully",
        data=user_response,
    )


@router.post("/login", response_model=ResponseEnvelope[TokenResponse])
async def login(
    body: LoginRequest,
    user_repo: UserRepository = Depends(get_user_repository),
    redis: Redis = Depends(get_redis_client),
) -> ResponseEnvelope[TokenResponse]:
    """Authenticate credentials and issue JWT access & refresh tokens."""
    user = await user_repo.get_by_email(body.email)
    if user is None or not verify_password(body.password, user.hashed_password):
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
    ttl_seconds = int(settings.refresh_token_expire_timedelta.total_seconds())
    await redis.setex(redis_key, ttl_seconds, "valid")

    token_data = TokenResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        token_type="bearer",
        expires_in=settings.access_token_expire_minutes * 60,
    )

    return ResponseEnvelope(
        success=True,
        message="Authentication successful",
        data=token_data,
    )


@router.post("/refresh", response_model=ResponseEnvelope[TokenResponse])
async def refresh_token(
    body: RefreshTokenRequest,
    user_repo: UserRepository = Depends(get_user_repository),
    redis: Redis = Depends(get_redis_client),
) -> ResponseEnvelope[TokenResponse]:
    """Exchange a valid refresh token for a new access token and rotated refresh token."""
    payload = decode_refresh_token(body.refresh_token)

    if not payload.jti:
        raise AuthenticationError(
            message="Malformed refresh token — missing JTI",
            error_code="AUTH_REFRESH_TOKEN_INVALID",
        )

    # Check if refresh token JTI is active in Redis
    redis_key = f"refresh_token:{payload.sub}:{payload.jti}"
    token_status = await redis.get(redis_key)
    if not token_status:
        raise AuthenticationError(
            message="Refresh token has been revoked or expired",
            error_code="AUTH_REFRESH_TOKEN_REVOKED",
        )

    # Verify user exists and is active
    user = await user_repo.get_by_id(UUID(payload.sub))
    if user is None or not user.is_active:
        raise AuthenticationError(
            message="User account inactive or not found",
            error_code="USER_INACTIVE",
        )

    # Revoke old refresh token JTI (Token Rotation)
    await redis.delete(redis_key)

    # Issue new token pair
    new_access_token = create_access_token(subject=str(user.id))
    new_refresh_token, new_jti = create_refresh_token(subject=str(user.id))

    # Store new refresh token JTI in Redis
    new_redis_key = f"refresh_token:{user.id}:{new_jti}"
    ttl_seconds = int(settings.refresh_token_expire_timedelta.total_seconds())
    await redis.setex(new_redis_key, ttl_seconds, "valid")

    token_data = TokenResponse(
        access_token=new_access_token,
        refresh_token=new_refresh_token,
        token_type="bearer",
        expires_in=settings.access_token_expire_minutes * 60,
    )

    return ResponseEnvelope(
        success=True,
        message="Token refreshed successfully",
        data=token_data,
    )


@router.post("/logout", response_model=ResponseEnvelope[None])
async def logout(
    body: RefreshTokenRequest,
    redis: Redis = Depends(get_redis_client),
) -> ResponseEnvelope[None]:
    """Revoke refresh token to complete user logout."""
    try:
        payload = decode_refresh_token(body.refresh_token)
        if payload.jti:
            redis_key = f"refresh_token:{payload.sub}:{payload.jti}"
            await redis.delete(redis_key)
    except Exception:
        # Logout should succeed idempotently even if token is already expired
        pass

    return ResponseEnvelope(
        success=True,
        message="Logged out successfully",
        data=None,
    )
