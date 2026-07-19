"""Shared test fixtures: an isolated in-memory DB + a TestClient with `get_db` overridden.

Deterministic fixture data (not the random seeder) keeps assertions stable. TestClient is used
without a `with` block so the app lifespan (which would seed the real DB) never runs.
"""

from __future__ import annotations

from collections.abc import Callable, Iterator
from datetime import date

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from app.db.session import Base, get_db, get_session_factory
from app.main import app
from app.models.customer import Customer
from app.services.batch_registry import BatchRegistry


@pytest.fixture
def db_session() -> Iterator[Session]:
    engine = create_engine(
        "sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool
    )
    Base.metadata.create_all(engine)
    session = sessionmaker(bind=engine)()
    try:
        yield session
    finally:
        session.close()
        Base.metadata.drop_all(engine)


@pytest.fixture
def client(db_session: Session) -> Iterator[TestClient]:
    def override_get_db() -> Iterator[Session]:
        yield db_session

    app.dependency_overrides[get_db] = override_get_db
    yield TestClient(app)
    app.dependency_overrides.clear()


@pytest.fixture
def bulk_client(tmp_path) -> Iterator[tuple[TestClient, sessionmaker]]:
    """A client for bulk tests backed by a temp-file SQLite so the request session and the
    background-task worker sessions each get their own connection (mirrors production pooling).

    Overrides both `get_db` and `get_session_factory` onto that engine, and installs a fresh
    `BatchRegistry` on the app so batches don't leak across tests. Yields (client, session_factory)
    so the test can seed customers directly.
    """
    engine = create_engine(
        f"sqlite:///{tmp_path / 'api.db'}", connect_args={"check_same_thread": False}
    )
    Base.metadata.create_all(engine)
    factory = sessionmaker(bind=engine)

    def override_get_db() -> Iterator[Session]:
        db = factory()
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = override_get_db
    app.dependency_overrides[get_session_factory] = lambda: factory
    app.state.batch_registry = BatchRegistry()
    try:
        yield TestClient(app), factory
    finally:
        app.dependency_overrides.clear()


@pytest.fixture
def make_customer() -> Callable[..., Customer]:
    def _make(
        *,
        id: str = "CUST-00001",
        name: str = "Alice Tan",
        plan: str = "fibre_300",
        monthly_price: int = 129,
        tenure_months: int = 12,
        archetype: str = "climbing",
        avg_gb: int = 400,
        last_gb: int = 550,
        contract_end_date: date = date(2026, 7, 20),
        region: str = "Penang",
    ) -> Customer:
        return Customer(
            id=id,
            name=name,
            email=f"{id.lower()}@example.com",
            phone="60123456789",
            current_plan_id=plan,
            monthly_price=monthly_price,
            tenure_months=tenure_months,
            contract_end_date=contract_end_date,
            region=region,
            usage_archetype=archetype,
            usage_history=[{"month": "2026-06", "gb": last_gb}],
            avg_monthly_gb=avg_gb,
            last_month_gb=last_gb,
        )

    return _make
