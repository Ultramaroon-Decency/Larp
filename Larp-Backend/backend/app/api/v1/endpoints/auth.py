"""Authentication endpoints: Register, Login, Google Login, Refresh Token, Logout, Me."""

from uuid import UUID

from fastapi import APIRouter, Depends, status

from app.dependencies import get_auth_service, get_current_user, get_user_repository
from app.repositories.user_repository import UserRepository
from app.schemas.auth import (
    GoogleLoginRequest,
    LoginRequest,
    RefreshTokenRequest,
    RegisterRequest,
    TokenResponse,
    UserResponse,
)
from app.schemas.common import ResponseEnvelope
from app.services.auth_service import AuthService

router = APIRouter()


@router.post(
    "/register",
    response_model=ResponseEnvelope[UserResponse],
    status_code=status.HTTP_201_CREATED,
)
async def register(
    body: RegisterRequest,
    auth_service: AuthService = Depends(get_auth_service),
) -> ResponseEnvelope[UserResponse]:
    """Register a new user account."""
    user_response = await auth_service.register(body)
    return ResponseEnvelope(
        success=True,
        message="User account registered successfully",
        data=user_response,
    )


@router.post("/login", response_model=ResponseEnvelope[TokenResponse])
async def login(
    body: LoginRequest,
    auth_service: AuthService = Depends(get_auth_service),
) -> ResponseEnvelope[TokenResponse]:
    """Authenticate credentials and issue JWT access & refresh tokens."""
    token_data = await auth_service.login(body)
    return ResponseEnvelope(
        success=True,
        message="Authentication successful",
        data=token_data,
    )


@router.post("/google", response_model=ResponseEnvelope[TokenResponse])
async def google_login(
    body: GoogleLoginRequest,
    auth_service: AuthService = Depends(get_auth_service),
) -> ResponseEnvelope[TokenResponse]:
    """Authenticate via Google ID token and issue Larp JWT access & refresh tokens.

    Accepts a Google ID token, verifies it server-side, finds or creates the
    Larp user, and returns the same token response as email/password login.
    """
    token_data = await auth_service.google_login(body.id_token)
    return ResponseEnvelope(
        success=True,
        message="Google authentication successful",
        data=token_data,
    )


@router.post("/refresh", response_model=ResponseEnvelope[TokenResponse])
async def refresh_token(
    body: RefreshTokenRequest,
    auth_service: AuthService = Depends(get_auth_service),
) -> ResponseEnvelope[TokenResponse]:
    """Exchange a valid refresh token for a new access token and rotated refresh token."""
    token_data = await auth_service.refresh_token(body.refresh_token)
    return ResponseEnvelope(
        success=True,
        message="Token refreshed successfully",
        data=token_data,
    )


@router.post("/logout", response_model=ResponseEnvelope[None])
async def logout(
    body: RefreshTokenRequest,
    auth_service: AuthService = Depends(get_auth_service),
) -> ResponseEnvelope[None]:
    """Revoke refresh token to complete user logout."""
    await auth_service.logout(body.refresh_token)
    return ResponseEnvelope(
        success=True,
        message="Logged out successfully",
        data=None,
    )


@router.get("/me", response_model=ResponseEnvelope[UserResponse])
async def get_current_user_profile(
    current_user: dict = Depends(get_current_user),
    user_repo: UserRepository = Depends(get_user_repository),
) -> ResponseEnvelope[UserResponse]:
    """Return the authenticated user's profile.

    Works with any Larp JWT token — whether issued via email/password
    or Google login.
    """
    user_id = UUID(current_user["id"])
    user = await user_repo.get_by_id(user_id)
    if user is None:
        from app.core.exceptions import AuthenticationError
        raise AuthenticationError(
            message="User not found",
            error_code="USER_NOT_FOUND",
        )
    return ResponseEnvelope(
        success=True,
        message="User profile retrieved successfully",
        data=UserResponse.model_validate(user),
    )
