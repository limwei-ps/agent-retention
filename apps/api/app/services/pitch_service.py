"""Pitch generation orchestration — the reliability core (spec §4.3–§4.8).

`stream_pitch` yields `SseEvent`s: cache-hit replays stored text; a miss runs the fallback chain,
streaming tokens live, verifying the output, regenerating once on an ungrounded result, persisting only
a verified pitch, and coalescing concurrent identical requests via single-flight. Every terminal
outcome (generated / last-cached fallback / failed) emits one structured cost/observability log line.

Concurrency note (documented tradeoff): the SQLAlchemy calls here are synchronous and run inside the
async request. At SQLite scale that's sub-millisecond; a production build would use an async driver or
offload to a threadpool and hold DB sessions only around each op. See docs/take-home-plan.md §8.
"""

from __future__ import annotations

import logging
import time
from collections.abc import AsyncIterator
from dataclasses import dataclass, field

from app.ai.grounding import GroundingContext, build_grounding, cache_key
from app.ai.llm_client import ProviderError, TextDelta, UsageInfo
from app.ai.llm_provider import LLMChain
from app.ai.pricing import estimate_cost
from app.ai.prompt import PROMPT_TEMPLATE_VERSION, build_prompt
from app.ai.single_flight import SingleFlight
from app.ai.verification import verify_grounding
from app.core.metrics import METRICS
from app.core.tracing import get_trace_id
from app.models.customer import Customer
from app.models.pitch import Pitch, PitchStatus
from app.repositories.pitch_repository import PitchRepository
from app.schemas.offer import OfferLadder

logger = logging.getLogger("app.pitch")


@dataclass
class SseEvent:
    event: str  # token | regenerating | fallback | done | error
    data: dict = field(default_factory=dict)


@dataclass
class _Terminal:
    """Internal sentinel yielded by _lead carrying the final pitch (None = failed)."""

    pitch: Pitch | None
    stale: bool = False  # True when serving a last-cached fallback (degraded)


@dataclass(frozen=True)
class GenerateOutcome:
    """Non-streaming result of a single generation (used by bulk fan-out)."""

    ok: bool
    pitch_id: int | None = None
    stale: bool = False  # served from a degraded last-cached fallback


