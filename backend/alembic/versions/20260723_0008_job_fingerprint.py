"""Add user-scoped job fingerprints.

Revision ID: 20260723_0008
Revises: 20260720_0007
Create Date: 2026-07-23
"""

from collections.abc import Sequence

from alembic import context, op
import sqlalchemy as sa

from backend.app.application.job_fingerprint import generate_job_fingerprint

revision: str = "20260723_0008"
down_revision: str | None = "20260720_0007"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    with op.batch_alter_table("jobs") as batch_op:
        batch_op.add_column(
            sa.Column("job_fingerprint", sa.String(length=64), nullable=True)
        )

    jobs = sa.table(
        "jobs",
        sa.column("id", sa.Uuid()),
        sa.column("user_id", sa.Uuid()),
        sa.column("title", sa.String()),
        sa.column("company", sa.String()),
        sa.column("description", sa.Text()),
        sa.column("source_url", sa.String()),
        sa.column("created_at", sa.DateTime(timezone=True)),
        sa.column("job_fingerprint", sa.String()),
    )
    if not context.is_offline_mode():
        connection = op.get_bind()
        rows = connection.execute(
            sa.select(
                jobs.c.id,
                jobs.c.user_id,
                jobs.c.title,
                jobs.c.company,
                jobs.c.description,
                jobs.c.source_url,
            ).order_by(jobs.c.created_at, jobs.c.id)
        )
        claimed: set[tuple[object, str]] = set()
        for row in rows:
            fingerprint = generate_job_fingerprint(
                source_url=row.source_url,
                title=row.title,
                company=row.company,
                description=row.description,
            )
            identity = (row.user_id, fingerprint)
            if identity in claimed:
                continue
            claimed.add(identity)
            connection.execute(
                jobs.update()
                .where(jobs.c.id == row.id)
                .values(job_fingerprint=fingerprint)
            )

    with op.batch_alter_table("jobs") as batch_op:
        batch_op.create_index(
            op.f("ix_jobs_job_fingerprint"), ["job_fingerprint"], unique=False
        )
        batch_op.create_unique_constraint(
            "uq_jobs_user_id_job_fingerprint",
            ["user_id", "job_fingerprint"],
        )


def downgrade() -> None:
    with op.batch_alter_table("jobs") as batch_op:
        batch_op.drop_constraint(
            "uq_jobs_user_id_job_fingerprint", type_="unique"
        )
        batch_op.drop_index(op.f("ix_jobs_job_fingerprint"))
        batch_op.drop_column("job_fingerprint")
