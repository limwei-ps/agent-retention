"""Customer data-access behind an interface, injected via FastAPI `Depends()`.

The `CustomerRepository` Protocol lets services/routers depend on the abstraction (and tests swap in
a fake), while `SqlCustomerRepository` is the SQLAlchemy implementation.
"""

from __future__ import annotations

from datetime import date
from typing import Protocol

from fastapi import Depends
from sqlalchemy import func, select
from sqlalchemy.orm import Session, defer, selectinload

from app.db.session import get_db
from app.models.customer import Customer
from app.models.pitch import Pitch

# Allowed sort keys → model columns (whitelist; never interpolate user input into SQL).
_SORT_COLUMNS = {
    "tenure": Customer.tenure_months,
    "avg_gb": Customer.avg_monthly_gb,
    "contract_end_date": Customer.contract_end_date,
}


class CustomerRepository(Protocol):
    def list(
        self,
        *,
        search: str | None,
        plan: str | None,
        sort: str,
        order: str,
        page: int,
        page_size: int,
        expiring_from: date | None = None,
        expiring_to: date | None = None,
        tenure_min: int | None = None,
        tenure_max: int | None = None,
        usage_min: int | None = None,
        usage_max: int | None = None,
    ) -> tuple[list[Customer], int]: ...

    def get(self, customer_id: str) -> Customer | None: ...

    def count_expiring_by_tier(self, start: date, end: date) -> dict[str, int]: ...


class SqlCustomerRepository:
    def __init__(self, db: Session) -> None:
        self._db = db

    def list(
        self,
        *,
        search: str | None,
        plan: str | None,
        sort: str,
        order: str,
        page: int,
        page_size: int,
        expiring_from: date | None = None,
        expiring_to: date | None = None,
        tenure_min: int | None = None,
        tenure_max: int | None = None,
        usage_min: int | None = None,
        usage_max: int | None = None,
    ) -> tuple[list[Customer], int]:
        stmt = select(Customer)
        if search:
            like = f"%{search}%"
            stmt = stmt.where(Customer.name.ilike(like) | Customer.id.ilike(like))
        if plan:
            stmt = stmt.where(Customer.current_plan_id == plan)
        if expiring_from is not None and expiring_to is not None:
            stmt = stmt.where(
                Customer.contract_end_date >= expiring_from,
                Customer.contract_end_date <= expiring_to,
            )
        # Tenure / usage range filters (usage = the derived avg_monthly_gb scalar, indexed for this).
        if tenure_min is not None:
            stmt = stmt.where(Customer.tenure_months >= tenure_min)
        if tenure_max is not None:
            stmt = stmt.where(Customer.tenure_months <= tenure_max)
        if usage_min is not None:
            stmt = stmt.where(Customer.avg_monthly_gb >= usage_min)
        if usage_max is not None:
            stmt = stmt.where(Customer.avg_monthly_gb <= usage_max)

        # Count over the filtered predicate only (before options/order/paging).
        total = self._db.scalar(select(func.count()).select_from(stmt.subquery())) or 0

        # Avoid N+1: batch-load the latest-pitch status for the whole page in one query,
        # and skip the JSON usage_history the summary never reads.
        stmt = stmt.options(
            selectinload(Customer.pitches).load_only(Pitch.status, Pitch.created_at),
            defer(Customer.usage_history),
        )

        # Sort by the requested column + a stable `id` tiebreaker so tied values don't
        # shuffle rows across pages (OFFSET pagination needs a total ordering).
        primary = _SORT_COLUMNS.get(sort, Customer.contract_end_date)

        def _dir(col):  # noqa: ANN001, ANN202
            return col.desc() if order == "desc" else col.asc()

        stmt = stmt.order_by(_dir(primary), _dir(Customer.id))
        stmt = stmt.offset((page - 1) * page_size).limit(page_size)

        rows = list(self._db.scalars(stmt).all())
        return rows, total

    def get(self, customer_id: str) -> Customer | None:
        return self._db.get(Customer, customer_id)

    def count_expiring_by_tier(self, start: date, end: date) -> dict[str, int]:
        stmt = (
            select(Customer.current_plan_id, func.count())
            .where(Customer.contract_end_date >= start, Customer.contract_end_date <= end)
            .group_by(Customer.current_plan_id)
        )
        return {plan_id: count for plan_id, count in self._db.execute(stmt).all()}


def get_customer_repository(db: Session = Depends(get_db)) -> SqlCustomerRepository:
    return SqlCustomerRepository(db)
