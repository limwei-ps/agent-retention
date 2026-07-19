"""Dashboard summary DTOs (spec §3)."""

from __future__ import annotations

from pydantic import BaseModel

from app.schemas.plan import PlanRef


class TierCount(BaseModel):
    plan: PlanRef
    count: int


class DashboardSummary(BaseModel):
    expiring_this_month: int  # total across all tiers
    by_tier: list[TierCount]
