
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
        model_name: str = "gemini-2.0-flash", # Updated default
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
        """Synchronous invocation with robust fallback."""
        
        # Candidate chain
        candidates = [self.model_name]
        
        # Add explicit fallbacks if not already in candidates
        # "Gemini 3.0" / Higher end models
        known_fallbacks = ["gemini-2.0-pro-exp", "gemini-2.0-flash", "gemini-1.5-pro"]
        
        for fb in known_fallbacks:
            if fb not in candidates and fb != self.model_name:
                candidates.append(fb)
                
        self.last_used_model = None

        errors = []
        for model in candidates:
            try:
                # print(f"{CYAN}Trying model: {model}...{RESET}")
                result = self._generate(model, input, system_instruction)
                self.last_used_model = model
                return result
            except Exception as e:
                # print(f"{YELLOW}⚠️ Model {model} failed: {e}{RESET}")
                errors.append(f"{model}: {e}")
                continue
        
        raise LLMGenerationError(f"All models failed: {errors}")

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
        
        # Check if the content looks like JSON. If so, try to extract it. 
        # But for Text-to-Cypher, we don't ALWAYS want JSON.
        # The prompt for Cypher specifically asks for "ONLY the raw query string".
        # So we should be careful about stripping braces unless it looks like a JSON object wrapper.
        
        # Heuristic: If it starts with { and ends with }, it's likely JSON.
        # Otherwise, if it has ```json ... ``` or similar, extract that.
        # The previous logic blindly extracted between { and }. If Cypher contains { (like in property lookups {name: 'foo'}),
        # it might break it if not careful.
        
        # Only try JSON extraction if it APPEARS to be a JSON response (which usually implies the user asked for it).
        # OR if the caller explicitly handles it.
        # However, for generic usage, we usually strip markdown.
        
        content = content.strip()
        
        # Handle markdown blocks first
        if "```" in content:
            # Extract content from code block if present
            import re
            match = re.search(r"```(?:\w+)?\n?(.*?)\n?```", content, re.DOTALL)
            if match:
                content = match.group(1).strip()
        
        # NOTE: Removing the aggressive JSON extraction logic because it breaks non-JSON outputs (like Cypher queries).
        # Consumers expecting JSON usually handle parsing or use libraries like json_repair.
        # For this agentic KG, most agents (Schema, Extraction) ask for JSON, but TextToCypher asks for String.
        # We'll rely on the agents to parse JSON if they need it.
            
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
    
    def __init__(self, model: str = "models/gemini-embedding-001", api_key: Optional[str] = None):
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
