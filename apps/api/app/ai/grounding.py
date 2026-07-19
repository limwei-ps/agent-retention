"""Grounding context + cache key (spec §4.1, §4.3).

`GroundingContext` carries the real facts fed to the model (for a tailored pitch). The cache key is
derived from a **bucketed projection** so small usage fluctuations don't needlessly invalidate a
pitch, while any material change (plan, price, tenure band, usage band, expiry month, offer ladder,
model, prompt-template version) does.
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from datetime import date

from app.core.catalog import SOFT_CAP_GB, get_plan
from app.models.customer import Customer
from app.schemas.offer import OfferLadder


def tenure_bucket(months: int) -> str:
    if months <= 12:
        return "0-12"
    if months <= 24:
        return "13-24"
    if months <= 36:
        return "25-36"
    return "37+"


def usage_bucket(avg_monthly_gb: int, plan_id: str) -> str:
    ratio = avg_monthly_gb / SOFT_CAP_GB[plan_id]
    if ratio < 0.5:
        return "low"
    if ratio < 0.85:
        return "mid"
    return "high"


@dataclass(frozen=True)
class GroundingContext:
    customer_id: str
    name: str
    plan_id: str
    plan_name: str
    monthly_price: int
    tenure_months: int
    avg_monthly_gb: int
    last_month_gb: int
    contract_end: date
    ladder: OfferLadder


def build_grounding(customer: Customer, ladder: OfferLadder) -> GroundingContext:
    plan = get_plan(customer.current_plan_id)
    return GroundingContext(
        customer_id=customer.id,
        name=customer.name,
        plan_id=plan.id,
        plan_name=plan.name,
        monthly_price=customer.monthly_price,
        tenure_months=customer.tenure_months,
        avg_monthly_gb=customer.avg_monthly_gb,
        last_month_gb=customer.last_month_gb,
        contract_end=customer.contract_end_date,
        ladder=ladder,
    )


def _cache_projection(ctx: GroundingContext) -> dict:
    """The exact, bucketed facts the pitch depends on — hashed into the cache key."""
    return {
        "customer_id": ctx.customer_id,
        "plan_id": ctx.plan_id,
        "monthly_price": ctx.monthly_price,
        "tenure_bucket": tenure_bucket(ctx.tenure_months),
        "usage_bucket": usage_bucket(ctx.avg_monthly_gb, ctx.plan_id),
        "contract_end_month": ctx.contract_end.strftime("%Y-%m"),
        "recommended": ctx.ladder.recommended,
        "ladder": [
            {
                "type": r.type,
                "target_plan_id": r.target_plan.id,
                "monthly_price": r.monthly_price,
                "term_months": r.term_months,
            }
            for r in ctx.ladder.rungs
        ],
    }


def cache_key(ctx: GroundingContext, model_id: str, template_version: str) -> str:
    payload = json.dumps(_cache_projection(ctx), sort_keys=True, separators=(",", ":"))
    digest = hashlib.sha256(f"{payload}|{template_version}|{model_id}".encode()).hexdigest()
    return digest
