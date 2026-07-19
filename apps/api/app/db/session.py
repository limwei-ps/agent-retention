"""SQLAlchemy engine, session factory, declarative base, and FastAPI DB dependency.

Models/repositories land in the next chunk; this establishes the wiring so services
and routers can depend on `get_db` via FastAPI `Depends()`.
"""

from __future__ import annotations

from collections.abc import Iterator

from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

from app.core.config import settings

# check_same_thread=False so the SQLite connection can be shared across threads
# (FastAPI runs sync endpoints in a threadpool).
_connect_args = {"check_same_thread": False} if settings.database_url.startswith("sqlite") else {}

engine = create_engine(settings.database_url, connect_args=_connect_args)
SessionLocal = sessionmaker(bind=engine, autocommit=False, autoflush=False)


class Base(DeclarativeBase):
    """Declarative base for all ORM models."""


def get_db() -> Iterator[Session]:
    """Yield a DB session, closing it after the request (DI target)."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
