"""Pitch generation orchestration — the reliability core (spec §4.3–§4.8).

`stream_pitch` yields `SseEvent`s: cache-hit replays stored text; a miss runs the fallback chain,
streaming tokens live, verifying the output, regenerating once on an ungrounded result, persisting only
a verified pitch, and coalescing concurrent identical requests via single-flight. Every terminal
outcome emits one structured cost/observability log line.
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
from app.models.customer import Customer
from app.models.pitch import Pitch, PitchStatus
from app.repositories.pitch_repository import PitchRepository
from app.schemas.offer import OfferLadder

logger = logging.getLogger("app.pitch")


@dataclass
class SseEvent:
    event: str  # token | regenerating | fallback | done | error
    data: dict = field(default_factory=dict)


class PitchService:
    def __init__(self, repo: PitchRepository, chain: LLMChain, single_flight: SingleFlight) -> None:
        self._repo = repo
        self._chain = chain
        self._sf = single_flight

    async def stream_pitch(
        self, customer: Customer, ladder: OfferLadder, *, force: bool = False
    ) -> AsyncIterator[SseEvent]:
        ctx = build_grounding(customer, ladder)
        key = cache_key(ctx, self._chain.hops[0].client.model_id, PROMPT_TEMPLATE_VERSION)

        # 1) Cache hit → replay the stored (already-verified) pitch as a stream.
        if not force:
            cached = self._repo.get_ready_by_cache_key(customer.id, key)
            if cached is not None:
                async for event in self._replay(cached, cache_hit=True):
                    yield event
                return

            # 2) A concurrent identical generation is already running → coalesce onto it.
            existing = self._sf.follower(key)
            if existing is not None:
                try:
                    pitch = await existing
                except Exception:  # noqa: BLE001 - leader failed; report a clean error
                    yield SseEvent("error", {"message": "generation failed"})
                    return
                async for event in self._replay(pitch, cache_hit=True):
                    yield event
                return

        # 3) Lead the generation (force bypasses single-flight so it never joins a normal run).
        future = None if force else self._sf.lead(key)
        try:
            pitch: Pitch | None = None
            async for event in self._lead(ctx, customer, key, force=force):
                if isinstance(event, Pitch):
                    pitch = event
                else:
                    yield event
            if future is not None:
                self._sf.finish(key, future, result=pitch)
            if pitch is None:
                yield SseEvent("error", {"message": "could not generate a grounded pitch"})
            else:
                yield self._done_event(pitch, cache_hit=False)
        except Exception as exc:  # noqa: BLE001
            if future is not None:
                self._sf.finish(key, future, error=exc)
            logger.exception("pitch generation crashed", extra={"ctx_customer_id": customer.id})
            yield SseEvent("error", {"message": "generation failed"})

    async def _lead(
        self, ctx: GroundingContext, customer: Customer, key: str, *, force: bool
    ) -> AsyncIterator[SseEvent | Pitch]:
        """Run the fallback chain; yield live token/fallback/regenerating events, then the Pitch."""
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
                    yield SseEvent("fallback", {"hop": hop.name})
                    break  # advance to the next hop

                result = verify_grounding(text, ctx.ladder, ctx.monthly_price)
                if result.ok:
                    pitch = self._persist(customer, key, hop.client.model_id, text, usage)
                    self._log(customer, pitch, cache_hit=False, hop=hop.name, started=started)
                    yield pitch
                    return
                if attempt == 1:
                    yield SseEvent("regenerating", {"reason": result.reason})
                    continue
                yield SseEvent("fallback", {"hop": hop.name})  # exhausted this hop's retry

        # All hops failed → last-cached fallback.
        cached = self._repo.get_latest_ready_for_customer(customer.id)
        if cached is not None:
            async for event in self._replay(cached, cache_hit=True):
                if event.event == "done":
                    continue  # caller emits the final done
                yield event
            yield cached
        # else: leave pitch as None → caller emits a clean error.

    async def _replay(self, pitch: Pitch, *, cache_hit: bool) -> AsyncIterator[SseEvent]:
        for word in (pitch.text or "").split(" "):
            yield SseEvent("token", {"text": word + " "})
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

    def _done_event(self, pitch: Pitch, *, cache_hit: bool) -> SseEvent:
        return SseEvent(
            "done",
            {
                "pitch_id": pitch.id,
                "model": pitch.model,
                "cache_hit": cache_hit,
                "grounding_ok": pitch.grounding_ok,
                "cost_usd": pitch.cost_usd,
                "prompt_tokens": pitch.prompt_tokens,
                "completion_tokens": pitch.completion_tokens,
            },
        )

    def _log(
        self, customer: Customer, pitch: Pitch, *, cache_hit: bool, hop: str, started: float
    ) -> None:
        logger.info(
            "pitch generated",
            extra={
                "ctx_customer_id": customer.id,
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
