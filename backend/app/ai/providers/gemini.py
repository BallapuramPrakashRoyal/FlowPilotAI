"""Google Gemini API Provider implementation with resilient fallback."""

import json
import logging
from typing import Any, Dict, List, Optional
from pydantic import BaseModel

from app.ai.providers.base import BaseAIProvider, AICompletionResponse
from app.ai.providers.mock import MockAIProvider
from app.core.config import settings

logger = logging.getLogger(__name__)


class GeminiProvider(BaseAIProvider):
    """Google Gemini AI Provider with automatic resilience fallback."""

    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or settings.GEMINI_API_KEY
        self._genai = None
        if self.api_key:
            try:
                import google.generativeai as genai
                genai.configure(api_key=self.api_key)
                self._genai = genai
            except Exception as e:
                logger.error(f"Failed to configure Gemini: {e}")

    async def complete(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 2048,
    ) -> AICompletionResponse:
        if not self._genai or not self.api_key:
            return await MockAIProvider().complete(prompt, system_prompt, temperature, max_tokens)

        try:
            model = self._genai.GenerativeModel(
                model_name="gemini-1.5-pro",
                system_instruction=system_prompt if system_prompt else None,
                generation_config={"temperature": temperature, "max_output_tokens": max_tokens},
            )
            response = await model.generate_content_async(prompt)
            text = response.text or ""
            return AICompletionResponse(
                content=text,
                prompt_tokens=len(prompt) // 4,
                completion_tokens=len(text) // 4,
                total_tokens=(len(prompt) + len(text)) // 4,
                model="gemini-1.5-pro",
                provider="gemini",
            )
        except Exception as e:
            logger.warning(f"Gemini completion failed ({e}). Engaging deterministic fallback.")
            return await MockAIProvider().complete(prompt, system_prompt, temperature, max_tokens)

    async def complete_structured(
        self,
        prompt: str,
        schema: type[BaseModel],
        system_prompt: Optional[str] = None,
    ) -> Dict[str, Any]:
        if not self._genai or not self.api_key:
            return await MockAIProvider().complete_structured(prompt, schema, system_prompt)

        schema_json = json.dumps(schema.model_json_schema())
        augmented_system = (
            f"{system_prompt or ''}\n\n"
            f"You MUST return ONLY valid JSON matching this schema:\n{schema_json}\n"
            f"Do not include markdown codeblocks or conversational text."
        )

        try:
            model = self._genai.GenerativeModel(
                model_name="gemini-1.5-pro",
                system_instruction=augmented_system,
                generation_config={"response_mime_type": "application/json"},
            )
            response = await model.generate_content_async(prompt)
            text = response.text or "{}"
            return json.loads(text)
        except Exception as e:
            logger.warning(f"Gemini structured call failed ({e}). Engaging deterministic fallback.")
            return await MockAIProvider().complete_structured(prompt, schema, system_prompt)

    async def get_embedding(self, text: str) -> List[float]:
        if not self._genai or not self.api_key:
            return await MockAIProvider().get_embedding(text)

    async def health_check(self) -> bool:
        return bool(self._genai and self.api_key)

        try:
            result = self._genai.embed_content(
                model="models/text-embedding-004",
                content=text,
            )
            return result.get("embedding", [])
        except Exception as e:
            logger.warning(f"Gemini embedding failed ({e}). Engaging fallback embedding.")
            return await MockAIProvider().get_embedding(text)
