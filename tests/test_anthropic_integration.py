"""
Integration tests using real Anthropic API calls (Haiku model).
All tests are skipped when PROJECT_ANTHROPIC_API_KEY is not set.
Run before git push via .githooks/pre-push.
"""

import os
import pytest

from services.llm_provider import AnthropicProvider
from agents.schema_agent import BaseAgent

_SKIP = not os.getenv("PROJECT_ANTHROPIC_API_KEY")
_SKIP_REASON = "PROJECT_ANTHROPIC_API_KEY not set"


@pytest.mark.skipif(_SKIP, reason=_SKIP_REASON)
def test_haiku_generates_text():
    provider = AnthropicProvider()
    text, model = provider.generate("Say hello in one word.", model="claude-haiku-4-5-20251001")
    assert text.strip(), "Expected non-empty response"
    assert model == "claude-haiku-4-5-20251001"


@pytest.mark.skipif(_SKIP, reason=_SKIP_REASON)
def test_haiku_via_base_agent():
    agent = BaseAgent(model_name="claude-haiku-4-5-20251001")
    text, model = agent._generate('Return {"ok": true}', function_name="integration_test")
    assert text.strip(), "Expected non-empty response"
    assert model == "claude-haiku-4-5-20251001"


@pytest.mark.skipif(_SKIP, reason=_SKIP_REASON)
def test_provider_available_models():
    provider = AnthropicProvider()
    models = provider.available_models()
    assert "claude-haiku-4-5-20251001" in models
    assert "claude-sonnet-4-6" in models


@pytest.mark.skipif(_SKIP, reason=_SKIP_REASON)
def test_haiku_system_instruction():
    provider = AnthropicProvider()
    text, model = provider.generate(
        "What is 2+2?",
        model="claude-haiku-4-5-20251001",
        system_instruction="You are a calculator. Respond with only the numeric answer.",
    )
    assert "4" in text
    assert model == "claude-haiku-4-5-20251001"
