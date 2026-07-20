"""Health check controller."""

from __future__ import annotations

from fastapi import APIRouter
from pydantic import BaseModel

from app.core.budget import BUDGET
from app.core.config import settings

router = APIRouter(tags=["health"])


class HealthResponse(BaseModel):
    status: str
    llm_mode: str
    daily_budget_usd: float
    daily_spent_usd: float
    budget_ok: bool


@router.get("/health", response_model=HealthResponse)
def health() -> HealthResponse:
    """Liveness probe; reports the active LLM mode (mock|gemini) and the daily spend-cap state."""
    b = BUDGET.snapshot()
    return HealthResponse(
        status="ok",
        llm_mode=settings.llm_mode,
        daily_budget_usd=b.limit_usd,
        daily_spent_usd=b.spent_usd,
        budget_ok=b.ok,
    )
