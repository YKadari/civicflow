import os

import httpx
from dotenv import load_dotenv

from app.ai.exceptions import AIProviderError


load_dotenv()


OLLAMA_BASE_URL = os.getenv(
    "OLLAMA_BASE_URL",
    "http://localhost:11434",
)

OLLAMA_EMBEDDING_MODEL = os.getenv(
    "OLLAMA_EMBEDDING_MODEL",
    "nomic-embed-text",
)


def embed_text(
    text: str,
) -> list[float]:

    try:
        response = httpx.post(
            f"{OLLAMA_BASE_URL}/api/embed",
            json={
                "model": OLLAMA_EMBEDDING_MODEL,
                "input": text,
            },
            timeout=60.0,
        )

        response.raise_for_status()

        data = response.json()

        embeddings = data["embeddings"]

        if not embeddings:
            raise AIProviderError(
                "Embedding provider returned no vectors."
            )

        return embeddings[0]

    except (
        httpx.HTTPError,
        KeyError,
        IndexError,
    ) as exc:
        raise AIProviderError(
            "Unable to generate embedding."
        ) from exc