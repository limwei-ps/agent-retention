"""Pitch controllers. Single-pitch generation streams over SSE (spec §4.10)."""

from __future__ import annotations

import json
from collections.abc import AsyncIterator

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse

from app.ai.llm_provider import LLMChain, get_llm_chain
from app.ai.single_flight import SingleFlight, get_single_flight
from app.repositories.customer_repository import SqlCustomerRepository, get_customer_repository
from app.repositories.pitch_repository import SqlPitchRepository, get_pitch_repository
from app.schemas.pitch import PitchGenerateRequest
from app.services.offer_service import build_offer_ladder
from app.services.pitch_service import PitchService, SseEvent

router = APIRouter(tags=["pitches"])


def _format_sse(event: SseEvent) -> str:
    return f"event: {event.event}\ndata: {json.dumps(event.data)}\n\n"


@router.post("/customers/{customer_id}/pitch")
async def generate_pitch(
    customer_id: str,
    body: PitchGenerateRequest | None = None,
    customer_repo: SqlCustomerRepository = Depends(get_customer_repository),
    pitch_repo: SqlPitchRepository = Depends(get_pitch_repository),
    chain: LLMChain = Depends(get_llm_chain),
    single_flight: SingleFlight = Depends(get_single_flight),
) -> StreamingResponse:
    customer = customer_repo.get(customer_id)
    if customer is None:
        raise HTTPException(status_code=404, detail="Customer not found")

    ladder = build_offer_ladder(
        customer.current_plan_id,
        customer.monthly_price,
        customer.tenure_months,
        customer.usage_archetype,
    )
    force = bool(body.force) if body else False
    service = PitchService(pitch_repo, chain, single_flight)

    async def event_stream() -> AsyncIterator[str]:
        async for event in service.stream_pitch(customer, ladder, force=force):
            yield _format_sse(event)

    return StreamingResponse(
        event_stream(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )
