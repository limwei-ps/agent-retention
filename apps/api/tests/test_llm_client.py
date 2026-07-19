import pytest

from app.ai.llm_client import (
    CUSTOMER_NAME_LINE,
    RECOMMENDED_OFFER_LINE,
    MockLLM,
    ProviderError,
    TextDelta,
    UsageInfo,
)
from app.ai.llm_provider import get_llm_chain
from app.ai.pricing import estimate_cost

_PROMPT = f"""You are a retention agent.
{CUSTOMER_NAME_LINE} Alice Tan
{RECOMMENDED_OFFER_LINE} TIME Fibre 500 | RM 159 | 24 months
"""


async def _collect(client, prompt):
    deltas: list[str] = []
    usage: UsageInfo | None = None
    async for event in client.generate(prompt):
        if isinstance(event, TextDelta):
            deltas.append(event.text)
        else:
            usage = event
    return "".join(deltas), usage


async def test_mock_streams_grounded_text_then_usage() -> None:
    text, usage = await _collect(MockLLM(), _PROMPT)
    assert "Alice Tan" in text
    assert "TIME Fibre 500" in text
    assert "RM 159" in text
    assert isinstance(usage, UsageInfo)
    assert usage.completion_tokens > 0


async def test_mock_fail_raises_provider_error() -> None:
    with pytest.raises(ProviderError):
        async for _ in MockLLM(fail=True).generate(_PROMPT):
            pass


async def test_mock_invalid_mode_produces_ungrounded_price() -> None:
    text, _ = await _collect(MockLLM(invalid_mode=True), _PROMPT)
    assert "RM 159" not in text  # real price replaced with an out-of-catalog amount


def test_estimate_cost_mock_is_free_and_gemini_scales() -> None:
    assert estimate_cost("mock", 1000, 1000) == 0.0
    assert estimate_cost("gemini-2.5-flash", 1000, 1000) > 0.0


def test_default_chain_is_mock_single_hop() -> None:
    chain = get_llm_chain()
    assert len(chain.hops) == 1
    assert chain.hops[0].name == "primary"
    assert chain.hops[0].client.model_id == "mock"
