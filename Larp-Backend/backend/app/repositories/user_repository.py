"""User repository — data access queries for the ``users`` table."""

from typing import Sequence
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import User
from app.repositories.base import BaseRepository


class UserRepository(BaseRepository[User]):
    """Data access repository for User entities."""

    def __init__(self, session: AsyncSession) -> None:
        super().__init__(model=User, session=session)

    async def get_by_email(self, email: str) -> User | None:
        """Find user by email address."""
        return await self.get_one_by(email=email)

    async def find_user_by_email(self, email: str) -> User | None:
        """Find user by email address (alias)."""
        return await self.get_by_email(email)

    async def get_by_google_sub(self, google_sub: str) -> User | None:
        """Find user by Google sub identifier."""
        return await self.get_one_by(google_sub=google_sub)

    async def find_user_by_google_id(self, google_sub: str) -> User | None:
        """Find user by Google sub identifier (alias)."""
        return await self.get_by_google_sub(google_sub)


    async def email_exists(self, email: str) -> bool:
        """Check if an email address is already registered."""
        return await self.exists(email=email)

    async def get_active_users(
        self, skip: int = 0, limit: int = 100
    ) -> Sequence[User]:
        """Fetch paginated list of active users."""
        stmt = (
            select(User)
            .where(User.is_active.is_(True))
            .order_by(User.created_at.desc())
            .offset(skip)
            .limit(limit)
        )
        result = await self.session.execute(stmt)
        return result.scalars().all()
