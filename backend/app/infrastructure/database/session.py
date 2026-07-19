"""Database engine and session construction."""

from collections.abc import Generator
from functools import lru_cache

from pydantic import ValidationError
from sqlalchemy import Engine, create_engine
from sqlalchemy.orm import Session, sessionmaker

from ...core.config import get_settings


class DatabaseConfigurationError(RuntimeError):
    """The database cannot be used until DATABASE_URL is configured."""


def create_database_engine(database_url: str | None = None) -> Engine:
    """Create an engine for an explicit URL or the configured database."""
    try:
        url = database_url if database_url is not None else get_settings().database_url
    except ValidationError as exc:
        raise DatabaseConfigurationError(
            "DATABASE_URL is not configured; set it before using database features."
        ) from exc
    return create_engine(url, pool_pre_ping=True)


def create_session_factory(engine: Engine) -> sessionmaker[Session]:
    """Create a SQLAlchemy 2.x session factory bound to an engine."""
    return sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)


@lru_cache
def _default_session_factory() -> sessionmaker[Session]:
    return create_session_factory(create_database_engine())


def get_db_session() -> Generator[Session, None, None]:
    """Yield one transactional session for future application dependencies."""
    session = _default_session_factory()()
    try:
        yield session
    finally:
        session.close()
