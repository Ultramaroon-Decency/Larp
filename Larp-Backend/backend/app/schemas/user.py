"""User management Pydantic schemas."""

import uuid
from datetime import datetime
from pydantic import BaseModel, ConfigDict, EmailStr, Field


class UserCreate(BaseModel):
    """User creation schema."""

    email: EmailStr = Field(description="User email address")
    password: str = Field(min_length=8, max_length=128, description="Password (min 8 characters)")
    full_name: str | None = Field(default=None, max_length=255, description="Full display name")


class UserRead(BaseModel):
    """User read / profile schema."""

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    email: EmailStr
    full_name: str | None = None
    name: str | None = None
    avatar_url: str | None = None
    role: str = "user"
    is_active: bool
    is_superuser: bool
    created_at: datetime
    last_login_at: datetime | None = None


class UserUpdate(BaseModel):
    """User profile update schema."""

    full_name: str | None = Field(default=None, max_length=255, description="Updated full name")
    email: EmailStr | None = Field(default=None, description="Updated email address")


class ChangePasswordRequest(BaseModel):
    """Change password payload schema."""

    current_password: str = Field(description="Current plaintext password")
    new_password: str = Field(
        min_length=8, max_length=128, description="New plaintext password (min 8 characters)"
    )
