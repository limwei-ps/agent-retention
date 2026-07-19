"""Pinned per-model token pricing for cost accounting (spec §4.8).

Rates are USD per 1k tokens (prompt, completion). Gemini rates are the Vertex AI *standard* tier for
prompts ≤200k tokens, verified against cloud.google.com/vertex-ai/generative-ai/pricing (2026-07).
Our pitch prompts are a few hundred tokens, so the long-context (>200k) tier never applies here.
"""

from __future__ import annotations

MODEL_PRICING: dict[str, tuple[float, float]] = {
    "mock": (0.0, 0.0),
    # Vertex standard tier, ≤200k prompt: pro $1.25/$10 per 1M, flash $0.30/$2.50 per 1M.
    "gemini-2.5-pro": (0.00125, 0.010),
    "gemini-2.5-flash": (0.0003, 0.0025),
}


def estimate_cost(model_id: str, prompt_tokens: int, completion_tokens: int) -> float:
    prompt_rate, completion_rate = MODEL_PRICING.get(model_id, (0.0, 0.0))
    return round(prompt_tokens / 1000 * prompt_rate + completion_tokens / 1000 * completion_rate, 6)
