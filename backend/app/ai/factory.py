import os

from dotenv import load_dotenv

from app.ai.base import AIProvider
from app.ai.ollama import OllamaProvider
from app.ai.openai_provider import OpenAIProvider


load_dotenv()


def get_ai_provider() -> AIProvider:
    provider = os.getenv(
        "AI_PROVIDER",
        "local",
    ).strip().lower()

    if provider in {
        "local",
        "ollama",
    }:
        return OllamaProvider()

    if provider == "openai":
        return OpenAIProvider()

    raise ValueError(
        f"Unsupported AI_PROVIDER: {provider}"
    )