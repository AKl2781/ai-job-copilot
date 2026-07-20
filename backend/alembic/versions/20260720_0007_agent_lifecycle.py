"""Add active Agent Run idempotency protection.

Revision ID: 20260720_0007
Revises: 20260720_0006
Create Date: 2026-07-20
"""

from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa

revision: str = "20260720_0007"
down_revision: str | None = "20260720_0006"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # Preserve the newest legacy active run and release older duplicates before
    # installing the concurrency guard.
    op.execute(sa.text("""
        UPDATE agent_runs
        SET status = 'failed',
            error_message = 'superseded by a newer active agent run'
        WHERE id IN (
            SELECT id FROM (
                SELECT id,
                       ROW_NUMBER() OVER (
                           PARTITION BY user_id, job_id
                           ORDER BY created_at DESC, id DESC
                       ) AS active_rank
                FROM agent_runs
                WHERE status IN ('pending', 'running')
            ) AS ranked_active_runs
            WHERE active_rank > 1
        )
    """))
    op.create_index(
        "uq_agent_runs_active_user_job",
        "agent_runs",
        ["user_id", "job_id"],
        unique=True,
        postgresql_where=sa.text("status IN ('pending', 'running')"),
        sqlite_where=sa.text("status IN ('pending', 'running')"),
    )


def downgrade() -> None:
    op.drop_index("uq_agent_runs_active_user_job", table_name="agent_runs")
