"""Pinned per-model token pricing for cost accounting (spec §4.8).

Rates are USD per 1k tokens (prompt, completion). Gemini rates are placeholders — confirm against the
provider's current pricing when wiring the real adapter (Phase C).
"""

from __future__ import annotations

MODEL_PRICING: dict[str, tuple[float, float]] = {
    "mock": (0.0, 0.0),
    # placeholders — verify before real use
    "gemini-2.5-pro": (0.00125, 0.005),
    "gemini-2.5-flash": (0.000075, 0.0003),
}


def estimate_cost(model_id: str, prompt_tokens: int, completion_tokens: int) -> float:
    prompt_rate, completion_rate = MODEL_PRICING.get(model_id, (0.0, 0.0))
    return round(prompt_tokens / 1000 * prompt_rate + completion_tokens / 1000 * completion_rate, 6)
