"""Health check controller."""

from __future__ import annotations

from fastapi import APIRouter
from pydantic import BaseModel

from app.core.config import settings

router = APIRouter(tags=["health"])


class HealthResponse(BaseModel):
    status: str
    llm_mode: str


@router.get("/health", response_model=HealthResponse)
def health() -> HealthResponse:
    """Liveness probe; also reports the active LLM mode (mock|gemini)."""
    return HealthResponse(status="ok", llm_mode=settings.llm_mode)
