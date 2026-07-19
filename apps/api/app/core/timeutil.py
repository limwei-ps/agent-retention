"""Timezone-aware calendar helpers."""

from __future__ import annotations

import calendar
from datetime import date, datetime
from zoneinfo import ZoneInfo


def current_month_bounds(tz_name: str) -> tuple[date, date]:
    """Return (first_day, last_day) of the current calendar month in the given timezone."""
    today = datetime.now(ZoneInfo(tz_name)).date()
    first = today.replace(day=1)
    last = date(today.year, today.month, calendar.monthrange(today.year, today.month)[1])
    return first, last
