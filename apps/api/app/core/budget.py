"""In-process daily LLM spend cap — the money backstop for the shared public demo.

A single-instance running total of estimated LLM cost for the current day. Once it reaches the
configured ceiling, fresh generations are refused (cache hits and last-cached fallbacks stay free, so
the app keeps working). Thread-safe (sync SQLAlchemy path may run in a threadpool); the total rolls
over at midnight in the app timezone and resets on restart — a production build would use a durable,
per-agent budget store (see README out-of-scope).
"""

from __future__ import annotations

import threading
from dataclasses import dataclass
from datetime import date

from app.core.config import settings
from app.core.timeutil import today_in


@dataclass(frozen=True)
class BudgetSnapshot:
    limit_usd: float
    spent_usd: float
    day: str
    ok: bool  # True when a fresh generation is still allowed


class DailyBudget:
    """Tracks (day, spent_usd) against a USD ceiling. limit <= 0 disables the cap."""

    def __init__(self, limit_usd: float, tz_name: str) -> None:
        self._limit = limit_usd
        self._tz = tz_name
        self._lock = threading.Lock()
        self._day: date = today_in(tz_name)
        self._spent = 0.0

    def _roll(self) -> None:
        # Caller must hold the lock. Reset the running total when the calendar day changes.
        current = today_in(self._tz)
        if current != self._day:
            self._day = current
            self._spent = 0.0

    def over_budget(self) -> bool:
        """True when the cap is set and the day's spend has reached it (block fresh generations)."""
        if self._limit <= 0:
            return False
        with self._lock:
            self._roll()
            return self._spent >= self._limit

    def record(self, cost_usd: float) -> None:
        """Add the cost of a completed fresh generation to today's running total."""
        if self._limit <= 0 or cost_usd <= 0:
            return
        with self._lock:
            self._roll()
            self._spent += cost_usd

    def snapshot(self) -> BudgetSnapshot:
        with self._lock:
            self._roll()
            ok = self._limit <= 0 or self._spent < self._limit
            return BudgetSnapshot(
                limit_usd=self._limit,
                spent_usd=round(self._spent, 6),
                day=self._day.isoformat(),
                ok=ok,
            )

    def reset(self) -> None:
        """Test helper: clear the running total for the current day."""
        with self._lock:
            self._day = today_in(self._tz)
            self._spent = 0.0


BUDGET = DailyBudget(settings.llm_daily_budget_usd, settings.app_timezone)
