"""SQLAlchemy declarative base and shared mixins.

Provides:

- ``Base`` — the declarative base that all models inherit from.
- ``TimestampMixin`` — adds ``created_at`` / ``updated_at`` columns.
- ``TableNameMixin`` — auto-generates ``__tablename__`` from the class name.

All models use SQLAlchemy 2.0 ``Mapped[]`` / ``mapped_column()`` style.
"""

import uuid
from datetime import datetime

from sqlalchemy import func
from sqlalchemy.orm import (
    DeclarativeBase,
    Mapped,
    mapped_column,
)


class Base(DeclarativeBase):
    """Declarative base for all ORM models.

    Provides a ``repr`` that shows the class name and primary key,
    which is useful in logs and debugging sessions.
    """

    def __repr__(self) -> str:
        pk = getattr(self, "id", None)
        return f"<{self.__class__.__name__}(id={pk})>"


class TimestampMixin:
    """Mixin that adds ``created_at`` and ``updated_at`` columns.

    - ``created_at`` is set **once** by the database server on INSERT.
    - ``updated_at`` is set on INSERT and re-set on every UPDATE.
    """

    created_at: Mapped[datetime] = mapped_column(
        server_default=func.now(),
        nullable=False,
    )
    updated_at: Mapped[datetime] = mapped_column(
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )


class UUIDPrimaryKeyMixin:
    """Mixin that adds a UUID4 primary key column named ``id``.

    UUIDs are generated **client-side** (``default=uuid.uuid4``),
    which means the ID is known before the INSERT — useful for
    building relationships in the same flush.
    """

    id: Mapped[uuid.UUID] = mapped_column(
        primary_key=True,
        default=uuid.uuid4,
    )
