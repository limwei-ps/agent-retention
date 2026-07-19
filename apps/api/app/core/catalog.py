"""Fixed plan catalog + offer constants — the single source of truth for plans/prices.

Imported by seeding, the offer service, and (later) the AI grounding layer so the model can only
quote real plan names and prices (spec §1.1).
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class PlanTier:
    id: str
    name: str
    speed_mbps: int
    price_myr: int


# Ordered cheapest → most expensive; "next tier up" = the next entry.
CATALOG: tuple[PlanTier, ...] = (
    PlanTier("fibre_100", "TIME Fibre 100", 100, 99),
    PlanTier("fibre_300", "TIME Fibre 300", 300, 129),
    PlanTier("fibre_500", "TIME Fibre 500", 500, 159),
    PlanTier("fibre_1000", "TIME Fibre 1Gbps", 1000, 199),
)

_BY_ID: dict[str, PlanTier] = {p.id: p for p in CATALOG}

# Rough monthly soft-cap (GB) per tier — shapes seeded usage curves and the grounding usage bucket.
SOFT_CAP_GB: dict[str, int] = {
    "fibre_100": 300,
    "fibre_300": 600,
    "fibre_500": 1000,
    "fibre_1000": 2000,
}

# Offer-ladder constants (spec §1.3).
RETAIN_DISCOUNT = 0.15  # 15% off current monthly price
RETAIN_DISCOUNT_TOP_TIER = 0.20  # deeper discount when there's no upgrade path
TERM_MONTHS = 24
UPSELL_PREMIUM_MYR = 30  # added over current spend for the upsell rung


def get_plan(plan_id: str) -> PlanTier:
    """Return the plan tier for `plan_id` or raise KeyError (fail fast on bad data)."""
    return _BY_ID[plan_id]


def next_tier(plan_id: str) -> PlanTier | None:
    """The next tier up, or None if `plan_id` is already the top tier."""
    for index, plan in enumerate(CATALOG):
        if plan.id == plan_id:
            return CATALOG[index + 1] if index + 1 < len(CATALOG) else None
    raise KeyError(plan_id)
