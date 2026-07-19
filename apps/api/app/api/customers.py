"""Customer list + detail controllers (thin HTTP layer)."""

from __future__ import annotations

from typing import Literal

from fastapi import APIRouter, Depends, HTTPException, Query

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
    repo: SqlCustomerRepository = Depends(get_customer_repository),
) -> Page[CustomerSummary]:
    rows, total = repo.list(
        search=search, plan=plan, sort=sort, order=order, page=page, page_size=page_size
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
