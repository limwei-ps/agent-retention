"""Offer-ladder DTOs (spec §1.3)."""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel

from app.schemas.plan import PlanRef

OfferType = Literal["retain", "value_upgrade", "upsell"]


class OfferRung(BaseModel):
    type: OfferType
    target_plan: PlanRef
    monthly_price: int
    term_months: int
    vs_current_delta: int  # signed RM change vs the customer's current monthly price
    headline: str


class OfferLadder(BaseModel):
    rungs: list[OfferRung]
    recommended: OfferType  # which rung the pitch should lead with
