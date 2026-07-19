"""Customer DTOs — list summary and full detail (spec §1.2, §3)."""

from __future__ import annotations

from datetime import date

from pydantic import BaseModel

from app.schemas.offer import OfferLadder
from app.schemas.pitch import PitchRead
from app.schemas.plan import PlanRef


class UsagePoint(BaseModel):
    month: str  # "YYYY-MM"
    gb: int


class CustomerSummary(BaseModel):
    """Row shape for the customer list."""

    id: str
    name: str
    current_plan: PlanRef
    tenure_months: int
    avg_monthly_gb: int
    contract_end_date: date
    latest_pitch_status: str | None = None


class CustomerDetail(BaseModel):
    """Full detail: customer info + usage history + offer ladder + latest pitch."""

    id: str
    name: str
    email: str
    phone: str
    region: str
    current_plan: PlanRef
    monthly_price: int
    tenure_months: int
    contract_end_date: date
    usage_archetype: str
    avg_monthly_gb: int
    last_month_gb: int
    usage_history: list[UsagePoint]
    offer_ladder: OfferLadder
    latest_pitch: PitchRead | None = None
