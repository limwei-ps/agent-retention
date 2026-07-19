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
    return LLMChain(hops=(LLMHop("primary", MockLLM()),))


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
    # Low temperature + bounded output keep the pitch grounded and tight (verification catches drift).
    config = types.GenerateContentConfig(temperature=0.4, max_output_tokens=512)
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
