import os

from app.ai.base import AIProvider
from app.ai.ollama import OllamaProvider


def get_ai_provider() -> AIProvider:
    provider = os.getenv(
        "AI_PROVIDER",
        "local",
    )

    if provider == "local":
        return OllamaProvider()

    raise ValueError(
        f"Unsupported AI provider: {provider}"
    )