class PitchService:
    def __init__(self, repo: PitchRepository, chain: LLMChain, single_flight: SingleFlight) -> None:
        self._repo = repo
        self._chain = chain
        self._sf = single_flight

    async def generate(
        self, customer: Customer, ladder: OfferLadder, *, force: bool = False
    ) -> GenerateOutcome:
        """Run a full generation and return the terminal outcome, discarding the token stream.

        A thin adapter over `stream_pitch` so bulk generation inherits the entire reliability path
        (cache, single-flight, fallback, verify+regenerate, cost logging) with no duplicated logic.
        """
        done: dict | None = None
        async for event in self.stream_pitch(customer, ladder, force=force):
            if event.event == "done":
                done = event.data
            elif event.event == "error":
                return GenerateOutcome(ok=False)
        if done is None:  # stream ended without a terminal event (shouldn't happen)
            return GenerateOutcome(ok=False)
        return GenerateOutcome(ok=True, pitch_id=done["pitch_id"], stale=done.get("stale", False))

    async def stream_pitch(
        self, customer: Customer, ladder: OfferLadder, *, force: bool = False
    ) -> AsyncIterator[SseEvent]:
        ctx = build_grounding(customer, ladder)
        key = cache_key(ctx, self._chain.hops[0].client.model_id, PROMPT_TEMPLATE_VERSION)

        if not force:
            # 1) Cache hit → replay the stored (already-verified) pitch.
            cached = self._repo.get_ready_by_cache_key(customer.id, key)
            if cached is not None:
                METRICS.inc("pitch_cache_hits_total")
                async for event in self._replay(cached, cache_hit=True):
                    yield event
                return

            # 2) A concurrent identical generation is running → coalesce onto it.
            existing = self._sf.follower(key)
            if existing is not None:
                try:
                    pitch = await existing
                except Exception:  # noqa: BLE001 - leader failed; report a clean error
                    pitch = None
                if pitch is None:
                    yield SseEvent("error", {"message": "generation failed"})
                    return
                async for event in self._replay(pitch, cache_hit=True):
                    yield event
                return

        # 3) Lead the generation (force bypasses single-flight so it never joins a normal run).
        future = None if force else self._sf.lead(key)
        pitch, stale = None, False
        try:
            async for item in self._lead(ctx, customer, key):
                if isinstance(item, _Terminal):
                    pitch, stale = item.pitch, item.stale
                else:
                    yield item
        except Exception as exc:  # noqa: BLE001
            if future is not None:
                self._sf.finish(key, future, error=exc)
            logger.exception("pitch generation crashed", extra={"ctx_customer_id": customer.id})
            yield SseEvent("error", {"message": "generation failed"})
            return

        if future is not None:
            if pitch is not None:
                self._sf.finish(key, future, result=pitch)
            else:  # resolve as error so coalesced followers surface a clean error, not a crash
                self._sf.finish(key, future, error=RuntimeError("no grounded pitch generated"))

        if pitch is None:
            yield SseEvent("error", {"message": "could not generate a grounded pitch"})
        else:
            yield self._done_event(pitch, cache_hit=stale, stale=stale)

    async def _lead(
        self, ctx: GroundingContext, customer: Customer, key: str
    ) -> AsyncIterator[SseEvent | _Terminal]:
        """Run the fallback chain; yield live events, then a _Terminal with the final pitch."""
        prompt = build_prompt(ctx)
        started = time.monotonic()

        for hop in self._chain.hops:
            for attempt in (1, 2):  # original + one regenerate on ungrounded output
                text, usage, provider_failed = "", None, False
                try:
                    async for ev in hop.client.generate(prompt):
                        if isinstance(ev, TextDelta):
                            text += ev.text
                            yield SseEvent("token", {"text": ev.text})
                        elif isinstance(ev, UsageInfo):
                            usage = ev
                except ProviderError:
                    provider_failed = True

                if provider_failed:
                    METRICS.inc("pitch_fallbacks_total", {"hop": hop.name})
                    yield SseEvent("fallback", {"hop": hop.name})
                    break  # advance to the next hop

                result = verify_grounding(text, ctx.ladder, ctx.monthly_price)
                if result.ok:
                    pitch = self._persist(customer, key, hop.client.model_id, text, usage)
                    self._log(
                        customer,
                        pitch,
                        cache_hit=False,
                        hop=hop.name,
                        started=started,
                        outcome="generated",
                    )
                    yield _Terminal(pitch)
                    return
                if attempt == 1:
                    METRICS.inc("pitch_regenerations_total")
                    yield SseEvent("regenerating", {"reason": result.reason})
                    continue
                METRICS.inc("pitch_fallbacks_total", {"hop": hop.name})
                yield SseEvent("fallback", {"hop": hop.name})  # retry exhausted for this hop

        # All hops failed → last-cached fallback (degraded, flagged stale).
        cached = self._repo.get_latest_ready_for_customer(customer.id)
        if cached is not None:
            METRICS.inc("pitch_fallbacks_total", {"hop": "cached"})
            yield SseEvent("fallback", {"hop": "cached"})
            for event in self._token_events(cached.text):
                yield event
            self._log(
                customer,
                cached,
                cache_hit=True,
                hop="cached",
                started=started,
                outcome="last_cached",
            )
            yield _Terminal(cached, stale=True)
            return

        METRICS.inc("pitch_generations_total", {"outcome": "failed"})
        logger.warning(
            "pitch generation failed",
            extra={
                "ctx_customer_id": customer.id,
                "ctx_outcome": "failed",
                "ctx_latency_ms": round((time.monotonic() - started) * 1000, 1),
            },
        )
        yield _Terminal(None)

    @staticmethod
    def _token_events(text: str | None) -> list[SseEvent]:
        return [SseEvent("token", {"text": word + " "}) for word in (text or "").split(" ")]

    async def _replay(self, pitch: Pitch, *, cache_hit: bool) -> AsyncIterator[SseEvent]:
        for event in self._token_events(pitch.text):
            yield event
        yield self._done_event(pitch, cache_hit=cache_hit)

    def _persist(
        self, customer: Customer, key: str, model_id: str, text: str, usage: UsageInfo | None
    ) -> Pitch:
        prompt_tokens = usage.prompt_tokens if usage else 0
        completion_tokens = usage.completion_tokens if usage else 0
        return self._repo.create(
            customer_id=customer.id,
            status=PitchStatus.ready,
            text=text,
            cache_key=key,
            model=model_id,
            prompt_tokens=prompt_tokens,
            completion_tokens=completion_tokens,
            cost_usd=estimate_cost(model_id, prompt_tokens, completion_tokens),
            grounding_ok=True,
        )

    def _done_event(self, pitch: Pitch, *, cache_hit: bool, stale: bool = False) -> SseEvent:
        return SseEvent(
            "done",
            {
                "pitch_id": pitch.id,
                "model": pitch.model,
                "cache_hit": cache_hit,
                "stale": stale,
                "grounding_ok": pitch.grounding_ok,
                "cost_usd": pitch.cost_usd,
                "prompt_tokens": pitch.prompt_tokens,
                "completion_tokens": pitch.completion_tokens,
                "trace_id": get_trace_id(),
            },
        )

    def _log(
        self,
        customer: Customer,
        pitch: Pitch,
        *,
        cache_hit: bool,
        hop: str,
        started: float,
        outcome: str,
    ) -> None:
        logger.info(
            "pitch generated",
            extra={
                "ctx_customer_id": customer.id,
                "ctx_outcome": outcome,
                "ctx_model": pitch.model,
                "ctx_cache_hit": cache_hit,
                "ctx_prompt_tokens": pitch.prompt_tokens,
                "ctx_completion_tokens": pitch.completion_tokens,
                "ctx_cost_usd": pitch.cost_usd,
                "ctx_latency_ms": round((time.monotonic() - started) * 1000, 1),
                "ctx_grounding_ok": pitch.grounding_ok,
                "ctx_fallback_hop": hop,
            },
        )
        METRICS.inc("pitch_generations_total", {"outcome": outcome})
        # Tokens/cost only for a fresh generation — a last-cached fallback replays an already-counted pitch.
        if outcome == "generated":
            METRICS.inc("pitch_tokens_total", amount=pitch.prompt_tokens + pitch.completion_tokens)
            METRICS.inc("pitch_cost_usd_total", amount=pitch.cost_usd)
