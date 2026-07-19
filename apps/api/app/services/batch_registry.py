"""In-memory bulk-batch progress registry (spec §4.7).

The source of truth for *live* X-of-N progress. A process-wide instance lives on `app.state` (built in
`create_app`, like the single-flight registry) so every request and background worker shares it. SSE
subscribers block on a per-batch `asyncio.Condition` + monotonic version counter, so a subscriber that
joins late (or reconnects) can pass the last version it saw and never miss the terminal state.

Durability is out of scope (docs §8): a process restart drops in-flight batches here. The bulk routes
fall back to a best-effort DB reconstruction (`live=False`) via the `pitch_batches` table.
"""

from __future__ import annotations

import asyncio
from collections.abc import Callable
from dataclasses import dataclass, field, replace
from typing import Literal

from fastapi import Request

ItemStatus = Literal["pending", "running", "succeeded", "failed"]


@dataclass(frozen=True)
class ItemState:
    customer_id: str
    status: ItemStatus = "pending"
    pitch_id: int | None = None
    error: str | None = None


@dataclass(frozen=True)
class BatchSnapshot:
    """Immutable point-in-time view of a batch (returned to poll/stream callers)."""

    batch_id: int
    total: int
    version: int
    complete: bool
    live: bool  # True from the registry; False when reconstructed from the DB
    items: tuple[ItemState, ...]

    @property
    def succeeded(self) -> int:
        return sum(1 for i in self.items if i.status == "succeeded")

    @property
    def failed(self) -> int:
        return sum(1 for i in self.items if i.status == "failed")

    @property
    def running(self) -> int:
        return sum(1 for i in self.items if i.status == "running")

    @property
    def pending(self) -> int:
        return sum(1 for i in self.items if i.status == "pending")

    @property
    def completed(self) -> int:
        """Items that have reached a terminal state (succeeded or failed)."""
        return self.succeeded + self.failed


@dataclass
class _Batch:
    batch_id: int
    items: dict[str, ItemState]
    complete: bool = False
    version: int = 0
    cond: asyncio.Condition = field(default_factory=asyncio.Condition)


class BatchRegistry:
    def __init__(self) -> None:
        self._batches: dict[int, _Batch] = {}

    def create(self, batch_id: int, customer_ids: list[str]) -> None:
        self._batches[batch_id] = _Batch(
            batch_id=batch_id,
            items={cid: ItemState(customer_id=cid) for cid in customer_ids},
        )

    def has(self, batch_id: int) -> bool:
        return batch_id in self._batches

    def snapshot(self, batch_id: int) -> BatchSnapshot | None:
        batch = self._batches.get(batch_id)
        if batch is None:
            return None
        # Read atomically — no awaits between accesses in single-threaded asyncio.
        return BatchSnapshot(
            batch_id=batch.batch_id,
            total=len(batch.items),
            version=batch.version,
            complete=batch.complete,
            live=True,
            items=tuple(batch.items.values()),
        )

    async def wait_for_change(self, batch_id: int, last_version: int) -> int:
        """Block until the batch advances past `last_version`; return the new version.

        Returns immediately if the batch already moved (or is gone). Callers re-`snapshot` after.
        """
        batch = self._batches.get(batch_id)
        if batch is None:
            return last_version
        async with batch.cond:
            await batch.cond.wait_for(lambda: batch.version > last_version)
            return batch.version

    async def mark_running(self, batch_id: int, customer_id: str) -> None:
        await self._update(batch_id, customer_id, lambda s: replace(s, status="running"))

    async def mark_succeeded(self, batch_id: int, customer_id: str, pitch_id: int | None) -> None:
        await self._update(
            batch_id, customer_id, lambda s: replace(s, status="succeeded", pitch_id=pitch_id)
        )

    async def mark_failed(self, batch_id: int, customer_id: str, error: str) -> None:
        await self._update(
            batch_id, customer_id, lambda s: replace(s, status="failed", error=error)
        )

    async def mark_complete(self, batch_id: int) -> None:
        batch = self._batches.get(batch_id)
        if batch is None:
            return
        async with batch.cond:
            batch.complete = True
            batch.version += 1
            batch.cond.notify_all()

    async def _update(
        self, batch_id: int, customer_id: str, fn: Callable[[ItemState], ItemState]
    ) -> None:
        batch = self._batches.get(batch_id)
        if batch is None or customer_id not in batch.items:
            return
        async with batch.cond:
            batch.items[customer_id] = fn(batch.items[customer_id])
            batch.version += 1
            batch.cond.notify_all()


def get_batch_registry(request: Request) -> BatchRegistry:
    return request.app.state.batch_registry
