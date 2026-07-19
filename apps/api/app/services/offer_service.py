"""Offer-ladder derivation — "retain while making additional profit" (spec §1.3).

Pure and deterministic: a function of the customer's plan, current spend, tenure, and usage
archetype + the fixed catalog. No DB, no I/O — so it's trivially unit-tested and safe to reuse in
the AI grounding layer (Day 3).
"""

from __future__ import annotations

from app.core.catalog import (
    RETAIN_DISCOUNT,
    RETAIN_DISCOUNT_TOP_TIER,
    TERM_MONTHS,
    UPSELL_PREMIUM_MYR,
    PlanTier,
    get_plan,
    next_tier,
)
from app.schemas.offer import OfferLadder, OfferRung, OfferType
from app.schemas.plan import PlanRef

# Long-tenure customers are loyal + price-sensitive → default to defending them.
HIGH_TENURE_MONTHS = 36


def _plan_ref(plan: PlanTier) -> PlanRef:
    return PlanRef(id=plan.id, name=plan.name, speed_mbps=plan.speed_mbps, price_myr=plan.price_myr)


def _retain_rung(current: PlanTier, monthly_price: int, *, deeper: bool) -> OfferRung:
    discount = RETAIN_DISCOUNT_TOP_TIER if deeper else RETAIN_DISCOUNT
    price = round(monthly_price * (1 - discount))
    pct = round(discount * 100)
    return OfferRung(
        type="retain",
        target_plan=_plan_ref(current),
        monthly_price=price,
        term_months=TERM_MONTHS,
        vs_current_delta=price - monthly_price,
        headline=f"{pct}% off your {current.name} plan for {TERM_MONTHS} months",
    )


def _value_upgrade_rung(upgrade: PlanTier, monthly_price: int) -> OfferRung:
    # Same wallet, more speed: hold price at (or near) current spend.
    price = monthly_price
    return OfferRung(
        type="value_upgrade",
        target_plan=_plan_ref(upgrade),
        monthly_price=price,
        term_months=TERM_MONTHS,
        vs_current_delta=price - monthly_price,
        headline=f"Upgrade to {upgrade.name} at your current price for {TERM_MONTHS} months",
    )


def _upsell_rung(upgrade: PlanTier, monthly_price: int) -> OfferRung:
    # Higher speed at a premium, still kept below list price to stay attractive.
    price = min(monthly_price + UPSELL_PREMIUM_MYR, upgrade.price_myr)
    return OfferRung(
        type="upsell",
        target_plan=_plan_ref(upgrade),
        monthly_price=price,
        term_months=TERM_MONTHS,
        vs_current_delta=price - monthly_price,
        headline=f"Step up to {upgrade.name} for +RM{price - monthly_price}/mo",
    )


def _recommend(archetype: str, tenure_months: int, has_upgrade: bool) -> OfferType:
    if not has_upgrade:
        return "retain"
    if tenure_months >= HIGH_TENURE_MONTHS:
        return "retain"
    if archetype == "heavy":
        return "upsell"
    if archetype == "climbing":
        return "value_upgrade"
    return "retain"  # flat_low (and any unknown archetype) → defend on price


def build_offer_ladder(
    plan_id: str,
    monthly_price: int,
    tenure_months: int,
    archetype: str,
) -> OfferLadder:
    """Build the 2–3 rung offer ladder and flag the recommended rung."""
    current = get_plan(plan_id)
    upgrade = next_tier(plan_id)

    if upgrade is None:
        # Top tier: no upgrade path → a single deeper-discount retain rung.
        return OfferLadder(
            rungs=[_retain_rung(current, monthly_price, deeper=True)],
            recommended="retain",
        )

    rungs = [
        _retain_rung(current, monthly_price, deeper=False),
        _value_upgrade_rung(upgrade, monthly_price),
        _upsell_rung(upgrade, monthly_price),
    ]
    return OfferLadder(
        rungs=rungs,
        recommended=_recommend(archetype, tenure_months, has_upgrade=True),
    )
