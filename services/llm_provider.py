"""
services/llm_provider.py — Provider abstraction for LLM backends.

To add a new provider:
1. Subclass BaseLLMProvider
2. Implement generate() and available_models()
3. Set DEFAULT_MODEL

Usage:
    provider = AnthropicProvider()
    text, model_used = provider.generate("Hello", model="claude-haiku-4-5-20251001")
"""

import os
import time
import random
from abc import ABC, abstractmethod


class BaseLLMProvider(ABC):
    """Abstract base for all LLM providers."""

    DEFAULT_MODEL: str = ""

    @abstractmethod
    def generate(
        self,
        prompt: str,
        model: str = None,
        system_instruction: str = None,
    ) -> tuple[str, str]:
        """
        Generate a completion.

        Returns:
            (text, model_used) tuple.
        """

    @abstractmethod
    def available_models(self) -> list[str]:
        """Return ordered list of model IDs for this provider."""


class AnthropicProvider(BaseLLMProvider):
    """LLM provider backed by the Anthropic Messages API."""

    MODELS = [
        "claude-haiku-4-5-20251001",
        "claude-sonnet-4-6",
    ]
    MODEL_LABELS = {
        "claude-haiku-4-5-20251001": "Haiku — fast & cheap",
        "claude-sonnet-4-6": "Sonnet — balanced",
    }
    DEFAULT_MODEL = "claude-haiku-4-5-20251001"

    def __init__(self, api_key: str = None):
        import anthropic

        self.api_key = api_key or os.getenv("PROJECT_ANTHROPIC_API_KEY")
        if not self.api_key:
            raise ValueError(
                "PROJECT_ANTHROPIC_API_KEY not set. Export it in your environment."
            )
        self.client = anthropic.Anthropic(api_key=self.api_key)

    def available_models(self) -> list[str]:
        return list(self.MODELS)

    def generate(
        self,
        prompt: str,
        model: str = None,
        system_instruction: str = None,
        log_file: str = None,
    ) -> tuple[str, str]:
        """
        Call the Anthropic Messages API with retry on rate-limit errors.

        Returns:
            (text, model_used) tuple.
        Raises:
            RuntimeError if all retries fail.
        """
        import anthropic

        model = model or self.DEFAULT_MODEL
        max_retries = 5

        for attempt in range(max_retries):
            try:
                kwargs: dict = {
                    "model": model,
                    "max_tokens": 8192,
                    "messages": [{"role": "user", "content": prompt}],
                }
                if system_instruction:
                    kwargs["system"] = system_instruction

                response = self.client.messages.create(**kwargs)
                return response.content[0].text, model

            except anthropic.RateLimitError:
                if attempt < max_retries - 1:
                    wait = 15 * (2 ** attempt) + random.random()
                    print(
                        f"\033[93m⏳ Anthropic rate limit. Waiting {wait:.1f}s "
                        f"(attempt {attempt + 1}/{max_retries})...\033[0m"
                    )
                    if log_file:
                        from core.logging_utils import log_retry_event
                        log_retry_event(log_file, "AnthropicProvider", model,
                                        attempt + 1, max_retries, wait)
                    time.sleep(wait)
                else:
                    raise RuntimeError(
                        f"Anthropic rate limit persisted after {max_retries} attempts "
                        f"for model {model}."
                    )
            except Exception as e:
                raise RuntimeError(
                    f"Anthropic API error with model {model}: {e}"
                ) from e

        raise RuntimeError(f"All retries exhausted for model {model}.")
