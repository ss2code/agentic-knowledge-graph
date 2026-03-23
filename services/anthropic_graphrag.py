"""
services/anthropic_graphrag.py — Adapters for neo4j_graphrag using Anthropic + sentence-transformers.

AnthropicLLM implements neo4j_graphrag's LLMInterface so it can drive SimpleKGPipeline.
SentenceTransformerEmbedder implements neo4j_graphrag's Embedder interface for local embeddings.
"""

from __future__ import annotations

import asyncio
import os
import re
from typing import Any, Optional, List, Union

from neo4j_graphrag.llm import LLMInterface, LLMResponse
from neo4j_graphrag.llm.types import LLMResponse
from neo4j_graphrag.types import LLMMessage
from neo4j_graphrag.embeddings.base import Embedder

from services.llm_provider import AnthropicProvider


class AnthropicLLM(LLMInterface):
    """
    Wraps AnthropicProvider to satisfy neo4j_graphrag's LLMInterface.
    Logs every call via BaseAgent-style log_llm_interaction when debug_dir is set.
    """

    def __init__(
        self,
        model_name: str = None,
        model_params: Optional[dict[str, Any]] = None,
        api_key: Optional[str] = None,
        debug_dir: Optional[str] = None,
        module_name: str = "KgPipelineInfoExtractor",
        **kwargs: Any,
    ):
        resolved_name = model_name or AnthropicProvider.DEFAULT_MODEL
        super().__init__(
            model_name=resolved_name,
            model_params=model_params or {},
            **kwargs,
        )
        self.module_name = module_name
        self.log_file = None

        if debug_dir:
            from core.logging_utils import get_log_file_path
            self.log_file = get_log_file_path(debug_dir, module_name)

        self.provider = AnthropicProvider(api_key=api_key)

    @staticmethod
    def _strip_markdown(text: str) -> str:
        """Strip markdown code fences from LLM response."""
        text = text.strip()
        if "```" in text:
            match = re.search(r"```(?:\w+)?\n?(.*?)\n?```", text, re.DOTALL)
            if match:
                text = match.group(1).strip()
        return text

    def invoke(
        self,
        input: str,
        message_history: Optional[Union[List[LLMMessage], Any]] = None,
        system_instruction: Optional[str] = None,
    ) -> LLMResponse:
        text, model_used = self.provider.generate(
            input,
            model=self.model_name,
            system_instruction=system_instruction,
            log_file=self.log_file,
        )
        text = self._strip_markdown(text)
        if self.log_file:
            from core.logging_utils import log_llm_interaction
            log_llm_interaction(
                self.log_file, self.module_name, model_used,
                "invoke", input, text,
            )
        return LLMResponse(content=text)

    async def ainvoke(
        self,
        input: str,
        message_history: Optional[Union[List[LLMMessage], Any]] = None,
        system_instruction: Optional[str] = None,
    ) -> LLMResponse:
        return await asyncio.to_thread(
            self.invoke, input, message_history, system_instruction
        )


class SentenceTransformerEmbedder(Embedder):
    """
    Local embedding adapter using sentence-transformers.
    Implements neo4j_graphrag's Embedder interface for use in SimpleKGPipeline.
    """

    def __init__(self, model: str = "all-MiniLM-L6-v2"):
        super().__init__()
        from sentence_transformers import SentenceTransformer
        self._model = SentenceTransformer(model)

    def embed_query(self, text: str) -> list[float]:
        return self._model.encode(text).tolist()

    def embed_documents(self, texts: list[str]) -> list[list[float]]:
        return [self._model.encode(t).tolist() for t in texts]
