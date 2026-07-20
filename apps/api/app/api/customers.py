"""Customer list + detail controllers (thin HTTP layer)."""

from __future__ import annotations

from typing import Literal

from fastapi import APIRouter, Depends, HTTPException, Query

from app.core.config import settings
from app.core.timeutil import current_month_bounds
from app.repositories.customer_repository import (
    SqlCustomerRepository,
    get_customer_repository,
)
from app.schemas.common import Page
from app.schemas.customer import CustomerDetail, CustomerSummary
from app.services.customer_service import to_detail, to_summary

router = APIRouter(prefix="/customers", tags=["customers"])


@router.get("", response_model=Page[CustomerSummary])
def list_customers(
    search: str | None = Query(default=None, description="matches name or customer id"),
    plan: str | None = Query(default=None, description="filter by plan id"),
    sort: Literal["tenure", "avg_gb", "contract_end_date"] = "contract_end_date",
    order: Literal["asc", "desc"] = "asc",
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    expiring: bool = Query(default=False, description="only contracts ending this calendar month"),
    # Upper bounds keep pathological ints from reaching the DB driver (OverflowError → 500); the
    # values are generous vs any real tenure (months) / monthly usage (GB).
    tenure_min: int | None = Query(default=None, ge=0, le=1200, description="min tenure in months"),
    tenure_max: int | None = Query(default=None, ge=0, le=1200, description="max tenure in months"),
    usage_min: int | None = Query(
        default=None, ge=0, le=1_000_000, description="min avg usage (GB)"
    ),
    usage_max: int | None = Query(
        default=None, ge=0, le=1_000_000, description="max avg usage (GB)"
    ),
    repo: SqlCustomerRepository = Depends(get_customer_repository),
) -> Page[CustomerSummary]:
    # "Expiring" reuses the dashboard's calendar-month window so the list matches the tile counts.
    expiring_from, expiring_to = (
        current_month_bounds(settings.app_timezone) if expiring else (None, None)
    )
    rows, total = repo.list(
        search=search,
        plan=plan,
        sort=sort,
        order=order,
        page=page,
        page_size=page_size,
        expiring_from=expiring_from,
        expiring_to=expiring_to,
        tenure_min=tenure_min,
        tenure_max=tenure_max,
        usage_min=usage_min,
        usage_max=usage_max,
    )
    return Page(
        data=[to_summary(c) for c in rows],
        page=page,
        page_size=page_size,
        total=total,
    )


@router.get("/{customer_id}", response_model=CustomerDetail)
def get_customer(
    customer_id: str,
    repo: SqlCustomerRepository = Depends(get_customer_repository),
) -> CustomerDetail:
    customer = repo.get(customer_id)
    if customer is None:
        raise HTTPException(status_code=404, detail="Customer not found")
    return to_detail(customer)
