"""User profile and user management endpoints backed by UserService."""

from uuid import UUID

from fastapi import APIRouter, Depends, status

from app.dependencies import (
    get_current_admin_user,
    get_current_user,
    get_user_repository,
    get_user_service,
)
from app.repositories.user_repository import UserRepository
from app.schemas.common import ResponseEnvelope
from app.schemas.user import ChangePasswordRequest, UserRead, UserUpdate
from app.services.user_service import UserService

router = APIRouter()


@router.get("/me", response_model=ResponseEnvelope[UserRead])
async def get_my_profile(
    current_user: dict = Depends(get_current_user),
    user_service: UserService = Depends(get_user_service),
) -> ResponseEnvelope[UserRead]:
    """Return the authenticated user's profile."""
    user_id = UUID(current_user["id"])
    profile = await user_service.get_profile(user_id)

    return ResponseEnvelope(
        success=True,
        message="User profile retrieved successfully",
        data=profile,
    )


@router.patch("/me", response_model=ResponseEnvelope[UserRead])
async def update_my_profile(
    body: UserUpdate,
    current_user: dict = Depends(get_current_user),
    user_service: UserService = Depends(get_user_service),
) -> ResponseEnvelope[UserRead]:
    """Update the authenticated user's profile details."""
    user_id = UUID(current_user["id"])
    updated_profile = await user_service.update_profile(user_id, body)

    return ResponseEnvelope(
        success=True,
        message="User profile updated successfully",
        data=updated_profile,
    )


@router.post("/me/change-password", response_model=ResponseEnvelope[None])
async def change_password(
    body: ChangePasswordRequest,
    current_user: dict = Depends(get_current_user),
    user_service: UserService = Depends(get_user_service),
) -> ResponseEnvelope[None]:
    """Change the authenticated user's password."""
    user_id = UUID(current_user["id"])
    await user_service.change_password(user_id, body)

    return ResponseEnvelope(
        success=True,
        message="Password changed successfully",
        data=None,
    )


@router.delete("/me", response_model=ResponseEnvelope[None])
async def delete_my_account(
    current_user: dict = Depends(get_current_user),
    user_service: UserService = Depends(get_user_service),
) -> ResponseEnvelope[None]:
    """Delete (deactivate) the authenticated user's own account."""
    user_id = UUID(current_user["id"])
    await user_service.delete_account(user_id)

    return ResponseEnvelope(
        success=True,
        message="Account deactivated successfully",
        data=None,
    )


@router.get("/{user_id}", response_model=ResponseEnvelope[UserRead])
async def get_user_by_id(
    user_id: UUID,
    current_user: dict = Depends(get_current_user),
    user_repo: UserRepository = Depends(get_user_repository),
    user_service: UserService = Depends(get_user_service),
) -> ResponseEnvelope[UserRead]:
    """Get a specific user profile by UUID (self or superuser)."""
    if str(user_id) != current_user["id"]:
        actor_id = UUID(current_user["id"])
        actor = await user_repo.get_by_id_or_raise(actor_id)
        if not actor.is_superuser:
            raise AuthorizationError("Insufficient permissions to view other profiles")

    profile = await user_service.get_profile(user_id)
    return ResponseEnvelope(
        success=True,
        message="User profile retrieved successfully",
        data=profile,
    )


@router.delete("/{user_id}", response_model=ResponseEnvelope[None])
async def delete_user_by_admin(
    user_id: UUID,
    admin_user=Depends(get_current_admin_user),
    user_service: UserService = Depends(get_user_service),
) -> ResponseEnvelope[None]:
    """Deactivate a user account by UUID (Admin only)."""
    await user_service.delete_account(user_id)
    return ResponseEnvelope(
        success=True,
        message=f"User account '{user_id}' deactivated by admin",
        data=None,
    )
