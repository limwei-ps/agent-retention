from app.core.catalog import CATALOG, get_plan
from app.services.offer_service import build_offer_ladder


def _prices_in_catalog_range(ladder) -> bool:
    lowest = min(p.price_myr for p in CATALOG)
    highest = max(p.price_myr for p in CATALOG)
    # Retain discounts can dip below list; upgrades never exceed the target list price.
    return all(0 < r.monthly_price <= highest for r in ladder.rungs) and lowest > 0


def test_mid_tier_has_three_rungs_with_recommended_in_rungs() -> None:
    ladder = build_offer_ladder(
        "fibre_300", monthly_price=129, tenure_months=12, archetype="climbing"
    )
    types = [r.type for r in ladder.rungs]
    assert types == ["retain", "value_upgrade", "upsell"]
    assert ladder.recommended in types


def test_heavy_usage_recommends_upsell() -> None:
    ladder = build_offer_ladder("fibre_300", monthly_price=129, tenure_months=12, archetype="heavy")
    assert ladder.recommended == "upsell"


def test_climbing_usage_recommends_value_upgrade() -> None:
    ladder = build_offer_ladder(
        "fibre_100", monthly_price=99, tenure_months=6, archetype="climbing"
    )
    assert ladder.recommended == "value_upgrade"


def test_flat_low_recommends_retain() -> None:
    ladder = build_offer_ladder(
        "fibre_300", monthly_price=129, tenure_months=6, archetype="flat_low"
    )
    assert ladder.recommended == "retain"


def test_high_tenure_overrides_to_retain() -> None:
    ladder = build_offer_ladder("fibre_300", monthly_price=129, tenure_months=48, archetype="heavy")
    assert ladder.recommended == "retain"


def test_top_tier_has_single_deeper_retain_rung() -> None:
    ladder = build_offer_ladder(
        "fibre_1000", monthly_price=199, tenure_months=12, archetype="heavy"
    )
    assert [r.type for r in ladder.rungs] == ["retain"]
    assert ladder.recommended == "retain"
    # 20% off 199 = ~159
    assert ladder.rungs[0].monthly_price == round(199 * 0.80)


def test_retain_rung_is_discounted_below_current() -> None:
    ladder = build_offer_ladder(
        "fibre_300", monthly_price=129, tenure_months=6, archetype="flat_low"
    )
    retain = next(r for r in ladder.rungs if r.type == "retain")
    assert retain.monthly_price < 129
    assert retain.vs_current_delta < 0


def test_upgrade_rungs_target_next_tier_and_stay_within_list() -> None:
    ladder = build_offer_ladder("fibre_300", monthly_price=129, tenure_months=12, archetype="heavy")
    upsell = next(r for r in ladder.rungs if r.type == "upsell")
    assert upsell.target_plan.id == "fibre_500"
    assert upsell.monthly_price <= get_plan("fibre_500").price_myr
    assert _prices_in_catalog_range(ladder)
