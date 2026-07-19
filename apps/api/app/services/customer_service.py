"""Maps Customer ORM rows to API DTOs (keeps routers thin)."""

from __future__ import annotations

from app.core.catalog import get_plan
from app.models.customer import Customer
from app.schemas.customer import CustomerDetail, CustomerSummary, UsagePoint
from app.schemas.pitch import PitchRead
from app.schemas.plan import PlanRef
from app.services.offer_service import build_offer_ladder


def _plan_ref(plan_id: str) -> PlanRef:
    plan = get_plan(plan_id)
    return PlanRef(id=plan.id, name=plan.name, speed_mbps=plan.speed_mbps, price_myr=plan.price_myr)


def _latest_pitch_status(customer: Customer) -> str | None:
    # Summary needs only the status. Reading just `.status` keeps the list query's
    # `load_only(status, created_at)` optimization intact (no extra column loads).
    return customer.pitches[0].status.value if customer.pitches else None


def _latest_pitch(customer: Customer) -> PitchRead | None:
    # Detail needs the full pitch. `pitches` is ordered created_at desc by the relationship.
    return PitchRead.model_validate(customer.pitches[0]) if customer.pitches else None


def to_summary(customer: Customer) -> CustomerSummary:
    return CustomerSummary(
        id=customer.id,
        name=customer.name,
        current_plan=_plan_ref(customer.current_plan_id),
        tenure_months=customer.tenure_months,
        avg_monthly_gb=customer.avg_monthly_gb,
        contract_end_date=customer.contract_end_date,
        latest_pitch_status=_latest_pitch_status(customer),
    )


def to_detail(customer: Customer) -> CustomerDetail:
    return CustomerDetail(
        id=customer.id,
        name=customer.name,
        email=customer.email,
        phone=customer.phone,
        region=customer.region,
        current_plan=_plan_ref(customer.current_plan_id),
        monthly_price=customer.monthly_price,
        tenure_months=customer.tenure_months,
        contract_end_date=customer.contract_end_date,
        usage_archetype=customer.usage_archetype,
        avg_monthly_gb=customer.avg_monthly_gb,
        last_month_gb=customer.last_month_gb,
        usage_history=[UsagePoint(**point) for point in customer.usage_history],
        offer_ladder=build_offer_ladder(
            customer.current_plan_id,
            customer.monthly_price,
            customer.tenure_months,
            customer.usage_archetype,
        ),
        latest_pitch=_latest_pitch(customer),
    )
