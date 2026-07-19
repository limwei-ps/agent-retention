"""Bulk fan-out unit tests. A file-based temp SQLite gives each worker its own connection (mirrors
production pooling), so real concurrency — and the semaphore cap — is exercised, unlike the in-memory
StaticPool fixture whose single shared connection can't take concurrent writers."""

from datetime import date

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.ai.llm_client import MockLLM
from app.ai.llm_provider import LLMChain, LLMHop
from app.ai.single_flight import SingleFlight
from app.db.session import Base
from app.models.customer import Customer
from app.services.batch_registry import BatchRegistry
from app.services.bulk_pitch_service import run_batch


class ConcurrencyProbeLLM:
    """Records peak concurrent generations so the semaphore cap can be asserted."""

    model_id = "mock"

    def __init__(self, delay_s: float = 0.02) -> None:
        self._delay = delay_s
        self.current = 0
        self.peak = 0

    async def generate(self, prompt: str):
        self.current += 1
        self.peak = max(self.peak, self.current)
        try:
            async for ev in MockLLM(self.model_id, delay_s=self._delay).generate(prompt):
                yield ev
        finally:
            self.current -= 1


def _chain(client) -> LLMChain:
    return LLMChain(hops=(LLMHop("primary", client),))


def _factory(tmp_path) -> sessionmaker:
    engine = create_engine(
        f"sqlite:///{tmp_path / 'bulk.db'}", connect_args={"check_same_thread": False}
    )
    Base.metadata.create_all(engine)
    return sessionmaker(bind=engine)


def _seed(factory: sessionmaker, ids: list[str]) -> None:
    with factory() as db:
        for i, cid in enumerate(ids):
            db.add(
                Customer(
                    id=cid,
                    name=f"Cust {i}",
                    email=f"{cid}@example.com",
                    phone="60123456789",
                    current_plan_id="fibre_300",
                    monthly_price=129,
                    tenure_months=12,
                    contract_end_date=date(2026, 7, 20),
                    region="Penang",
                    usage_archetype="climbing",
                    usage_history=[{"month": "2026-06", "gb": 550}],
                    avg_monthly_gb=400,
                    last_month_gb=550,
                )
            )
        db.commit()


async def test_all_succeed(tmp_path):
    factory = _factory(tmp_path)
    ids = ["CUST-1", "CUST-2", "CUST-3"]
    _seed(factory, ids)
    reg = BatchRegistry()
    reg.create(1, ids)

    await run_batch(
        1,
        ids,
        session_factory=factory,
        chain=_chain(MockLLM()),
        single_flight=SingleFlight(),
        registry=reg,
        concurrency=4,
    )

    snap = reg.snapshot(1)
    assert snap.complete is True
    assert snap.succeeded == 3
    assert snap.failed == 0
    assert all(i.pitch_id is not None for i in snap.items)


async def test_partial_failure_never_aborts_batch(tmp_path):
    """One bogus customer id fails in isolation; the real ones still succeed."""
    factory = _factory(tmp_path)
    real = ["CUST-1", "CUST-2"]
    _seed(factory, real)
    ids = ["CUST-1", "CUST-MISSING", "CUST-2"]
    reg = BatchRegistry()
    reg.create(2, ids)

    await run_batch(
        2,
        ids,
        session_factory=factory,
        chain=_chain(MockLLM()),
        single_flight=SingleFlight(),
        registry=reg,
        concurrency=4,
    )

    snap = reg.snapshot(2)
    assert snap.complete is True
    assert snap.succeeded == 2
    assert snap.failed == 1
    missing = next(i for i in snap.items if i.customer_id == "CUST-MISSING")
    assert missing.status == "failed"
    assert missing.error == "customer not found"


async def test_provider_failure_marks_item_failed(tmp_path):
    factory = _factory(tmp_path)
    ids = ["CUST-1"]
    _seed(factory, ids)
    reg = BatchRegistry()
    reg.create(3, ids)

    await run_batch(
        3,
        ids,
        session_factory=factory,
        chain=_chain(MockLLM(fail=True)),  # every hop fails, no cache → generation fails
        single_flight=SingleFlight(),
        registry=reg,
        concurrency=4,
    )

    snap = reg.snapshot(3)
    assert snap.failed == 1
    assert snap.succeeded == 0


async def test_semaphore_caps_concurrency(tmp_path):
    factory = _factory(tmp_path)
    ids = [f"CUST-{i}" for i in range(6)]
    _seed(factory, ids)
    reg = BatchRegistry()
    reg.create(4, ids)
    probe = ConcurrencyProbeLLM(delay_s=0.02)

    await run_batch(
        4,
        ids,
        session_factory=factory,
        chain=_chain(probe),
        single_flight=SingleFlight(),
        registry=reg,
        concurrency=2,
    )

    assert reg.snapshot(4).succeeded == 6
    assert probe.peak <= 2  # never more than the cap in flight at once
    assert probe.peak >= 2  # and it did run concurrently (not serialized)
