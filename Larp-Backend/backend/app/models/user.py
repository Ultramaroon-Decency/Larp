"""User database model with explicit Role-Based Access Control (RBAC)."""

import enum
import uuid
from typing import TYPE_CHECKING, List

from sqlalchemy import Boolean, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin, UUIDPrimaryKeyMixin

if TYPE_CHECKING:
    from app.models.research_job import ResearchJob
    from app.models.research_report import ResearchReport
    from app.models.research_history import ResearchHistory
    from app.models.payment import Payment


class UserRole(str, enum.Enum):
    """Supported RBAC roles."""

    ADMIN = "admin"
    USER = "user"


class User(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """User entity storing credentials, profile, RBAC role, and authorization flags."""

    __tablename__ = "users"

    email: Mapped[str] = mapped_column(
        String(255), unique=True, index=True, nullable=False
    )
    hashed_password: Mapped[str] = mapped_column(String(255), nullable=False)
    full_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    role: Mapped[str] = mapped_column(
        String(20), default=UserRole.USER.value, index=True, nullable=False
    )  # "admin" or "user"
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    is_superuser: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    @property
    def is_admin(self) -> bool:
        """Return True if user is an Administrator or Superuser."""
        return self.role == UserRole.ADMIN.value or self.is_superuser

    # Relationships
    jobs: Mapped[List["ResearchJob"]] = relationship(
        "ResearchJob", back_populates="user", cascade="all, delete-orphan"
    )
    reports: Mapped[List["ResearchReport"]] = relationship(
        "ResearchReport", back_populates="user", cascade="all, delete-orphan"
    )
    history: Mapped[List["ResearchHistory"]] = relationship(
        "ResearchHistory", back_populates="user", cascade="all, delete-orphan"
    )
    payments: Mapped[List["Payment"]] = relationship(
        "Payment", back_populates="user", cascade="all, delete-orphan"
    )
