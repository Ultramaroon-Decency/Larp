"""Authentication Pydantic schemas for requests, responses, and token payloads."""

import uuid
from datetime import datetime
from pydantic import BaseModel, ConfigDict, EmailStr, Field


class RegisterRequest(BaseModel):
    """Register request payload."""

    email: EmailStr = Field(description="User email address")
    password: str = Field(min_length=8, max_length=128, description="Plaintext password (min 8 chars)")
    full_name: str | None = Field(default=None, max_length=255, description="Optional full name")


class LoginRequest(BaseModel):
    """Login request payload."""

    email: EmailStr = Field(description="User email address")
    password: str = Field(description="Plaintext password")


class RefreshTokenRequest(BaseModel):
    """Refresh token request payload."""

    refresh_token: str = Field(description="Valid long-lived refresh token")


class GoogleLoginRequest(BaseModel):
    """Google OAuth login request payload."""

    id_token: str = Field(description="Google ID token from Google Sign-In")


class TokenResponse(BaseModel):
    """Token response payload returned upon successful login or refresh."""

    access_token: str = Field(description="Signed JWT access token")
    refresh_token: str = Field(description="Signed JWT refresh token")
    token_type: str = Field(default="bearer", description="Token scheme (bearer)")
    expires_in: int = Field(description="Access token lifetime in seconds")


class UserResponse(BaseModel):
    """User profile summary schema."""

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    email: EmailStr
    full_name: str | None = None
    role: str = "user"
    is_active: bool
    is_superuser: bool
    google_sub: str | None = None
    avatar_url: str | None = None
    created_at: datetime


class TokenPayload(BaseModel):
    """Token content payload decoded from JWT claims."""

    sub: str = Field(description="Subject claim — User UUID as string")
    type: str = Field(default="access", description="Token type claim ('access' or 'refresh')")
    jti: str | None = Field(default=None, description="JWT ID claim for refresh token tracking")
    exp: int = Field(description="Expiration Unix timestamp")
    iat: int = Field(description="Issued-at Unix timestamp")

