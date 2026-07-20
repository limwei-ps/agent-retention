"""FastAPI application factory.

Routers mount under `/api` (see spec §3). On startup we create tables and seed fake data if the DB
is empty (seed-on-boot; Cloud Run's filesystem is ephemeral).
"""

from __future__ import annotations

from contextlib import asynccontextmanager

from fastapi import FastAPI

from app import __version__
from app.ai.single_flight import SingleFlight
from app.api import customers, dashboard, health, metrics, pitches
from app.core.config import settings
from app.core.logging import configure_logging
from app.core.tracing import TraceIdMiddleware
from app import models  # noqa: F401  (import models so Base.metadata sees every table)
from app.db.seed import seed_if_empty
from app.db.session import Base, SessionLocal, engine
from app.services.batch_registry import BatchRegistry


@asynccontextmanager
async def lifespan(app: FastAPI):
    Base.metadata.create_all(bind=engine)
    with SessionLocal() as db:
        seed_if_empty(db)
    yield


def create_app() -> FastAPI:
    configure_logging()
    app = FastAPI(title=settings.app_name, version=__version__, lifespan=lifespan)

    # Correlation trace id on every request + log line (X-Trace-Id header out).
    app.add_middleware(TraceIdMiddleware)

    # Process-wide registries (built here, not in lifespan, so tests that skip lifespan still
    # have them on app.state).
    app.state.single_flight = SingleFlight()
    app.state.batch_registry = BatchRegistry()

    app.include_router(health.router, prefix="/api")
    app.include_router(metrics.router, prefix="/api")
    app.include_router(customers.router, prefix="/api")
    app.include_router(dashboard.router, prefix="/api")
    app.include_router(pitches.router, prefix="/api")

    return app


app = create_app()
