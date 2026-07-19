"""Single-flight coalescing (spec §4.5).

Collapses concurrent identical generations (same cache_key) into one in-flight run: the first caller
leads (generates + persists), concurrent callers await the leader's result instead of firing their own
LLM call. A process-wide instance lives on `app.state` so it's shared across requests.
"""

from __future__ import annotations

import asyncio
from typing import TYPE_CHECKING

from fastapi import Request

if TYPE_CHECKING:
    from app.models.pitch import Pitch


class SingleFlight:
    def __init__(self) -> None:
        self._inflight: dict[str, asyncio.Future["Pitch"]] = {}

    def follower(self, key: str) -> "asyncio.Future[Pitch] | None":
        """Return the in-flight future for `key` if a generation is already running, else None."""
        return self._inflight.get(key)

    def lead(self, key: str) -> "asyncio.Future[Pitch]":
        """Register this caller as the leader for `key`; returns the future to resolve when done."""
        future: asyncio.Future[Pitch] = asyncio.get_event_loop().create_future()
        self._inflight[key] = future
        return future

    def finish(
        self,
        key: str,
        future: "asyncio.Future[Pitch]",
        *,
        result: "Pitch | None" = None,
        error: BaseException | None = None,
    ) -> None:
        self._inflight.pop(key, None)
        if future.done():
            return
        if error is not None:
            future.set_exception(error)
        elif result is not None:
            future.set_result(result)
        else:  # neither result nor error → surface as a failure rather than resolve with None
            future.set_exception(RuntimeError("single-flight finished with no result"))


def get_single_flight(request: Request) -> SingleFlight:
    return request.app.state.single_flight
