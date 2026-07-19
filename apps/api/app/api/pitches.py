"""Pitch controllers.

Single-pitch generation streams over SSE (spec §4.10). Bulk generation (spec §4.7) fans out over
FastAPI `BackgroundTasks`, tracks live X-of-N progress in an in-memory registry, and exposes both a
poll endpoint and an SSE progress stream (with a best-effort DB reconstruction when the registry no
longer holds the batch — e.g. after a restart).
"""

from __future__ import annotations

import json
from collections.abc import AsyncIterator

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session, sessionmaker

from app.ai.llm_provider import LLMChain, get_llm_chain
from app.ai.single_flight import SingleFlight, get_single_flight
from app.core.config import settings
from app.db.session import get_session_factory
from app.repositories.batch_repository import SqlBatchRepository, get_batch_repository
from app.repositories.customer_repository import SqlCustomerRepository, get_customer_repository
from app.repositories.pitch_repository import SqlPitchRepository, get_pitch_repository
from app.schemas.pitch import (
    BulkBatchCreated,
    BulkBatchStatus,
    BulkItemStatus,
    BulkPitchRequest,
    PitchGenerateRequest,
)
from app.services.batch_registry import BatchRegistry, BatchSnapshot, ItemState, get_batch_registry
from app.services.bulk_pitch_service import run_batch
from app.services.offer_service import build_offer_ladder
from app.services.pitch_service import PitchService, SseEvent

router = APIRouter(tags=["pitches"])


def _sse(event: str, data: dict) -> str:
    return f"event: {event}\ndata: {json.dumps(data)}\n\n"


def _format_sse(event: SseEvent) -> str:
    return _sse(event.event, event.data)


_SSE_HEADERS = {"Cache-Control": "no-cache", "X-Accel-Buffering": "no"}


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

    return StreamingResponse(event_stream(), media_type="text/event-stream", headers=_SSE_HEADERS)


# --- Bulk generation (spec §4.7) ---


@router.post("/pitches/bulk", response_model=BulkBatchCreated)
async def generate_pitches_bulk(
    body: BulkPitchRequest,
    background_tasks: BackgroundTasks,
    batch_repo: SqlBatchRepository = Depends(get_batch_repository),
    session_factory: sessionmaker[Session] = Depends(get_session_factory),
    chain: LLMChain = Depends(get_llm_chain),
    single_flight: SingleFlight = Depends(get_single_flight),
    registry: BatchRegistry = Depends(get_batch_registry),
) -> BulkBatchCreated:
    # Dedup while preserving order so `total` matches the registry's per-customer item set.
    customer_ids = list(dict.fromkeys(body.customer_ids))
    batch = batch_repo.create(customer_ids, total=len(customer_ids))
    registry.create(batch.id, customer_ids)

    background_tasks.add_task(
        run_batch,
        batch.id,
        customer_ids,
        session_factory=session_factory,
        chain=chain,
        single_flight=single_flight,
        registry=registry,
        concurrency=settings.bulk_concurrency,
        force=body.force,
    )
    return BulkBatchCreated(batch_id=batch.id, total=len(customer_ids))


# async (not sync) so it reads the event-loop-mutated registry on the loop, never a threadpool thread.
@router.get("/pitches/bulk/{batch_id}", response_model=BulkBatchStatus)
async def get_bulk_status(
    batch_id: int,
    batch_repo: SqlBatchRepository = Depends(get_batch_repository),
    pitch_repo: SqlPitchRepository = Depends(get_pitch_repository),
    registry: BatchRegistry = Depends(get_batch_registry),
) -> BulkBatchStatus:
    snap = registry.snapshot(batch_id) or _db_fallback_snapshot(batch_id, batch_repo, pitch_repo)
    if snap is None:
        raise HTTPException(status_code=404, detail="Batch not found")
    return _to_status(snap)


@router.get("/pitches/bulk/{batch_id}/stream")
async def stream_bulk_status(
    batch_id: int,
    batch_repo: SqlBatchRepository = Depends(get_batch_repository),
    pitch_repo: SqlPitchRepository = Depends(get_pitch_repository),
    registry: BatchRegistry = Depends(get_batch_registry),
) -> StreamingResponse:
    if not registry.has(batch_id):
        # Not live (restart / evicted) → one-shot reconstructed snapshot, then close.
        snap = _db_fallback_snapshot(batch_id, batch_repo, pitch_repo)
        if snap is None:
            raise HTTPException(status_code=404, detail="Batch not found")

        async def once() -> AsyncIterator[str]:
            yield _sse("progress", _progress_payload(snap))
            yield _sse("done", _done_payload(snap))

        return StreamingResponse(once(), media_type="text/event-stream", headers=_SSE_HEADERS)

    async def event_stream() -> AsyncIterator[str]:
        snap = registry.snapshot(batch_id)
        if snap is None:  # raced with eviction
            return
        yield _sse("progress", _progress_payload(snap))
        last_version = snap.version
        while not snap.complete:
            last_version = await registry.wait_for_change(batch_id, last_version)
            snap = registry.snapshot(batch_id)
            if snap is None:
                return
            yield _sse("progress", _progress_payload(snap))
        yield _sse("done", _done_payload(snap))

    return StreamingResponse(event_stream(), media_type="text/event-stream", headers=_SSE_HEADERS)


def _db_fallback_snapshot(
    batch_id: int, batch_repo: SqlBatchRepository, pitch_repo: SqlPitchRepository
) -> BatchSnapshot | None:
    """Reconstruct a batch's state from the DB when the registry no longer holds it.

    Best-effort: we count a customer `succeeded` only if they have a ready pitch generated at/after
    this batch was created (a pre-existing pitch from an earlier single/bulk run must not be
    miscounted as this batch's success). We can't distinguish "failed" from "never ran" for the rest,
    so those are reported `pending`. Flagged `live=False` for the caller.
    """
    batch = batch_repo.get(batch_id)
    if batch is None:
        return None

    items: list[ItemState] = []
    all_ready = True
    for customer_id in batch.customer_ids:
        pitch = pitch_repo.get_latest_ready_for_customer(
            customer_id, created_since=batch.created_at
        )
        if pitch is not None:
            items.append(ItemState(customer_id=customer_id, status="succeeded", pitch_id=pitch.id))
        else:
            items.append(ItemState(customer_id=customer_id, status="pending"))
            all_ready = False

    return BatchSnapshot(
        batch_id=batch.id,
        total=batch.total,
        version=0,
        complete=all_ready,
        live=False,
        items=tuple(items),
    )


def _to_status(snap: BatchSnapshot) -> BulkBatchStatus:
    return BulkBatchStatus(
        batch_id=snap.batch_id,
        total=snap.total,
        completed=snap.completed,
        succeeded=snap.succeeded,
        failed=snap.failed,
        running=snap.running,
        pending=snap.pending,
        complete=snap.complete,
        live=snap.live,
        items=[
            BulkItemStatus(
                customer_id=i.customer_id, status=i.status, pitch_id=i.pitch_id, error=i.error
            )
            for i in snap.items
        ],
    )


def _progress_payload(snap: BatchSnapshot) -> dict:
    return {
        "completed": snap.completed,
        "total": snap.total,
        "succeeded": snap.succeeded,
        "failed": snap.failed,
        "running": snap.running,
        "pending": snap.pending,
    }


def _done_payload(snap: BatchSnapshot) -> dict:
    return {"total": snap.total, "succeeded": snap.succeeded, "failed": snap.failed}
