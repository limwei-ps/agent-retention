"""FastAPI application factory.

Routers mount under `/api` (see spec §3). Business routers (customers, pitches,
dashboard) are added in the next chunk.
"""

from __future__ import annotations

from fastapi import FastAPI

from app import __version__
from app.api import health
from app.core.config import settings
from app.core.logging import configure_logging


def create_app() -> FastAPI:
    configure_logging()
    app = FastAPI(title=settings.app_name, version=__version__)

    app.include_router(health.router, prefix="/api")

    return app


app = create_app()
