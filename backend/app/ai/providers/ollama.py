"""Ollama local models provider implementation."""

import json
import logging
from typing import Any, Dict, List, Optional
import httpx
from pydantic import BaseModel

from app.ai.providers.base import BaseAIProvider, AICompletionResponse
from app.core.config import settings

logger = logging.getLogger(__name__)


class OllamaProvider(BaseAIProvider):
    """Local inference via Ollama HTTP API."""

    def __init__(self, base_url: Optional[str] = None, model: str = "llama3:latest"):
        self.base_url = (base_url or settings.OLLAMA_BASE_URL).rstrip("/")
        self.model = model

    async def complete(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 2048,
    ) -> AICompletionResponse:
        async with httpx.AsyncClient(timeout=settings.AI_REQUEST_TIMEOUT_SECONDS) as client:
            payload = {
                "model": self.model,
                "prompt": prompt,
                "system": system_prompt or "",
                "stream": False,
                "options": {"temperature": temperature, "num_predict": max_tokens},
            }
            res = await client.post(f"{self.base_url}/api/generate", json=payload)
            res.raise_for_status()
            data = res.json()
            content = data.get("response", "")
            return AICompletionResponse(
                content=content,
                prompt_tokens=data.get("prompt_eval_count", len(prompt) // 4),
                completion_tokens=data.get("eval_count", len(content) // 4),
                total_tokens=data.get("prompt_eval_count", 0) + data.get("eval_count", 0),
                model=self.model,
                provider="ollama",
            )

    async def complete_structured(
        self,
        prompt: str,
        schema: type[BaseModel],
        system_prompt: Optional[str] = None,
    ) -> Dict[str, Any]:
        schema_json = json.dumps(schema.model_json_schema())
        augmented_prompt = f"{prompt}\n\nReturn strict JSON matching:\n{schema_json}"
        async with httpx.AsyncClient(timeout=settings.AI_REQUEST_TIMEOUT_SECONDS) as client:
            payload = {
                "model": self.model,
                "prompt": augmented_prompt,
                "system": system_prompt or "",
                "stream": False,
                "format": "json",
            }
            res = await client.post(f"{self.base_url}/api/generate", json=payload)
            res.raise_for_status()
            data = res.json()
            content = data.get("response", "{}")
            return json.loads(content)

    async def get_embedding(self, text: str) -> List[float]:
        async with httpx.AsyncClient(timeout=settings.AI_REQUEST_TIMEOUT_SECONDS) as client:
            res = await client.post(
                f"{self.base_url}/api/embeddings",
                json={"model": self.model, "prompt": text},
            )
            res.raise_for_status()
            return res.json().get("embedding", [])

    async def health_check(self) -> bool:
        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                response = await client.get(f"{self.base_url}/api/tags")
            return response.is_success
        except httpx.HTTPError:
            return False
