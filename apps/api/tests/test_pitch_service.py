import asyncio

from sqlalchemy import func, select

from app.ai.llm_client import MockLLM, ProviderError
from app.ai.llm_provider import LLMChain, LLMHop
from app.ai.single_flight import SingleFlight
from app.core.budget import DailyBudget
from app.models.pitch import Pitch
from app.repositories.pitch_repository import SqlPitchRepository
from app.services.offer_service import build_offer_ladder
from app.services.pitch_service import PitchService


class CountingLLM:
    """Wraps MockLLM and counts generate() calls (for cache/single-flight assertions)."""

    def __init__(self, model_id: str = "mock", delay_s: float = 0.0) -> None:
        self.model_id = model_id
        self.calls = 0
        self._delay = delay_s

    async def generate(self, prompt: str):
        self.calls += 1
        async for ev in MockLLM(self.model_id, delay_s=self._delay).generate(prompt):
            yield ev


class FlakyLLM:
    """Ungrounded on the first attempt, grounded on the second (tests regenerate-once)."""

    def __init__(self, model_id: str = "mock") -> None:
        self.model_id = model_id
        self.calls = 0

    async def generate(self, prompt: str):
        self.calls += 1
        async for ev in MockLLM(self.model_id, invalid_mode=(self.calls == 1)).generate(prompt):
            yield ev


def _chain(*hops: tuple[str, object]) -> LLMChain:
    return LLMChain(hops=tuple(LLMHop(name, client) for name, client in hops))


def _service(db_session, chain: LLMChain) -> PitchService:
    return PitchService(SqlPitchRepository(db_session), chain, SingleFlight())


def _customer(db_session, make_customer, **kw):
    customer = make_customer(**kw)
    db_session.add(customer)
    db_session.commit()
    ladder = build_offer_ladder(
        customer.current_plan_id,
        customer.monthly_price,
        customer.tenure_months,
        customer.usage_archetype,
    )
    return customer, ladder


async def _run(service, customer, ladder, *, force=False):
    return [ev async for ev in service.stream_pitch(customer, ladder, force=force)]


def _pitch_count(db_session) -> int:
    return db_session.scalar(select(func.count()).select_from(Pitch))


async def test_generates_streams_and_persists(db_session, make_customer):
    customer, ladder = _customer(db_session, make_customer, plan="fibre_300", archetype="heavy")
    events = await _run(_service(db_session, _chain(("primary", MockLLM()))), customer, ladder)

    assert any(e.event == "token" for e in events)
    done = next(e for e in events if e.event == "done")
    assert done.data["grounding_ok"] is True
    assert done.data["cache_hit"] is False
    assert _pitch_count(db_session) == 1


async def test_cache_hit_replays_without_calling_llm(db_session, make_customer):
    customer, ladder = _customer(db_session, make_customer)
    client = CountingLLM()
    svc = _service(db_session, _chain(("primary", client)))

    await _run(svc, customer, ladder)  # miss → generate
    events = await _run(svc, customer, ladder)  # hit → replay

    assert client.calls == 1
    assert _pitch_count(db_session) == 1
    assert next(e for e in events if e.event == "done").data["cache_hit"] is True


async def test_force_bypasses_cache(db_session, make_customer):
    customer, ladder = _customer(db_session, make_customer)
    client = CountingLLM()
    svc = _service(db_session, _chain(("primary", client)))

    await _run(svc, customer, ladder)
    await _run(svc, customer, ladder, force=True)

    assert client.calls == 2
    assert _pitch_count(db_session) == 2


async def test_regenerates_once_on_ungrounded_output(db_session, make_customer):
    customer, ladder = _customer(db_session, make_customer)
    client = FlakyLLM()
    events = await _run(_service(db_session, _chain(("primary", client))), customer, ladder)

    assert any(e.event == "regenerating" for e in events)
    assert next(e for e in events if e.event == "done").data["grounding_ok"] is True
    assert client.calls == 2


async def test_falls_back_to_secondary_on_provider_error(db_session, make_customer):
    customer, ladder = _customer(db_session, make_customer)
    chain = _chain(("primary", MockLLM(fail=True)), ("secondary", MockLLM("mock-flash")))
    events = await _run(_service(db_session, chain), customer, ladder)

    assert any(e.event == "fallback" for e in events)
    assert next(e for e in events if e.event == "done").data["model"] == "mock-flash"


async def test_all_hops_fail_no_cache_yields_error(db_session, make_customer):
    customer, ladder = _customer(db_session, make_customer)
    events = await _run(
        _service(db_session, _chain(("primary", MockLLM(fail=True)))), customer, ladder
    )

    assert events[-1].event == "error"
    assert _pitch_count(db_session) == 0


