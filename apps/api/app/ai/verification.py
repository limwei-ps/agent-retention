"""Output grounding verification (spec §4.4).

Turns "prompted carefully" into a guarantee: a pitch is only accepted if it (positively) states the
recommended plan + price and (negatively) contains no RM amount or TIME Fibre plan name outside the
catalog/offer-ladder allow-list.
"""

from __future__ import annotations

import re
from dataclasses import dataclass

from app.core.catalog import CATALOG
from app.schemas.offer import OfferLadder

_AMOUNT_RE = re.compile(r"RM\s?(\d+)")
# Plan-name check targets numeric plan identifiers: "<brand> Fibre/Fiber <digit…>". Requiring a
# digit-led token after "Fibre" gates real plan mentions (every catalog name is digit-suffixed —
# "TIME Fibre 100" … "TIME Fibre 1Gbps") and catches misspellings/fabrications that carry a number
# ("TIME Fiber 300", "MaxSpeed Fibre 900"), while NOT flagging ordinary prose ("TIME Fibre plans",
# "Our Fibre network", "Malaysian Fibre provider"). Fabricated *prices* are caught independently by
# the amount allow-list; a fabricated brand with a non-numeric suffix ("MaxSpeed Fibre Ultra") is an
# accepted residual gap (docs/take-home-plan.md §8).
_PLAN_RE = re.compile(r"\b[A-Za-z][A-Za-z0-9]* Fib(?:re|er) \d\S*")
# Real models append the speed unit the catalog name omits ("TIME Fibre 300Mbps" vs catalog
# "TIME Fibre 300"). Fold a trailing Mbps/Gbps away before the catalog membership test so that
# grounded phrasing isn't flagged — wrong numbers / misspelt brands survive and are still caught.
_SPEED_UNIT_RE = re.compile(r"\s*(?:mbps|gbps)\.?$", re.IGNORECASE)


def _normalize_plan(name: str) -> str:
    return _SPEED_UNIT_RE.sub("", name.rstrip(".,;:")).strip()


@dataclass(frozen=True)
class VerificationResult:
    ok: bool
    reason: str = ""
    invented_amounts: tuple[int, ...] = ()
    invented_plans: tuple[str, ...] = ()


def verify_grounding(text: str, ladder: OfferLadder, current_price: int) -> VerificationResult:
    catalog_names = {_normalize_plan(p.name) for p in CATALOG}
    allowed_amounts = (
        {current_price} | {p.price_myr for p in CATALOG} | {r.monthly_price for r in ladder.rungs}
    )

    found_amounts = {int(m) for m in _AMOUNT_RE.findall(text)}
    invented_amounts = tuple(sorted(found_amounts - allowed_amounts))

    mentioned_plans = {_normalize_plan(m) for m in _PLAN_RE.findall(text)}
    invented_plans = tuple(sorted(p for p in mentioned_plans if p not in catalog_names))

    rec = next(r for r in ladder.rungs if r.type == ladder.recommended)
    has_plan = rec.target_plan.name in text
    has_price = rec.monthly_price in found_amounts

    if invented_amounts:
        return VerificationResult(False, "out-of-catalog amount", invented_amounts, invented_plans)
    if invented_plans:
        return VerificationResult(False, "out-of-catalog plan", invented_amounts, invented_plans)
    if not has_plan or not has_price:
        return VerificationResult(False, "recommended offer not stated")
    return VerificationResult(True)
