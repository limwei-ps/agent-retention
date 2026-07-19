from app.services.offer_service import build_offer_ladder
from app.ai.verification import verify_grounding

# Mid-tier, heavy → recommended = upsell (fibre_500 @ RM 159).
LADDER = build_offer_ladder("fibre_300", monthly_price=129, tenure_months=12, archetype="heavy")
REC = next(r for r in LADDER.rungs if r.type == LADDER.recommended)


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
