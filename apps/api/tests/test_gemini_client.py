"""Unit tests for the real Gemini adapter + chain wiring — no network.

A fake genai client (duck-typed to `client.aio.models.generate_content_stream`) drives every path:
delta mapping, usage extraction, usage fallback, and the three failure modes (connect error,
mid-stream error, stall timeout) that must all normalize to `ProviderError` so the fallback chain
fires. The chain-wiring tests monkeypatch `genai.Client` so no ADC/credentials are needed.
"""

from __future__ import annotations

import asyncio
from collections.abc import AsyncIterator
from typing import Any

import pytest

from app.ai.llm_client import GeminiLLM, ProviderError, TextDelta, UsageInfo
from app.ai.llm_provider import get_llm_chain
from app.core.config import settings


class _Usage:
    def __init__(self, prompt_token_count: int | None, candidates_token_count: int | None) -> None:
        self.prompt_token_count = prompt_token_count
        self.candidates_token_count = candidates_token_count


class _Chunk:
    def __init__(self, text: str | None = None, usage_metadata: Any = None) -> None:
        self.text = text
        self.usage_metadata = usage_metadata


class _FakeModels:
    """Stands in for `client.aio.models`. `generate_content_stream` is an async coroutine that
    returns an async iterator, matching the real SDK (`await ...generate_content_stream(...)`)."""

    def __init__(
        self,
        chunks: list[_Chunk] | None = None,
        *,
        connect_error: Exception | None = None,
        mid_stream_error: Exception | None = None,
        stall: bool = False,
    ) -> None:
        self._chunks = chunks or []
        self._connect_error = connect_error
        self._mid_stream_error = mid_stream_error
        self._stall = stall

    async def generate_content_stream(
        self, *, model: str, contents: str, config: Any = None
    ) -> AsyncIterator[_Chunk]:
        if self._connect_error is not None:
            raise self._connect_error
        chunks, mid_error, stall = self._chunks, self._mid_stream_error, self._stall

        async def _gen() -> AsyncIterator[_Chunk]:
            for chunk in chunks:
                yield chunk
            if mid_error is not None:
                raise mid_error
            if stall:
                await asyncio.sleep(3600)  # never terminates → next-chunk wait times out

        return _gen()


class _FakeClient:
    def __init__(self, models: _FakeModels) -> None:
        self.aio = type("_Aio", (), {"models": models})()


def _client(**kwargs: Any) -> _FakeClient:
    return _FakeClient(_FakeModels(**kwargs))


async def _collect(client: GeminiLLM, prompt: str = "hello world") -> tuple[str, UsageInfo | None]:
    deltas: list[str] = []
    usage: UsageInfo | None = None
    async for event in client.generate(prompt):
        if isinstance(event, TextDelta):
            deltas.append(event.text)
        else:
            usage = event
    return "".join(deltas), usage


async def test_streams_deltas_then_usage() -> None:
    fake = _client(
        chunks=[
            _Chunk("Hi Alice, "),
            _Chunk("renew TIME Fibre 500 ", usage_metadata=_Usage(120, 40)),
        ]
    )
    text, usage = await _collect(GeminiLLM("gemini-2.5-pro", fake))
    assert text == "Hi Alice, renew TIME Fibre 500 "
    assert usage == UsageInfo(prompt_tokens=120, completion_tokens=40)


async def test_ignores_empty_text_chunks() -> None:
    fake = _client(chunks=[_Chunk(None), _Chunk("Real text", usage_metadata=_Usage(10, 2))])
    text, usage = await _collect(GeminiLLM("gemini-2.5-flash", fake))
    assert text == "Real text"
    assert usage is not None and usage.completion_tokens == 2


async def test_missing_usage_falls_back_to_estimate() -> None:
    fake = _client(chunks=[_Chunk("one two three")])  # no usage_metadata anywhere
    _, usage = await _collect(GeminiLLM("gemini-2.5-pro", fake))
    assert usage is not None
    assert usage.completion_tokens == 3  # estimated from streamed words


async def test_zero_completion_usage_is_backfilled_from_stream() -> None:
    fake = _client(chunks=[_Chunk("a b", usage_metadata=_Usage(50, 0))])
    _, usage = await _collect(GeminiLLM("gemini-2.5-pro", fake))
    assert usage == UsageInfo(prompt_tokens=50, completion_tokens=2)


async def test_connect_error_becomes_provider_error() -> None:
    fake = _client(connect_error=RuntimeError("vertex unreachable"))
    with pytest.raises(ProviderError):
        await _collect(GeminiLLM("gemini-2.5-pro", fake))


async def test_mid_stream_error_becomes_provider_error() -> None:
    fake = _client(chunks=[_Chunk("partial ")], mid_stream_error=RuntimeError("API 500"))
    with pytest.raises(ProviderError):
        await _collect(GeminiLLM("gemini-2.5-pro", fake))


async def test_stall_times_out_as_provider_error() -> None:
    fake = _client(chunks=[_Chunk("slow ")], stall=True)
    with pytest.raises(ProviderError):
        await _collect(GeminiLLM("gemini-2.5-pro", fake, timeout_s=0.05))


# --- chain wiring ---------------------------------------------------------------------------------


async def test_gemini_mode_without_project_raises(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(settings, "llm_mode", "gemini")
    monkeypatch.setattr(settings, "google_cloud_project", None)
    with pytest.raises(RuntimeError, match="GOOGLE_CLOUD_PROJECT"):
        get_llm_chain()


async def test_gemini_mode_builds_two_hop_chain(monkeypatch: pytest.MonkeyPatch) -> None:
    import google.genai as genai_mod

    monkeypatch.setattr(settings, "llm_mode", "gemini")
    monkeypatch.setattr(settings, "google_cloud_project", "test-project")
    monkeypatch.setattr(genai_mod, "Client", lambda **kwargs: _client())

    chain = get_llm_chain()
    assert [hop.name for hop in chain.hops] == ["primary", "secondary"]
    assert chain.hops[0].client.model_id == settings.gemini_model_primary
    assert chain.hops[1].client.model_id == settings.gemini_model_secondary


def test_default_mode_is_mock_single_hop() -> None:
    chain = get_llm_chain()  # settings default llm_mode == "mock"
    assert len(chain.hops) == 1
    assert chain.hops[0].client.model_id == "mock"
