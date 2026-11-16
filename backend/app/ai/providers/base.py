"""Base abstract interface for AI model providers."""

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class AICompletionResponse(BaseModel):
    content: str
    structured_data: Optional[Dict[str, Any]] = None
    prompt_tokens: int = 0
    completion_tokens: int = 0
    total_tokens: int = 0
    model: str = "default"
    finish_reason: str = "stop"
    provider: str = "unknown"


class BaseAIProvider(ABC):
    """Abstract provider for LLM inference and structured outputs."""

    @abstractmethod
    async def complete(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 2048,
    ) -> AICompletionResponse:
        pass

    @abstractmethod
    async def complete_structured(
        self,
        prompt: str,
        schema: type[BaseModel],
        system_prompt: Optional[str] = None,
    ) -> Dict[str, Any]:
        pass

    @abstractmethod
    async def get_embedding(self, text: str) -> List[float]:
        pass

    async def health_check(self) -> bool:
        """Return whether the provider is reachable and configured."""
        return True
