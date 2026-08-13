from app.ai.provider import BaseAIProvider
from app.ai.gemini import GeminiProvider
from app.ai.openai import OpenAIProvider
from app.core.config import settings


def get_ai_provider() -> BaseAIProvider:
    provider = settings.AI_PROVIDER.lower()
    if provider == "openai":
        return OpenAIProvider()
    return GeminiProvider()
