"""Payment repository — data access queries for the ``payments`` table."""

from typing import Sequence
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.payment import Payment
from app.repositories.base import BaseRepository


class PaymentRepository(BaseRepository[Payment]):
    """Data access repository for Payment entities."""

    def __init__(self, session: AsyncSession) -> None:
        super().__init__(model=Payment, session=session)

    async def get_by_stripe_id(self, stripe_payment_id: str) -> Payment | None:
        """Fetch payment record by Stripe payment ID."""
        return await self.get_one_by(stripe_payment_id=stripe_payment_id)

    async def get_by_user_id(
        self, user_id: UUID, skip: int = 0, limit: int = 100
    ) -> Sequence[Payment]:
        """Fetch payment history for a user (newest first)."""
        stmt = (
            select(Payment)
            .where(Payment.user_id == user_id)
            .order_by(Payment.created_at.desc())
            .offset(skip)
            .limit(limit)
        )
        result = await self.session.execute(stmt)
        return result.scalars().all()
