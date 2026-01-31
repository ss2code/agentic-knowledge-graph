
import os
import asyncio
from typing import Any, List, Optional, Union, Sequence

from neo4j_graphrag.llm.base import LLMInterface
from neo4j_graphrag.embeddings.base import Embedder
from neo4j_graphrag.types import LLMMessage
from neo4j_graphrag.llm.types import LLMResponse
from neo4j_graphrag.exceptions import LLMGenerationError

from google import genai
from google.genai import types

class GeminiLLM(LLMInterface):
    """Adapter for Google Gemini models using the genai library."""

    def __init__(
        self,
        model_name: str = "gemini-3-pro-preview", # Try latest first
        model_params: Optional[dict[str, Any]] = None,
        api_key: Optional[str] = None,
        debug_dir: Optional[str] = None,
        module_name: str = "GeminiGraphRAG",
        **kwargs: Any,
    ):
        super().__init__(model_name, model_params, **kwargs)
        self.api_key = api_key or os.getenv("GEMINI_API_KEY")
        if not self.api_key:
            raise ValueError("GEMINI_API_KEY is required.")
        
        self.client = genai.Client(api_key=self.api_key)
        self.model_name = model_name
        self.fallback_model = "gemini-1.5-pro" # Reliable fallback
        
        self.debug_dir = debug_dir
        self.module_name = module_name
        self.log_file = None
        
        if self.debug_dir:
            from core.logging_utils import get_log_file_path
            self.log_file = get_log_file_path(self.debug_dir, self.module_name)

    def invoke(
        self,
        input: str,
        message_history: Optional[Union[List[LLMMessage], Any]] = None,
        system_instruction: Optional[str] = None,
    ) -> LLMResponse:
        """Synchronous invocation with fallback."""
        
        # 1. Try Primary Model
        try:
            return self._generate(self.model_name, input, system_instruction)
        except Exception as e:
            # 2. Try Fallback if primary fails
            print(f"⚠️ Primary model {self.model_name} failed: {e}")
            print(f"🔄 Falling back to {self.fallback_model}...")
            try:
                return self._generate(self.fallback_model, input, system_instruction, calling_function="invoke_fallback")
            except Exception as e2:
                raise LLMGenerationError(f"Gemini Error (Primary & Fallback failed): {e2}")

    def _generate(self, model, prompt, system_instruction, calling_function="Unknown"):
        """Helper to call generate_content"""
        config = {}
        if self.model_params:
            if 'temperature' in self.model_params:
                    config['temperature'] = self.model_params['temperature']
        
        response = self.client.models.generate_content(
            model=model,
            contents=prompt,
            config=types.GenerateContentConfig(
                system_instruction=system_instruction,
                temperature=config.get('temperature')
            )
        )

        content = response.text
        # print(f"\n[DEBUG] Raw LLM Response ({model}):\n{content}\n[DEBUG] End Raw Response\n")
        
        if self.log_file:
            from core.logging_utils import log_llm_interaction
            log_llm_interaction(self.log_file, self.module_name, model, calling_function, prompt, content, system_instruction)
        
        # Robust JSON Extraction
        start = content.find("{")
        end = content.rfind("}")
        
        if start != -1 and end != -1:
            content = content[start:end+1]
        else:
            # Fallback cleanup if no braces found (unlikely for valid JSON)
            content = content.replace("```json", "").replace("```", "").strip()
            
        return LLMResponse(content=content)

    async def ainvoke(
        self,
        input: str,
        message_history: Optional[Union[List[LLMMessage], Any]] = None,
        system_instruction: Optional[str] = None,
    ) -> LLMResponse:
        """Async invocation."""
        # The genai client supports async via specific async_client or running in thread
        # The v1 genai.Client seems to be sync by default or has async methods?
        # Checking valid methods. Client usually wraps.
        # For now, simplistic sync-in-thread wrapper to satisfy interface
        
        return await asyncio.to_thread(
            self.invoke, input, message_history, system_instruction
        )
        
class GeminiEmbedder(Embedder):
    """Adapter for Google Gemini Embeddings."""
    
    def __init__(self, model: str = "text-embedding-004", api_key: Optional[str] = None):
        super().__init__()
        self.model = model
        self.api_key = api_key or os.getenv("GEMINI_API_KEY")
        if not self.api_key:
            raise ValueError("GEMINI_API_KEY is required.")
        self.client = genai.Client(api_key=self.api_key)

    def embed_query(self, text: str) -> List[float]:
        try:
            result = self.client.models.embed_content(
                model=self.model,
                contents=text,
            )
            return result.embeddings[0].values
        except Exception as e:
            # Fallback or re-raise
            print(f"Embedding failed: {e}")
            return []
