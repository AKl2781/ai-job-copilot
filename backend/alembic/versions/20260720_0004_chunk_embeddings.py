"""Enable pgvector and add chunk embeddings.

Revision ID: 20260720_0004
Revises: 20260720_0003
Create Date: 2026-07-20
"""

from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa
from pgvector.sqlalchemy import Vector

from backend.app.infrastructure.database.vector import BGE_M3_DIMENSION

revision: str = "20260720_0004"
down_revision: str | None = "20260720_0003"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    dialect_name = op.get_context().dialect.name
    if dialect_name == "postgresql":
        op.execute("CREATE EXTENSION IF NOT EXISTS vector")
        embedding_type: sa.types.TypeEngine[object] = Vector(BGE_M3_DIMENSION)
    else:
        embedding_type = sa.JSON()
    op.add_column(
        "document_chunks",
        sa.Column("embedding", embedding_type, nullable=True),
    )


def downgrade() -> None:
    op.drop_column("document_chunks", "embedding")
