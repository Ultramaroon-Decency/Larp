"""Add cancelled_at timestamp column to research_jobs table.

Revision ID: 0002_add_cancelled_at
Revises: 0001_initial_schema
Create Date: 2026-08-03 19:55:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '0002_add_cancelled_at'
down_revision: Union[str, None] = '0001_initial_schema'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Apply forward migration — add cancelled_at column to research_jobs."""
    op.add_column('research_jobs', sa.Column('cancelled_at', sa.DateTime(), nullable=True))


def downgrade() -> None:
    """Revert migration — drop cancelled_at column from research_jobs."""
    op.drop_column('research_jobs', 'cancelled_at')
