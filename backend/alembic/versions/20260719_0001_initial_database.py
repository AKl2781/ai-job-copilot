"""Create users, candidate profiles, jobs, and analyses.

Revision ID: 20260719_0001
Revises:
Create Date: 2026-07-19
"""

from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = "20260719_0001"
down_revision: str | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def _json_type() -> sa.JSON:
    return sa.JSON().with_variant(postgresql.JSONB(), "postgresql")


def upgrade() -> None:
    op.create_table(
        "users",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("email", sa.String(length=320), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_users")),
        sa.UniqueConstraint("email", name=op.f("uq_users_email")),
    )

    op.create_table(
        "candidate_profiles",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("user_id", sa.Uuid(), nullable=False),
        sa.Column("name", sa.String(length=200), nullable=False),
        sa.Column("target_role", sa.String(length=200), nullable=True),
        sa.Column("summary", sa.Text(), nullable=True),
        sa.Column("skills", _json_type(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
        sa.ForeignKeyConstraint(
            ["user_id"],
            ["users.id"],
            name=op.f("fk_candidate_profiles_user_id_users"),
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_candidate_profiles")),
    )
    op.create_index(op.f("ix_candidate_profiles_user_id"), "candidate_profiles", ["user_id"])

    op.create_table(
        "jobs",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("user_id", sa.Uuid(), nullable=False),
        sa.Column("title", sa.String(length=500), nullable=False),
        sa.Column("company", sa.String(length=300), nullable=True),
        sa.Column("description", sa.Text(), nullable=False),
        sa.Column("source_url", sa.String(length=2048), nullable=True),
        sa.Column("source_type", sa.String(length=50), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
        sa.ForeignKeyConstraint(
            ["user_id"],
            ["users.id"],
            name=op.f("fk_jobs_user_id_users"),
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_jobs")),
    )
    op.create_index(op.f("ix_jobs_user_id"), "jobs", ["user_id"])

    op.create_table(
        "analyses",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("user_id", sa.Uuid(), nullable=False),
        sa.Column("job_id", sa.Uuid(), nullable=False),
        sa.Column("candidate_profile_id", sa.Uuid(), nullable=False),
        sa.Column("status", sa.String(length=50), nullable=False),
        sa.Column("score", sa.Integer(), nullable=True),
        sa.Column("result_json", _json_type(), nullable=False),
        sa.Column("scoring_version", sa.String(length=100), nullable=True),
        sa.Column("prompt_version", sa.String(length=100), nullable=True),
        sa.Column("model_provider", sa.String(length=100), nullable=True),
        sa.Column("model_name", sa.String(length=200), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
        sa.CheckConstraint(
            "score IS NULL OR (score >= 0 AND score <= 100)",
            name=op.f("ck_analyses_score_range"),
        ),
        sa.ForeignKeyConstraint(
            ["candidate_profile_id"],
            ["candidate_profiles.id"],
            name=op.f("fk_analyses_candidate_profile_id_candidate_profiles"),
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["job_id"],
            ["jobs.id"],
            name=op.f("fk_analyses_job_id_jobs"),
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["user_id"],
            ["users.id"],
            name=op.f("fk_analyses_user_id_users"),
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_analyses")),
    )
    op.create_index(op.f("ix_analyses_candidate_profile_id"), "analyses", ["candidate_profile_id"])
    op.create_index(op.f("ix_analyses_job_id"), "analyses", ["job_id"])
    op.create_index(op.f("ix_analyses_status"), "analyses", ["status"])
    op.create_index(op.f("ix_analyses_user_id"), "analyses", ["user_id"])


def downgrade() -> None:
    op.drop_index(op.f("ix_analyses_user_id"), table_name="analyses")
    op.drop_index(op.f("ix_analyses_status"), table_name="analyses")
    op.drop_index(op.f("ix_analyses_job_id"), table_name="analyses")
    op.drop_index(op.f("ix_analyses_candidate_profile_id"), table_name="analyses")
    op.drop_table("analyses")

    op.drop_index(op.f("ix_jobs_user_id"), table_name="jobs")
    op.drop_table("jobs")

    op.drop_index(op.f("ix_candidate_profiles_user_id"), table_name="candidate_profiles")
    op.drop_table("candidate_profiles")

    op.drop_table("users")
