"""OpenAI-compatible chat completion provider."""

import json
from typing import Any, Dict, List, Optional

import httpx
from pydantic import BaseModel

from app.ai.providers.base import AICompletionResponse, BaseAIProvider
from app.core.config import settings


class OpenAICompatibleProvider(BaseAIProvider):
    """Provider for OpenAI-compatible APIs without exposing credentials."""

    def __init__(
        self,
        api_key: Optional[str] = None,
        base_url: Optional[str] = None,
        model: Optional[str] = None,
    ):
        self.api_key = api_key or settings.OPENAI_API_KEY
        self.base_url = (base_url or settings.OPENAI_BASE_URL).rstrip("/")
        self.model = model or settings.OPENAI_MODEL

    async def complete(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 2048,
    ) -> AICompletionResponse:
        if not self.api_key:
            raise RuntimeError("OpenAI-compatible provider is not configured")
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})
        async with httpx.AsyncClient(timeout=settings.AI_REQUEST_TIMEOUT_SECONDS) as client:
            response = await client.post(
                f"{self.base_url}/chat/completions",
                headers={"Authorization": f"Bearer {self.api_key}"},
                json={
                    "model": self.model,
                    "messages": messages,
                    "temperature": temperature,
                    "max_tokens": max_tokens,
                },
            )
            response.raise_for_status()
        data = response.json()
        choice = (data.get("choices") or [{}])[0]
        usage = data.get("usage") or {}
        return AICompletionResponse(
            content=(choice.get("message") or {}).get("content", ""),
            prompt_tokens=usage.get("prompt_tokens", 0),
            completion_tokens=usage.get("completion_tokens", 0),
            total_tokens=usage.get("total_tokens", 0),
            model=data.get("model", self.model),
            provider="openai-compatible",
            finish_reason=choice.get("finish_reason", "stop"),
        )

    async def complete_structured(
        self,
        prompt: str,
        schema: type[BaseModel],
        system_prompt: Optional[str] = None,
    ) -> Dict[str, Any]:
        response = await self.complete(
            prompt=f"{prompt}\n\nReturn only JSON matching this schema:\n{json.dumps(schema.model_json_schema())}",
            system_prompt=system_prompt,
            temperature=0,
        )
        return schema.model_validate_json(response.content).model_dump()

    async def get_embedding(self, text: str) -> List[float]:
        raise NotImplementedError("Embedding is not supported by this provider")

    async def health_check(self) -> bool:
        if not self.api_key:
            return False
        try:
            async with httpx.AsyncClient(timeout=settings.AI_REQUEST_TIMEOUT_SECONDS) as client:
                response = await client.get(
                    f"{self.base_url}/models",
                    headers={"Authorization": f"Bearer {self.api_key}"},
                )
            return response.is_success
        except httpx.HTTPError:
            return False
