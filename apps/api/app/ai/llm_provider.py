"""LLM chain assembly + the DI seam.

`get_llm_chain()` is the single swap point (mirrors `get_customer_repository`): tests override
`app.dependency_overrides[get_llm_chain]` to inject failing/invalid mocks and exercise the reliability
paths without a network.
"""

from __future__ import annotations

from dataclasses import dataclass

from app.ai.llm_client import LLMClient, MockLLM
from app.core.config import settings


@dataclass(frozen=True)
class LLMHop:
    name: str  # "primary" | "secondary" — used in fallback logging
    client: LLMClient


@dataclass(frozen=True)
class LLMChain:
    hops: tuple[LLMHop, ...]


def get_llm_chain() -> LLMChain:
    if settings.llm_mode == "gemini":
        # Real adapter is wired in Phase C; until then, gemini mode is not available.
        raise RuntimeError(
            "LLM_MODE=gemini is not wired yet (Gemini adapter arrives in Phase C). Use LLM_MODE=mock."
        )
    return LLMChain(hops=(LLMHop("primary", MockLLM()),))
