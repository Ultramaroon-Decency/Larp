"""Authentication endpoints: Register, Login, Refresh Token, Logout."""

from fastapi import APIRouter, Depends, status

from app.dependencies import get_auth_service, get_current_active_user
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


@router.post("/google", response_model=ResponseEnvelope[TokenResponse])
async def google_login(
    body: GoogleLoginRequest,
    auth_service: AuthService = Depends(get_auth_service),
) -> ResponseEnvelope[TokenResponse]:
    """Authenticate Google ID token and issue JWT access & refresh tokens."""
    token_data = await auth_service.google_login(body.credential)
    return ResponseEnvelope(
        success=True,
        message="Google authentication successful",
        data=token_data,
    )


@router.get("/me", response_model=ResponseEnvelope[UserResponse])
async def get_current_user_profile(
    current_user=Depends(get_current_active_user),
) -> ResponseEnvelope[UserResponse]:
    """Return the currently authenticated user's profile."""
    return ResponseEnvelope(
        success=True,
        message="Current user profile retrieved successfully",
        data=UserResponse.model_validate(current_user),
    )

