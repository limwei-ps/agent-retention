"""LLM client abstraction + deterministic mock (spec §4.9).

`LLMClient` is the seam every backend implements. `MockLLM` is the default (tests + deployed demo):
it produces a grounded pitch deterministically by reading the marker lines that `prompt.build_prompt`
guarantees, so mock output always passes grounding verification. The real `GeminiLLM` lands in Phase C.
"""

from __future__ import annotations

import asyncio
from collections.abc import AsyncIterator
from dataclasses import dataclass
from typing import Protocol

# Marker lines emitted by prompt.build_prompt so the mock can echo real facts. Real LLMs ignore
# these and read the whole prompt.
CUSTOMER_NAME_LINE = "CUSTOMER_NAME:"
RECOMMENDED_OFFER_LINE = "RECOMMENDED_OFFER:"  # "<plan name> | RM <price> | <term> months"


@dataclass(frozen=True)
class TextDelta:
    text: str


@dataclass(frozen=True)
class UsageInfo:
    prompt_tokens: int
    completion_tokens: int


StreamEvent = TextDelta | UsageInfo


class ProviderError(Exception):
    """Normalized provider failure (mock or real) — triggers a fallback hop (spec §4.6)."""


class LLMClient(Protocol):
    model_id: str

    def generate(self, prompt: str) -> AsyncIterator[StreamEvent]:
        """Stream text deltas, then a final UsageInfo. Raises ProviderError on failure."""
        ...


def _extract(prompt: str, marker: str) -> str:
    for line in prompt.splitlines():
        stripped = line.strip()
        if stripped.startswith(marker):
            return stripped[len(marker) :].strip()
    return ""


class MockLLM:
    """Deterministic, grounded generator. Flags let tests exercise reliability paths."""

    def __init__(
        self,
        model_id: str = "mock",
        *,
        fail: bool = False,
        invalid_mode: bool = False,
        delay_s: float = 0.0,
    ) -> None:
        self.model_id = model_id
        self._fail = fail
        self._invalid = invalid_mode
        self._delay = delay_s

    async def generate(self, prompt: str) -> AsyncIterator[StreamEvent]:
        if self._fail:
            raise ProviderError(f"{self.model_id}: forced failure")

        name = _extract(prompt, CUSTOMER_NAME_LINE) or "there"
        text = self._compose(name, _extract(prompt, RECOMMENDED_OFFER_LINE))

        completion_tokens = 0
        for index, word in enumerate(text.split(" ")):
            completion_tokens += 1
            if self._delay:
                await asyncio.sleep(self._delay)
            yield TextDelta(word if index == 0 else f" {word}")

        yield UsageInfo(prompt_tokens=max(1, len(prompt.split())), completion_tokens=completion_tokens)

    def _compose(self, name: str, offer: str) -> str:
        parts = [p.strip() for p in offer.split("|")] if offer else []
        plan = parts[0] if parts else "your current plan"
        price = parts[1] if len(parts) > 1 else ""
        term = parts[2] if len(parts) > 2 else "24 months"
        if self._invalid:
            price = "RM 1"  # out-of-catalog amount → deliberately fails verification
        return (
            f"Hi {name}, thanks for being with TIME Internet. Based on how you've been using your "
            f"connection, we'd love to keep you with {plan} at {price}/month for {term}. "
            f"It's our best value for your usage. Ready to renew? Reply and we'll sort it out today."
        )
