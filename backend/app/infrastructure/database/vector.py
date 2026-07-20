"""Cross-dialect vector column support for pgvector and SQLite tests."""

from sqlalchemy import JSON
from sqlalchemy.engine import Dialect
from sqlalchemy.types import TypeDecorator, TypeEngine
from pgvector.sqlalchemy import Vector

BGE_M3_DIMENSION = 1024


class EmbeddingVector(TypeDecorator[list[float]]):
    """Use pgvector on PostgreSQL and JSON storage on test databases."""

    impl = JSON
    cache_ok = True

    def __init__(self, dimensions: int = BGE_M3_DIMENSION) -> None:
        super().__init__()
        self.dimensions = dimensions

    def load_dialect_impl(self, dialect: Dialect) -> TypeEngine[object]:
        if dialect.name == "postgresql":
            return dialect.type_descriptor(Vector(self.dimensions))
        return dialect.type_descriptor(JSON())
