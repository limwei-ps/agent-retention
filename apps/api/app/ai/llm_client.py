"""LLM client abstraction + deterministic mock + real Gemini adapter (spec §4.9).

`LLMClient` is the seam every backend implements. `MockLLM` is the default (tests + deployed demo):
it produces a grounded pitch deterministically by reading the marker lines that `prompt.build_prompt`
guarantees, so mock output always passes grounding verification. `GeminiLLM` is the real provider
(Vertex AI via Application Default Credentials), wired behind `LLM_MODE=gemini` in `llm_provider`.
"""

from __future__ import annotations

import asyncio
from collections.abc import AsyncIterator
from dataclasses import dataclass
from typing import TYPE_CHECKING, Any, Protocol

if TYPE_CHECKING:  # avoid importing the SDK on the mock/test path
    from google import genai

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

        yield UsageInfo(
            prompt_tokens=max(1, len(prompt.split())), completion_tokens=completion_tokens
        )

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


def _usage_from_metadata(meta: Any) -> UsageInfo:
    """Map a google-genai usage_metadata object to our UsageInfo (defensive: fields may be None)."""
    return UsageInfo(
        prompt_tokens=getattr(meta, "prompt_token_count", None) or 0,
        completion_tokens=getattr(meta, "candidates_token_count", None) or 0,
    )


class GeminiLLM:
    """Real provider: streams a pitch from Gemini on Vertex AI (auth via ADC).

    The `genai.Client` is injected so the test suite can pass a fake and never touch the network.
    Every failure mode — connect error, mid-stream error, or a stall longer than `timeout_s` between
    chunks — is normalized to `ProviderError` so the caller's fallback chain (pro → flash → cached →
    clean error) fires instead of the stream crashing. Usage tokens come from the provider's
    `usage_metadata` (delivered on the final chunk); if absent, a rough estimate keeps cost logging
    honest rather than silently zero.
    """

    def __init__(
        self,
        model_id: str,
        client: genai.Client,
        *,
        timeout_s: float = 30.0,
        generation_config: Any = None,
    ) -> None:
        self.model_id = model_id
        self._client = client
        self._timeout = timeout_s
        self._config = generation_config

    async def generate(self, prompt: str) -> AsyncIterator[StreamEvent]:
        usage: UsageInfo | None = None
        streamed_words = 0
        try:
            kwargs: dict[str, Any] = {"model": self.model_id, "contents": prompt}
            if self._config is not None:
                kwargs["config"] = self._config
            # Bound the connect and each chunk wait: a stalled hop must fail over, not hang.
            stream = await asyncio.wait_for(
                self._client.aio.models.generate_content_stream(**kwargs), timeout=self._timeout
            )
            iterator = stream.__aiter__()
            while True:
                try:
                    chunk = await asyncio.wait_for(iterator.__anext__(), timeout=self._timeout)
                except StopAsyncIteration:
                    break
                text = getattr(chunk, "text", None)
                if text:
                    streamed_words += len(text.split())
                    yield TextDelta(text)
                meta = getattr(chunk, "usage_metadata", None)
                if meta is not None:
                    usage = _usage_from_metadata(meta)
        except TimeoutError as exc:
            raise ProviderError(f"{self.model_id}: timed out after {self._timeout}s") from exc
        except ProviderError:
            raise
        except Exception as exc:  # noqa: BLE001 - normalize any SDK/API error into a fallback trigger
            raise ProviderError(f"{self.model_id}: {type(exc).__name__}: {exc}") from exc

        # Guarantee exactly one terminal UsageInfo, even if the provider omitted or zeroed it.
        if usage is None:
            usage = UsageInfo(prompt_tokens=max(1, len(prompt.split())), completion_tokens=0)
        if usage.completion_tokens == 0 and streamed_words > 0:
            usage = UsageInfo(prompt_tokens=usage.prompt_tokens, completion_tokens=streamed_words)
        yield usage