async def test_falls_back_to_last_cached_when_all_hops_fail(db_session, make_customer):
    # pro→flash→cached: every live hop fails but a prior ready pitch exists → serve it, flagged stale.
    customer, ladder = _customer(db_session, make_customer)
    await _run(_service(db_session, _chain(("primary", MockLLM()))), customer, ladder)  # seed cache
    assert _pitch_count(db_session) == 1

    # force bypasses the normal cache-read so we exercise the fallback chain, not a plain cache hit.
    failing = _service(db_session, _chain(("primary", MockLLM(fail=True))))
    events = await _run(failing, customer, ladder, force=True)

    assert any(e.event == "fallback" and e.data.get("hop") == "cached" for e in events)
    done = next(e for e in events if e.event == "done")
    assert done.data["stale"] is True
    assert done.data["cache_hit"] is True
    assert _pitch_count(db_session) == 1  # a stale serve writes no new row


async def test_generate_reports_stale_outcome(db_session, make_customer):
    # Bulk path (generate) must surface the degraded last-cached fallback via outcome.stale.
    customer, ladder = _customer(db_session, make_customer)
    await _service(db_session, _chain(("primary", MockLLM()))).generate(customer, ladder)

    failing = _service(db_session, _chain(("primary", MockLLM(fail=True))))
    outcome = await failing.generate(customer, ladder, force=True)

    assert outcome.ok is True
    assert outcome.stale is True
    assert _pitch_count(db_session) == 1


async def test_single_flight_coalesces_concurrent_requests(db_session, make_customer):
    customer, ladder = _customer(db_session, make_customer)
    client = CountingLLM(delay_s=0.01)
    svc = _service(db_session, _chain(("primary", client)))

    r1, r2 = await asyncio.gather(_run(svc, customer, ladder), _run(svc, customer, ladder))

    assert client.calls == 1  # coalesced into one generation
    assert any(e.event == "done" for e in r1)
    assert any(e.event == "done" for e in r2)
    assert _pitch_count(db_session) == 1


async def test_generate_returns_outcome_and_persists(db_session, make_customer):
    customer, ladder = _customer(db_session, make_customer)
    svc = _service(db_session, _chain(("primary", MockLLM())))

    outcome = await svc.generate(customer, ladder)

    assert outcome.ok is True
    assert outcome.pitch_id is not None
    assert outcome.stale is False
    assert _pitch_count(db_session) == 1


async def test_generate_cache_hit_reuses_row(db_session, make_customer):
    customer, ladder = _customer(db_session, make_customer)
    client = CountingLLM()
    svc = _service(db_session, _chain(("primary", client)))

    await svc.generate(customer, ladder)  # miss
    outcome = await svc.generate(customer, ladder)  # hit → replay, no new row

    assert outcome.ok is True
    assert client.calls == 1
    assert _pitch_count(db_session) == 1


async def test_generate_reports_failure(db_session, make_customer):
    customer, ladder = _customer(db_session, make_customer)
    svc = _service(db_session, _chain(("primary", MockLLM(fail=True))))

    outcome = await svc.generate(customer, ladder)

    assert outcome.ok is False
    assert outcome.pitch_id is None
    assert _pitch_count(db_session) == 0


async def test_single_flight_coalesced_failure_yields_clean_error(db_session, make_customer):
    # Two concurrent requests, every hop fails, no prior cache → both get a clean error (no crash).
    customer, ladder = _customer(db_session, make_customer)

    class _FailSlow:
        model_id = "mock"

        async def generate(self, prompt):
            await asyncio.sleep(0.01)
            raise ProviderError("down")
            yield  # unreachable; makes this an async generator

    svc = _service(db_session, _chain(("primary", _FailSlow())))
    r1, r2 = await asyncio.gather(_run(svc, customer, ladder), _run(svc, customer, ladder))

    assert r1[-1].event == "error"
    assert r2[-1].event == "error"
    assert _pitch_count(db_session) == 0


def _over_budget() -> DailyBudget:
    b = DailyBudget(limit_usd=0.01, tz_name="Asia/Kuala_Lumpur")
    b.record(1.0)  # spent >= limit
    return b


async def test_over_budget_refuses_fresh_generation(db_session, make_customer, monkeypatch):
    # Over the daily cap → a fresh generation is refused with a clean error and no LLM call / no row.
    monkeypatch.setattr("app.services.pitch_service.BUDGET", _over_budget())
    customer, ladder = _customer(db_session, make_customer)
    client = CountingLLM()
    events = await _run(_service(db_session, _chain(("primary", client))), customer, ladder)

    assert events[-1].event == "error"
    assert "budget" in events[-1].data["message"].lower()
    assert client.calls == 0
    assert _pitch_count(db_session) == 0


async def test_cache_hit_served_even_when_over_budget(db_session, make_customer, monkeypatch):
    # Seed a cached pitch under the default (disabled) budget, then flip to over-budget: the cache
    # replay must still be served (only fresh generations are gated).
    customer, ladder = _customer(db_session, make_customer)
    client = CountingLLM()
    svc = _service(db_session, _chain(("primary", client)))
    await _run(svc, customer, ladder)  # miss → generate + cache
    assert client.calls == 1

    monkeypatch.setattr("app.services.pitch_service.BUDGET", _over_budget())
    events = await _run(svc, customer, ladder)  # over budget, but cache hit → still served

    assert not any(e.event == "error" for e in events)
    assert next(e for e in events if e.event == "done").data["cache_hit"] is True
    assert client.calls == 1  # no new LLM call
