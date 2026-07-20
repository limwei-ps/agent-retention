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
# Any "<Capitalized brand> Fibre/Fiber <token>" phrase — catches fabricated brands
# ("MaxSpeed Fibre Ultra") and misspellings ("TIME Fiber 300"), not just the real "TIME Fibre"
# prefix. Case-sensitive on capital-F so generic lowercase prose ("a Malaysian fibre provider",
# straight from the system prompt) is not mistaken for a plan mention.
_PLAN_RE = re.compile(r"\b[A-Z][A-Za-z0-9]+ Fib(?:re|er) \S+")


@dataclass(frozen=True)
class VerificationResult:
    ok: bool
    reason: str = ""
    invented_amounts: tuple[int, ...] = ()
    invented_plans: tuple[str, ...] = ()


def verify_grounding(text: str, ladder: OfferLadder, current_price: int) -> VerificationResult:
    catalog_names = {p.name for p in CATALOG}
    allowed_amounts = (
        {current_price} | {p.price_myr for p in CATALOG} | {r.monthly_price for r in ladder.rungs}
    )

    found_amounts = {int(m) for m in _AMOUNT_RE.findall(text)}
    invented_amounts = tuple(sorted(found_amounts - allowed_amounts))

    mentioned_plans = {m.rstrip(".,;:") for m in _PLAN_RE.findall(text)}
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
