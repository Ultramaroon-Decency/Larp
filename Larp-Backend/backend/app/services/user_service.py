"""User service handling profile management, profile updates, password changes, and account deletion."""

from uuid import UUID

from app.core.exceptions import AuthenticationError, ConflictError, NotFoundError
from app.core.security import hash_password, verify_password
from app.repositories.user_repository import UserRepository
from app.schemas.user import ChangePasswordRequest, UserRead, UserUpdate


class UserService:
    """Service encapsulating user profile business logic."""

    def __init__(self, user_repo: UserRepository) -> None:
        self.user_repo = user_repo

    async def get_profile(self, user_id: UUID) -> UserRead:
        """Retrieve user profile by UUID.

        Raises:
            NotFoundError: If user does not exist.
        """
        user = await self.user_repo.get_by_id_or_raise(user_id)
        return UserRead.model_validate(user)

    async def update_profile(self, user_id: UUID, data: UserUpdate) -> UserRead:
        """Update user profile (full_name, email).

        Raises:
            NotFoundError: If user does not exist.
            ConflictError: If new email is already registered by another account.
        """
        user = await self.user_repo.get_by_id_or_raise(user_id)
        update_data = data.model_dump(exclude_unset=True)

        if "email" in update_data and update_data["email"] != user.email:
            new_email = update_data["email"]
            if await self.user_repo.email_exists(new_email):
                raise ConflictError(
                    message="A user with this email address already exists",
                    errors=[f"email: '{new_email}' is already taken"],
                )

        if not update_data:
            return UserRead.model_validate(user)

        updated_user = await self.user_repo.update(user_id, update_data)
        return UserRead.model_validate(updated_user)

    async def change_password(
        self, user_id: UUID, data: ChangePasswordRequest
    ) -> None:
        """Verify current password and set new bcrypt hashed password.

        Raises:
            NotFoundError: If user does not exist.
            AuthenticationError: If current password verification fails.
        """
        user = await self.user_repo.get_by_id_or_raise(user_id)

        if not verify_password(data.current_password, user.hashed_password):
            raise AuthenticationError(
                message="Current password is incorrect",
                error_code="INVALID_CURRENT_PASSWORD",
            )

        new_hashed_password = hash_password(data.new_password)
        await self.user_repo.update(user_id, {"hashed_password": new_hashed_password})

    async def delete_account(self, user_id: UUID) -> None:
        """Deactivate user account (soft delete).

        Raises:
            NotFoundError: If user does not exist.
        """
        user = await self.user_repo.get_by_id_or_raise(user_id)
        if user.is_active:
            await self.user_repo.deactivate(user_id)
