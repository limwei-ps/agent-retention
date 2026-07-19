"""SQLAlchemy engine, session factory, declarative base, and FastAPI DB dependency.

Models/repositories land in the next chunk; this establishes the wiring so services
and routers can depend on `get_db` via FastAPI `Depends()`.
"""

from __future__ import annotations

from collections.abc import Iterator

from sqlalchemy import create_engine, event
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

from app.core.config import settings

_is_sqlite = settings.database_url.startswith("sqlite")
# check_same_thread=False so the SQLite connection can be shared across threads
# (FastAPI runs sync endpoints in a threadpool).
_connect_args = {"check_same_thread": False} if _is_sqlite else {}

engine = create_engine(settings.database_url, connect_args=_connect_args)
SessionLocal = sessionmaker(bind=engine, autocommit=False, autoflush=False)


if _is_sqlite:

    @event.listens_for(engine, "connect")
    def _sqlite_pragmas(dbapi_conn, _record):  # noqa: ANN001, ANN202
        # WAL lets readers (list/detail) proceed while a writer commits; busy_timeout makes writer
        # serialization tunable rather than an immediate "database is locked" (spec §4.5).
        cursor = dbapi_conn.cursor()
        cursor.execute("PRAGMA journal_mode=WAL")
        cursor.execute("PRAGMA busy_timeout=5000")
        cursor.close()


class Base(DeclarativeBase):
    """Declarative base for all ORM models."""


def get_db() -> Iterator[Session]:
    """Yield a DB session, closing it after the request (DI target)."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def get_session_factory() -> sessionmaker[Session]:
    """Return the session factory itself (DI target).

    Background tasks outlive the request session, so they must open their own sessions rather than
    reuse the request-scoped one. Exposing the factory via DI lets tests point bulk workers at a
    temp-file engine (see conftest `bulk_client`).
    """
    return SessionLocal
