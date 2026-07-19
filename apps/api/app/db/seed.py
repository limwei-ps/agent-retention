"""Seed-on-boot fake data (spec §2).

Deterministic (seeded RNG + Faker) so runs are reproducible. Idempotent: only seeds when the
customers table is empty. Cloud Run's filesystem is ephemeral, so we seed on every boot.
"""

from __future__ import annotations

import calendar
import random
from datetime import date, timedelta

from faker import Faker
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.core.catalog import CATALOG, SOFT_CAP_GB
from app.models.customer import Customer

SEED = 1337
CUSTOMER_COUNT = 60
ARCHETYPES = ("flat_low", "climbing", "heavy")
REGIONS = ("Klang Valley", "Penang", "Johor", "Sabah", "Sarawak", "Perak", "Melaka")


def _last_12_months(today: date) -> list[str]:
    months: list[str] = []
    year, month = today.year, today.month
    for _ in range(12):
        months.append(f"{year:04d}-{month:02d}")
        month -= 1
        if month == 0:
            month, year = 12, year - 1
    return list(reversed(months))


def _usage_curve(rng: random.Random, archetype: str, cap: int) -> list[int]:
    points: list[int] = []
    for i in range(12):
        frac = i / 11
        if archetype == "flat_low":
            base = 0.4
        elif archetype == "climbing":
            base = 0.3 + 0.6 * frac  # 30% → 90%
        else:  # heavy
            base = 0.95
        noise = rng.uniform(-0.05, 0.05)
        points.append(max(1, round(cap * (base + noise))))
    return points


def _contract_end_date(rng: random.Random, today: date) -> date:
    month_end = date(today.year, today.month, calendar.monthrange(today.year, today.month)[1])
    if rng.random() < 0.35:
        # Cluster in the current calendar month so the dashboard is non-trivial.
        start = date(today.year, today.month, 1)
        span = (month_end - start).days
        return start + timedelta(days=rng.randint(0, span))
    # Otherwise spread across the coming ~90 days.
    return today + timedelta(days=rng.randint(1, 90))


def _build_customers(today: date) -> list[Customer]:
    rng = random.Random(SEED)
    fake = Faker()
    Faker.seed(SEED)
    months = _last_12_months(today)

    customers: list[Customer] = []
    for i in range(CUSTOMER_COUNT):
        plan = rng.choice(CATALOG)
        archetype = ARCHETYPES[i % len(ARCHETYPES)]
        monthly_price = plan.price_myr - rng.choice([0, 0, 10, 20])
        gb_points = _usage_curve(rng, archetype, SOFT_CAP_GB[plan.id])
        usage_history = [{"month": m, "gb": gb} for m, gb in zip(months, gb_points)]

        customers.append(
            Customer(
                id=f"CUST-{i + 1:05d}",
                name=fake.name(),
                email=fake.email(),
                phone=fake.msisdn(),
                current_plan_id=plan.id,
                monthly_price=monthly_price,
                tenure_months=rng.randint(3, 60),
                contract_end_date=_contract_end_date(rng, today),
                region=rng.choice(REGIONS),
                usage_archetype=archetype,
                usage_history=usage_history,
                avg_monthly_gb=round(sum(gb_points) / len(gb_points)),
                last_month_gb=gb_points[-1],
            )
        )
    return customers


def seed_if_empty(db: Session, *, today: date | None = None) -> int:
    """Seed customers if the table is empty. Returns the number of rows inserted (0 if already seeded)."""
    existing = db.scalar(select(func.count()).select_from(Customer))
    if existing:
        return 0
    customers = _build_customers(today or date.today())
    db.add_all(customers)
    db.commit()
    return len(customers)
