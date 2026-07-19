"""FastAPI application factory.

Routers mount under `/api` (see spec §3). On startup we create tables and seed fake data if the DB
is empty (seed-on-boot; Cloud Run's filesystem is ephemeral).
"""

from __future__ import annotations

from contextlib import asynccontextmanager

from fastapi import FastAPI

from app import __version__
from app.api import customers, dashboard, health
from app.core.config import settings
from app.core.logging import configure_logging
from app import models  # noqa: F401  (import models so Base.metadata sees every table)
from app.db.seed import seed_if_empty
from app.db.session import Base, SessionLocal, engine


@asynccontextmanager
async def lifespan(app: FastAPI):
    Base.metadata.create_all(bind=engine)
    with SessionLocal() as db:
        seed_if_empty(db)
    yield


def create_app() -> FastAPI:
    configure_logging()
    app = FastAPI(title=settings.app_name, version=__version__, lifespan=lifespan)

    app.include_router(health.router, prefix="/api")
    app.include_router(customers.router, prefix="/api")
    app.include_router(dashboard.router, prefix="/api")

    return app


app = create_app()
