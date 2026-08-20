"""Add Google auth fields to users table.

Revision ID: 0003
Revises: 2026_08_03_0002
Create Date: 2026-08-20

Adds:
    - google_sub (VARCHAR 255, unique, indexed, nullable)
    - avatar_url (VARCHAR 512, nullable)
    - last_login_at (TIMESTAMP WITH TIME ZONE, nullable)
    - Makes hashed_password nullable for Google-only users
"""

from alembic import op
import sqlalchemy as sa

# revision identifiers
revision = "2026_08_20_0003"
down_revision = "0002_add_cancelled_at"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("users", sa.Column("google_sub", sa.String(255), nullable=True))
    op.add_column("users", sa.Column("avatar_url", sa.String(512), nullable=True))
    op.add_column(
        "users",
        sa.Column("last_login_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.create_unique_constraint("uq_users_google_sub", "users", ["google_sub"])
    op.create_index("ix_users_google_sub", "users", ["google_sub"])

    # Make hashed_password nullable for Google-only users
    op.alter_column(
        "users",
        "hashed_password",
        existing_type=sa.String(255),
        nullable=True,
    )


def downgrade() -> None:
    op.alter_column(
        "users",
        "hashed_password",
        existing_type=sa.String(255),
        nullable=False,
    )
    op.drop_index("ix_users_google_sub", table_name="users")
    op.drop_constraint("uq_users_google_sub", "users", type_="unique")
    op.drop_column("users", "last_login_at")
    op.drop_column("users", "avatar_url")
    op.drop_column("users", "google_sub")
