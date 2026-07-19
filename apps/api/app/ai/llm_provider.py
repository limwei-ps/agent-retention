"""LLM chain assembly + the DI seam.

`get_llm_chain()` is the single swap point (mirrors `get_customer_repository`): tests override
`app.dependency_overrides[get_llm_chain]` to inject failing/invalid mocks and exercise the reliability
paths without a network.
"""

from __future__ import annotations

from dataclasses import dataclass

from app.ai.llm_client import GeminiLLM, LLMClient, MockLLM
from app.core.config import settings


@dataclass(frozen=True)
class LLMHop:
    name: str  # "primary" | "secondary" — used in fallback logging
    client: LLMClient


@dataclass(frozen=True)
class LLMChain:
    hops: tuple[LLMHop, ...]


def get_llm_chain() -> LLMChain:
    """Assemble the fallback chain for the active LLM mode.

    mock   → single deterministic hop (default; also the deployed-demo default).
    gemini → two Vertex AI hops, primary (pro) → secondary (flash), both over one shared client.
    """
    if settings.llm_mode == "gemini":
        return _gemini_chain()
    # SSE_TOKEN_CHUNK_DELAY_MS paces the mock's token stream so streaming is visible in dev/demo/E2E
    # (0 in tests keeps them instant).
    delay_s = settings.sse_token_chunk_delay_ms / 1000
    return LLMChain(hops=(LLMHop("primary", MockLLM(delay_s=delay_s)),))


def _gemini_chain() -> LLMChain:
    if not settings.google_cloud_project:
        raise RuntimeError(
            "LLM_MODE=gemini requires GOOGLE_CLOUD_PROJECT (Vertex AI + ADC). Set it in .env and run "
            "`gcloud auth application-default login`, or switch back to LLM_MODE=mock."
        )

    # Local imports: only the real path pulls in the SDK, keeping the mock/test path import-light.
    from google import genai
    from google.genai import types

    client = genai.Client(
        vertexai=True,
        project=settings.google_cloud_project,
        location=settings.google_cloud_location,
    )
    # Gemini 2.5 are *thinking* models: thinking tokens count against max_output_tokens, so a tight
    # cap (e.g. 512) is spent entirely on thinking and truncates the visible pitch (finish=MAX_TOKENS)
    # before it can state the offer — which then fails grounding verification. Give the pitch ample
    # room and bound thinking so cost/latency stay predictable. Low temperature keeps it grounded.
    config = types.GenerateContentConfig(
        temperature=0.4,
        max_output_tokens=2048,
        thinking_config=types.ThinkingConfig(thinking_budget=512),
    )
    timeout = settings.gemini_timeout_s

    def hop(name: str, model_id: str) -> LLMHop:
        client_impl = GeminiLLM(model_id, client, timeout_s=timeout, generation_config=config)
        return LLMHop(name, client_impl)

    return LLMChain(
        hops=(
            hop("primary", settings.gemini_model_primary),
            hop("secondary", settings.gemini_model_secondary),
        )
    )
