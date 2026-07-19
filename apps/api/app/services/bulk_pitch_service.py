"""Bulk pitch generation — semaphore-bounded fan-out with per-item failure isolation (spec §4.5, §4.7).

Runs as a FastAPI `BackgroundTask`, so it opens its own DB session *per item* (the request session is
already closed by the time this runs) and reports progress to the in-memory `BatchRegistry`. Each item
reuses `PitchService.generate`, inheriting the full single-pitch reliability path (cache, single-flight,
fallback, verify+regenerate, cost logging). One customer failing never aborts the batch.
"""

from __future__ import annotations

import asyncio
import logging

from sqlalchemy.orm import Session, sessionmaker

from app.ai.llm_provider import LLMChain
from app.ai.single_flight import SingleFlight
from app.repositories.customer_repository import SqlCustomerRepository
from app.repositories.pitch_repository import SqlPitchRepository
from app.services.batch_registry import BatchRegistry
from app.services.offer_service import build_offer_ladder
from app.services.pitch_service import PitchService

logger = logging.getLogger("app.pitch.bulk")


async def run_batch(
    batch_id: int,
    customer_ids: list[str],
    *,
    session_factory: sessionmaker[Session],
    chain: LLMChain,
    single_flight: SingleFlight,
    registry: BatchRegistry,
    concurrency: int,
    force: bool = False,
) -> None:
    """Generate pitches for every customer in the batch, capped at `concurrency` at a time."""
    semaphore = asyncio.Semaphore(concurrency)

    async def worker(customer_id: str) -> None:
        async with semaphore:
            await _generate_one(
                batch_id,
                customer_id,
                session_factory=session_factory,
                chain=chain,
                single_flight=single_flight,
                registry=registry,
                force=force,
            )

    # return_exceptions=True is belt-and-braces: _generate_one already isolates every failure, but
    # this guarantees one worker can never abort the gather (and thus the whole batch).
    await asyncio.gather(*(worker(cid) for cid in customer_ids), return_exceptions=True)
    await registry.mark_complete(batch_id)


async def _generate_one(
    batch_id: int,
    customer_id: str,
    *,
    session_factory: sessionmaker[Session],
    chain: LLMChain,
    single_flight: SingleFlight,
    registry: BatchRegistry,
    force: bool,
) -> None:
    """Generate one pitch in its own session; isolate every failure to this item."""
    await registry.mark_running(batch_id, customer_id)
    db = session_factory()
    try:
        customer = SqlCustomerRepository(db).get(customer_id)
        if customer is None:
            await registry.mark_failed(batch_id, customer_id, "customer not found")
            return

        ladder = build_offer_ladder(
            customer.current_plan_id,
            customer.monthly_price,
            customer.tenure_months,
            customer.usage_archetype,
        )
        service = PitchService(SqlPitchRepository(db), chain, single_flight)
        outcome = await service.generate(customer, ladder, force=force)

        if outcome.ok:
            await registry.mark_succeeded(batch_id, customer_id, outcome.pitch_id)
        else:
            await registry.mark_failed(batch_id, customer_id, "generation failed")
    except Exception:  # noqa: BLE001 - isolate: a crash here must not abort the batch
        logger.exception(
            "bulk pitch item crashed",
            extra={"ctx_batch_id": batch_id, "ctx_customer_id": customer_id},
        )
        await registry.mark_failed(batch_id, customer_id, "generation error")
    finally:
        db.close()
