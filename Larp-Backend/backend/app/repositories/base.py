"""Generic base repository implementing the Repository Pattern.

Provides type-safe, reusable CRUD operations for any SQLAlchemy model.
Concrete repositories (``UserRepository``, ``ResearchRepository``, …)
inherit from this and add domain-specific query methods.

Key design decisions:

- **Generic[ModelType]** — full type-safety; IDE autocomplete works on
  the return types of ``get_by_id()``, ``create()``, etc.
- **Session injected via constructor** — the repository never creates
  or commits a session; that's the caller's responsibility (Unit of
  Work pattern enforced by ``database.get_async_session()``).
- **``flush()`` not ``commit()``** — changes are flushed to the DB so
  IDs / server defaults are available, but the transaction commit
  happens in the session context manager in ``database.py``.
- **Custom exceptions** — SQLAlchemy errors are caught and wrapped in
  ``DatabaseError`` / ``DatabaseIntegrityError`` / ``NotFoundError`` so
  the error handler returns the correct HTTP status code.
"""

from typing import Any, Generic, Sequence, TypeVar
from uuid import UUID

from sqlalchemy import delete, func, select, update
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload, selectinload

from app.core.exceptions import (
    DatabaseError,
    DatabaseIntegrityError,
    NotFoundError,
)

ModelType = TypeVar("ModelType")


class BaseRepository(Generic[ModelType]):
    """Generic async repository for CRUD operations.

    Usage::

        class UserRepository(BaseRepository[User]):
            def __init__(self, session: AsyncSession):
                super().__init__(model=User, session=session)

            async def get_by_email(self, email: str) -> User | None:
                return await self.get_one_by(email=email)
    """

    def __init__(self, model: type[ModelType], session: AsyncSession) -> None:
        self.model = model
        self.session = session

    # ── Read ───────────────────────────────────────────────────────────

    async def get_by_id(self, id: UUID) -> ModelType | None:
        """Return a single record by primary key, or ``None``."""
        stmt = select(self.model).where(self.model.id == id)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_by_id_or_raise(self, id: UUID) -> ModelType:
        """Return a single record by primary key, or raise ``NotFoundError``."""
        obj = await self.get_by_id(id)
        if obj is None:
            raise NotFoundError(
                f"{self.model.__name__} with id '{id}' not found"
            )
        return obj

    async def get_one_by(self, **filters: Any) -> ModelType | None:
        """Return a single record matching the given column filters.

        Usage::

            user = await repo.get_one_by(email="a@b.com", is_active=True)
        """
        stmt = select(self.model).filter_by(**filters)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_all(
        self,
        skip: int = 0,
        limit: int = 100,
        order_by: str | None = None,
    ) -> Sequence[ModelType]:
        """Return paginated records with optional ordering.

        Args:
            skip:     Number of records to skip (offset).
            limit:    Maximum records to return.
            order_by: Column name to sort by (prefix with ``-`` for DESC).
        """
        stmt = select(self.model)

        if order_by:
            desc = order_by.startswith("-")
            col_name = order_by.lstrip("-")
            col = getattr(self.model, col_name, None)
            if col is not None:
                stmt = stmt.order_by(col.desc() if desc else col.asc())

        stmt = stmt.offset(skip).limit(limit)
        result = await self.session.execute(stmt)
        return result.scalars().all()

    async def get_many_by(
        self,
        skip: int = 0,
        limit: int = 100,
        order_by: str | None = None,
        **filters: Any,
    ) -> Sequence[ModelType]:
        """Return paginated records matching column filters."""
        stmt = select(self.model).filter_by(**filters)

        if order_by:
            desc = order_by.startswith("-")
            col_name = order_by.lstrip("-")
            col = getattr(self.model, col_name, None)
            if col is not None:
                stmt = stmt.order_by(col.desc() if desc else col.asc())

        stmt = stmt.offset(skip).limit(limit)
        result = await self.session.execute(stmt)
        return result.scalars().all()

    async def exists(self, **filters: Any) -> bool:
        """Return ``True`` if at least one matching record exists."""
        stmt = select(func.count()).select_from(self.model).filter_by(**filters)
        result = await self.session.execute(stmt)
        return (result.scalar_one() or 0) > 0

    async def count(self, **filters: Any) -> int:
        """Count records, optionally filtered."""
        stmt = select(func.count()).select_from(self.model)
        if filters:
            stmt = stmt.filter_by(**filters)
        result = await self.session.execute(stmt)
        return result.scalar_one() or 0

    # ── Create ─────────────────────────────────────────────────────────

    async def create(self, obj_data: dict[str, Any]) -> ModelType:
        """Insert a new record and return it with server-generated fields.

        Raises:
            DatabaseIntegrityError: On unique / FK constraint violation.
            DatabaseError: On any other database failure.
        """
        try:
            db_obj = self.model(**obj_data)
            self.session.add(db_obj)
            await self.session.flush()
            await self.session.refresh(db_obj)
            return db_obj
        except IntegrityError as exc:
            await self.session.rollback()
            raise DatabaseIntegrityError(
                f"Integrity constraint violated: {_extract_constraint(exc)}"
            ) from exc
        except SQLAlchemyError as exc:
            await self.session.rollback()
            raise DatabaseError(f"Failed to create {self.model.__name__}") from exc

    # ── Update ─────────────────────────────────────────────────────────

    async def update(self, id: UUID, obj_data: dict[str, Any]) -> ModelType:
        """Update an existing record by ID. Raises ``NotFoundError`` if missing.

        Raises:
            NotFoundError: If no record with this ID exists.
            DatabaseIntegrityError: On constraint violation.
        """
        db_obj = await self.get_by_id_or_raise(id)
        try:
            for key, value in obj_data.items():
                setattr(db_obj, key, value)
            await self.session.flush()
            await self.session.refresh(db_obj)
            return db_obj
        except IntegrityError as exc:
            await self.session.rollback()
            raise DatabaseIntegrityError(
                f"Integrity constraint violated: {_extract_constraint(exc)}"
            ) from exc
        except SQLAlchemyError as exc:
            await self.session.rollback()
            raise DatabaseError(f"Failed to update {self.model.__name__}: {exc}") from exc

    # ── Delete ─────────────────────────────────────────────────────────

    async def delete(self, id: UUID) -> bool:
        """Delete a record by ID. Returns ``True`` if deleted."""
        stmt = delete(self.model).where(self.model.id == id)
        result = await self.session.execute(stmt)
        await self.session.flush()
        return result.rowcount > 0

    async def delete_or_raise(self, id: UUID) -> None:
        """Delete a record by ID, raising ``NotFoundError`` if missing."""
        deleted = await self.delete(id)
        if not deleted:
            raise NotFoundError(
                f"{self.model.__name__} with id '{id}' not found"
            )


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _extract_constraint(exc: IntegrityError) -> str:
    """Extract the constraint name from an IntegrityError for logging."""
    orig = getattr(exc, "orig", None)
    if orig:
        msg = str(orig)
        # asyncpg format: 'duplicate key value violates unique constraint "users_email_key"'
        if "unique constraint" in msg.lower():
            return msg.split('"')[1] if '"' in msg else msg
        return msg[:200]
    return str(exc)[:200]
