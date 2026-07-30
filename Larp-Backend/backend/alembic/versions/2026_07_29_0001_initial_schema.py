"""Initial database schema with optimized indexes.

Revision ID: 0001_initial_schema
Revises: 
Create Date: 2026-07-29 18:30:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '0001_initial_schema'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Apply forward migration — create all 7 core tables and indexes."""
    # ── 1. Users ────────────────────────────────────────────────────────
    op.create_table(
        'users',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('email', sa.String(length=255), nullable=False),
        sa.Column('hashed_password', sa.String(length=255), nullable=False),
        sa.Column('full_name', sa.String(length=255), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default=sa.text('true')),
        sa.Column('is_superuser', sa.Boolean(), nullable=False, server_default=sa.text('false')),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.text('now()'), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_users_email'), 'users', ['email'], unique=True)

    # ── 2. ResearchJobs ─────────────────────────────────────────────────
    op.create_table(
        'research_jobs',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('user_id', sa.UUID(), nullable=False),
        sa.Column('title', sa.String(length=500), nullable=False),
        sa.Column('query', sa.Text(), nullable=False),
        sa.Column('status', sa.String(length=50), nullable=False, server_default='pending'),
        sa.Column('depth', sa.String(length=50), nullable=False, server_default='standard'),
        sa.Column('config', sa.JSON(), nullable=True),
        sa.Column('error_message', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_research_jobs_user_id'), 'research_jobs', ['user_id'], unique=False)
    op.create_index(op.f('ix_research_jobs_status'), 'research_jobs', ['status'], unique=False)
    op.create_index('ix_research_jobs_user_created', 'research_jobs', ['user_id', 'created_at'], unique=False)
    op.create_index('ix_research_jobs_user_status', 'research_jobs', ['user_id', 'status'], unique=False)
    op.create_index('ix_research_jobs_status_created', 'research_jobs', ['status', 'created_at'], unique=False)

    # ── 3. ResearchReports ──────────────────────────────────────────────
    op.create_table(
        'research_reports',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('job_id', sa.UUID(), nullable=False),
        sa.Column('user_id', sa.UUID(), nullable=False),
        sa.Column('title', sa.String(length=500), nullable=False),
        sa.Column('summary', sa.Text(), nullable=False),
        sa.Column('content_markdown', sa.Text(), nullable=False),
        sa.Column('key_findings', sa.JSON(), nullable=True),
        sa.Column('word_count', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['job_id'], ['research_jobs.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('job_id')
    )
    op.create_index(op.f('ix_research_reports_job_id'), 'research_reports', ['job_id'], unique=True)
    op.create_index(op.f('ix_research_reports_user_id'), 'research_reports', ['user_id'], unique=False)

    # ── 4. ResearchSources ──────────────────────────────────────────────
    op.create_table(
        'research_sources',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('job_id', sa.UUID(), nullable=False),
        sa.Column('url', sa.String(length=2048), nullable=False),
        sa.Column('title', sa.String(length=500), nullable=True),
        sa.Column('domain', sa.String(length=255), nullable=True),
        sa.Column('snippet', sa.Text(), nullable=True),
        sa.Column('relevance_score', sa.Float(), nullable=True),
        sa.Column('raw_content', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['job_id'], ['research_jobs.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_research_sources_job_id'), 'research_sources', ['job_id'], unique=False)
    op.create_index(op.f('ix_research_sources_domain'), 'research_sources', ['domain'], unique=False)
    op.create_index('ix_research_sources_job_relevance', 'research_sources', ['job_id', 'relevance_score'], unique=False)

    # ── 5. ResearchHistory ──────────────────────────────────────────────
    op.create_table(
        'research_history',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('user_id', sa.UUID(), nullable=False),
        sa.Column('job_id', sa.UUID(), nullable=True),
        sa.Column('action', sa.String(length=100), nullable=False),
        sa.Column('details', sa.JSON(), nullable=True),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['job_id'], ['research_jobs.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_research_history_user_id'), 'research_history', ['user_id'], unique=False)
    op.create_index(op.f('ix_research_history_job_id'), 'research_history', ['job_id'], unique=False)
    op.create_index(op.f('ix_research_history_action'), 'research_history', ['action'], unique=False)
    op.create_index('ix_research_history_user_created', 'research_history', ['user_id', 'created_at'], unique=False)

    # ── 6. Payments ─────────────────────────────────────────────────────
    op.create_table(
        'payments',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('user_id', sa.UUID(), nullable=False),
        sa.Column('stripe_payment_id', sa.String(length=255), nullable=True),
        sa.Column('amount_cents', sa.Integer(), nullable=False),
        sa.Column('currency', sa.String(length=3), nullable=False, server_default='usd'),
        sa.Column('status', sa.String(length=50), nullable=False, server_default='pending'),
        sa.Column('credits_awarded', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('payment_method', sa.String(length=50), nullable=True),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_payments_user_id'), 'payments', ['user_id'], unique=False)
    op.create_index(op.f('ix_payments_stripe_payment_id'), 'payments', ['stripe_payment_id'], unique=True)
    op.create_index(op.f('ix_payments_status'), 'payments', ['status'], unique=False)

    # ── 7. AgentExecutionLogs ───────────────────────────────────────────
    op.create_table(
        'agent_execution_logs',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('job_id', sa.UUID(), nullable=False),
        sa.Column('agent_name', sa.String(length=100), nullable=False),
        sa.Column('step_number', sa.Integer(), nullable=False),
        sa.Column('status', sa.String(length=50), nullable=False, server_default='running'),
        sa.Column('input_data', sa.JSON(), nullable=True),
        sa.Column('output_data', sa.JSON(), nullable=True),
        sa.Column('execution_time_ms', sa.Integer(), nullable=True),
        sa.Column('error_message', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['job_id'], ['research_jobs.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_agent_execution_logs_job_id'), 'agent_execution_logs', ['job_id'], unique=False)
    op.create_index(op.f('ix_agent_execution_logs_agent_name'), 'agent_execution_logs', ['agent_name'], unique=False)
    op.create_index(op.f('ix_agent_execution_logs_status'), 'agent_execution_logs', ['status'], unique=False)
    op.create_index('ix_agent_execution_logs_job_step', 'agent_execution_logs', ['job_id', 'step_number'], unique=False)
    op.create_index('ix_agent_execution_logs_job_status', 'agent_execution_logs', ['job_id', 'status'], unique=False)


def downgrade() -> None:
    """Revert migration — drop tables in reverse dependency order."""
    op.drop_table('agent_execution_logs')
    op.drop_table('payments')
    op.drop_table('research_history')
    op.drop_table('research_sources')
    op.drop_table('research_reports')
    op.drop_table('research_jobs')
    op.drop_table('users')
