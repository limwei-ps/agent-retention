"""Dashboard summary controller — customers expiring this month, by plan tier."""

from __future__ import annotations

from fastapi import APIRouter, Depends

from app.core.catalog import CATALOG
from app.core.config import settings
from app.core.timeutil import current_month_bounds
from app.repositories.customer_repository import (
    SqlCustomerRepository,
    get_customer_repository,
)
from app.schemas.dashboard import DashboardSummary, TierCount
from app.schemas.plan import PlanRef

router = APIRouter(prefix="/dashboard", tags=["dashboard"])


@router.get("/summary", response_model=DashboardSummary)
def summary(
    repo: SqlCustomerRepository = Depends(get_customer_repository),
) -> DashboardSummary:
    start, end = current_month_bounds(settings.app_timezone)
    counts = repo.count_expiring_by_tier(start, end)

    by_tier = [
        TierCount(
            plan=PlanRef(id=p.id, name=p.name, speed_mbps=p.speed_mbps, price_myr=p.price_myr),
            count=counts.get(p.id, 0),
        )
        for p in CATALOG
    ]
    return DashboardSummary(
        expiring_this_month=sum(t.count for t in by_tier),
        by_tier=by_tier,
    )
