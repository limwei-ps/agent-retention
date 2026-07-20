from app.core.catalog import CATALOG
from app.services.offer_service import build_offer_ladder
from app.ai.verification import verify_grounding

# Mid-tier, heavy → recommended = upsell (fibre_500 @ RM 159).
LADDER = build_offer_ladder("fibre_300", monthly_price=129, tenure_months=12, archetype="heavy")
REC = next(r for r in LADDER.rungs if r.type == LADDER.recommended)

# High tenure → recommended = retain (same plan, TIME Fibre 300 @ ~RM 110).
RETAIN_LADDER = build_offer_ladder(
    "fibre_300", monthly_price=129, tenure_months=48, archetype="flat_low"
)


def _pitch(price: int, plan: str = "TIME Fibre 500") -> str:
    return f"Upgrade to {plan} at RM {price}/month for 24 months. Great value!"


def test_grounded_pitch_passes() -> None:
    result = verify_grounding(_pitch(REC.monthly_price), LADDER, current_price=129)
    assert result.ok


def test_invented_amount_fails() -> None:
    result = verify_grounding(
        "Upgrade to TIME Fibre 500 at RM 159 for just RM 5 extra!", LADDER, current_price=129
    )
    assert not result.ok
    assert 5 in result.invented_amounts


def test_savings_delta_amount_passes() -> None:
    # Models state the monthly saving ("saving RM 19" = current 129 − retain 110), a grounded
    # difference that isn't a listed price. It must be allowed (was an intermittent false positive
    # → extra regenerate). Retain ladder: current 129, retain "TIME Fibre 300" @ 110, delta 19.
    text = "Recontract TIME Fibre 300 at RM 110/month — saving RM 19 a month — for 24 months."
    result = verify_grounding(text, RETAIN_LADDER, current_price=129)
    assert result.ok, result


def test_upsell_premium_delta_amount_passes() -> None:
    # The upsell premium ("+RM 30" = 159 − 129) is likewise a grounded delta, not an invented price.
    text = "Step up to TIME Fibre 500 at RM 159/month, just +RM 30 more than your RM 129 today."
    result = verify_grounding(text, LADDER, current_price=129)
    assert result.ok, result


def test_invented_plan_fails() -> None:
    result = verify_grounding(
        "Upgrade to TIME Fibre 9000 at RM 159/month.", LADDER, current_price=129
    )
    assert not result.ok
    assert "TIME Fibre 9000" in result.invented_plans


def test_missing_recommended_offer_fails() -> None:
    # No RM price stated for the recommended plan.
    result = verify_grounding("Thanks for being a loyal TIME Fibre 500 customer!", LADDER, 129)
    assert not result.ok
    assert result.reason == "recommended offer not stated"


def test_invented_brand_name_fails() -> None:
    # Recommended plan + a valid RM amount are present, but a fabricated numeric plan must be caught.
    text = "Upgrade to TIME Fibre 500 at RM 159/month — or try our MaxSpeed Fibre 900 deal!"
    result = verify_grounding(text, LADDER, current_price=129)
    assert not result.ok
    assert result.reason == "out-of-catalog plan"
    assert "MaxSpeed Fibre 900" in result.invented_plans


def test_misspelled_plan_fails() -> None:
    result = verify_grounding(
        "Upgrade to TIME Fiber 300 at RM 159/month.", LADDER, current_price=129
    )
    assert not result.ok
    assert "TIME Fiber 300" in result.invented_plans


def test_lowercase_fibre_prose_passes() -> None:
    # Generic lowercase "fibre" (as in the system prompt's "Malaysian fibre provider") is prose, not
    # a plan mention — it must not be flagged as an invented plan (no false positive).
    text = (
        "As your Malaysian fibre provider, upgrade to TIME Fibre 500 at RM 159/month for 24 months."
    )
    result = verify_grounding(text, LADDER, current_price=129)
    assert result.ok


def test_capitalized_fibre_prose_passes() -> None:
    # Regression guard: capitalized "Fibre" used as a common noun (not a numeric plan id) must NOT be
    # flagged. The earlier regex over-fired on these and wrongly failed fully-grounded pitches.
    for prose in ("TIME Fibre plans", "Our Fibre network", "As your Malaysian Fibre provider"):
        text = f"{prose}: upgrade to TIME Fibre 500 at RM 159/month for 24 months."
        result = verify_grounding(text, LADDER, current_price=129)
        assert result.ok, f"prose wrongly flagged: {prose} -> {result.invented_plans}"


def test_speed_suffixed_plan_passes() -> None:
    # Real models write the plan WITH its speed unit ("TIME Fibre 300Mbps"); the catalog name omits
    # it. This is fully grounded (right tier + price) and must NOT be flagged — the false positive
    # that made single-pitch regenerate loop: out-of-catalog plan → regenerate → fallback.
    for name in ("TIME Fibre 300Mbps", "TIME Fibre 300 Mbps"):
        text = f"Recontract your {name} plan for just RM 110/month on a 24-month term."
        result = verify_grounding(text, RETAIN_LADDER, current_price=129)
        assert result.ok, f"speed-suffixed plan wrongly flagged: {name} -> {result}"


def test_invented_number_with_speed_unit_still_fails() -> None:
    # Normalizing the unit must not blunt real inventions: a wrong number keeps failing.
    text = "Upgrade to TIME Fibre 9000Mbps at RM 159/month."
    result = verify_grounding(text, LADDER, current_price=129)
    assert not result.ok
    assert result.reason == "out-of-catalog plan"


def test_all_catalog_names_not_flagged() -> None:
    # Guards the regex's digit-suffix assumption against catalog drift: every real plan name, when
    # quoted, must never land in invented_plans (a future multi-word name would fail here loudly).
    for plan in CATALOG:
        text = f"Consider {plan.name} at RM {plan.price_myr}/month."
        result = verify_grounding(text, LADDER, current_price=129)
        assert plan.name not in result.invented_plans, f"{plan.name} wrongly flagged"
