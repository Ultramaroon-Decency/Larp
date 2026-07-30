"""Payment database model with x402 payment protocol, budget tracking, and retry metrics."""

import uuid
from typing import TYPE_CHECKING, Optional

from sqlalchemy import Float, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin, UUIDPrimaryKeyMixin

if TYPE_CHECKING:
    from app.models.user import User


class Payment(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """Payment entity tracking x402 billing, API cost tracking, user budgets, failures, and retries."""

    __tablename__ = "payments"

    user_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), index=True, nullable=False
    )
    stripe_payment_id: Mapped[Optional[str]] = mapped_column(
        String(255), unique=True, index=True, nullable=True
    )
    amount_cents: Mapped[int] = mapped_column(Integer, nullable=False)
    currency: Mapped[str] = mapped_column(String(3), default="usd", nullable=False)
    status: Mapped[str] = mapped_column(
        String(50), default="pending", index=True, nullable=False
    )  # pending, succeeded, failed, refunded, 402_required
    credits_awarded: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    payment_method: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)

    # ── x402 Payment & Resilience Fields ────────────────────────────────
    cost_usd: Mapped[Optional[float]] = mapped_column(Float, default=0.0, nullable=True)
    retry_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    error_message: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Relationships
    user: Mapped["User"] = relationship("User", back_populates="payments")
