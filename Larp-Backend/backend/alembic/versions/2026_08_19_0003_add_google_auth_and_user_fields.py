"""Add google_sub, avatar_url, and last_login_at to users table.

Revision ID: 0003_add_google_auth_and_user_fields
Revises: 0002_add_cancelled_at
Create Date: 2026-08-19 21:30:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '0003_add_google_auth_and_user_fields'
down_revision: Union[str, None] = '0002_add_cancelled_at'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Apply forward migration — add google_sub, avatar_url, last_login_at to users and make hashed_password nullable."""
    op.add_column('users', sa.Column('google_sub', sa.String(length=255), nullable=True))
    op.add_column('users', sa.Column('avatar_url', sa.String(length=1024), nullable=True))
    op.add_column('users', sa.Column('last_login_at', sa.DateTime(), nullable=True))
    op.alter_column('users', 'hashed_password', existing_type=sa.String(length=255), nullable=True)
    op.create_index(op.f('ix_users_google_sub'), 'users', ['google_sub'], unique=True)


def downgrade() -> None:
    """Revert migration — drop google_sub index and columns, restore hashed_password non-nullable."""
    op.drop_index(op.f('ix_users_google_sub'), table_name='users')
    op.alter_column('users', 'hashed_password', existing_type=sa.String(length=255), nullable=False)
    op.drop_column('users', 'last_login_at')
    op.drop_column('users', 'avatar_url')
    op.drop_column('users', 'google_sub')
