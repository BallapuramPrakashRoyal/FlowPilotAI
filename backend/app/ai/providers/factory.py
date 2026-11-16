"""Provider factory for instantiating configured AI engines."""

from typing import Optional
from app.ai.providers.base import BaseAIProvider
from app.ai.providers.gemini import GeminiProvider
from app.ai.providers.ollama import OllamaProvider
from app.ai.providers.mock import MockAIProvider
from app.ai.providers.openai_compatible import OpenAICompatibleProvider
from app.core.config import settings


def get_ai_provider(provider_name: Optional[str] = None) -> BaseAIProvider:
    """Return configured AI provider based on environment variables or explicit preference."""
    pref = (provider_name or settings.DEFAULT_AI_PROVIDER).lower()

    if pref == "gemini" and settings.GEMINI_API_KEY:
        return GeminiProvider(api_key=settings.GEMINI_API_KEY)
    elif pref == "ollama":
        return OllamaProvider(base_url=settings.OLLAMA_BASE_URL)
    elif pref == "mock":
        return MockAIProvider()
    elif pref in {"openai", "openai-compatible"} and settings.OPENAI_API_KEY:
        return OpenAICompatibleProvider()

    # Intelligent fallback: if Gemini key exists use Gemini, otherwise Mock
    if settings.GEMINI_API_KEY:
        return GeminiProvider(api_key=settings.GEMINI_API_KEY)
    if settings.OPENAI_API_KEY:
        return OpenAICompatibleProvider()
    return MockAIProvider()
