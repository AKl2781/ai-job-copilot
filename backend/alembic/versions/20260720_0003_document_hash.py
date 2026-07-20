"""Add user-scoped document content hashes.

Revision ID: 20260720_0003
Revises: 20260720_0002
Create Date: 2026-07-20
"""

from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa

revision: str = "20260720_0003"
down_revision: str | None = "20260720_0002"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    with op.batch_alter_table("documents") as batch_op:
        batch_op.add_column(sa.Column("file_hash", sa.String(length=64), nullable=True))
        batch_op.create_unique_constraint(
            op.f("uq_documents_user_id"),
            ["user_id", "file_hash"],
        )


def downgrade() -> None:
    with op.batch_alter_table("documents") as batch_op:
        batch_op.drop_constraint(op.f("uq_documents_user_id"), type_="unique")
        batch_op.drop_column("file_hash")
