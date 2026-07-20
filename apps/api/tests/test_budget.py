from datetime import date

import app.core.budget as budget_mod
from app.core.budget import DailyBudget

TZ = "Asia/Kuala_Lumpur"


def test_zero_limit_never_blocks() -> None:
    b = DailyBudget(limit_usd=0.0, tz_name=TZ)
    b.record(999.0)
    assert b.over_budget() is False
    assert b.snapshot().ok is True


def test_blocks_at_limit() -> None:
    b = DailyBudget(limit_usd=1.0, tz_name=TZ)
    assert b.over_budget() is False
    b.record(0.6)
    assert b.over_budget() is False
    b.record(0.5)  # 1.1 >= 1.0
    assert b.over_budget() is True
    assert b.snapshot().ok is False


def test_rolls_over_on_new_day(monkeypatch) -> None:
    day = {"d": date(2026, 7, 20)}
    monkeypatch.setattr(budget_mod, "today_in", lambda _tz: day["d"])
    b = DailyBudget(limit_usd=1.0, tz_name=TZ)
    b.record(1.0)
    assert b.over_budget() is True
    day["d"] = date(2026, 7, 21)  # next day → running total resets
    assert b.over_budget() is False
    assert b.snapshot().spent_usd == 0.0


def test_reset_clears_spend() -> None:
    b = DailyBudget(limit_usd=1.0, tz_name=TZ)
    b.record(1.0)
    assert b.over_budget() is True
    b.reset()
    assert b.over_budget() is False
