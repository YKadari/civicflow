import os
from typing import Any, Protocol

import requests
from openai import OpenAI


class EmbeddingProvider(Protocol):
    def embed(
        self,
        text: str,
    ) -> list[float]:
        ...


class OllamaEmbeddingProvider:
    """
    Local embedding provider used during development.
    """

    def __init__(
        self,
        base_url: str | None = None,
        model: str | None = None,
    ):
        self.base_url = (
            base_url
            or os.getenv(
                "OLLAMA_BASE_URL",
                "http://localhost:11434",
            )
        ).rstrip("/")

        self.model = (
            model
            or os.getenv(
                "OLLAMA_EMBEDDING_MODEL",
                "nomic-embed-text",
            )
        )

    def embed(
        self,
        text: str,
    ) -> list[float]:
        response = requests.post(
            f"{self.base_url}/api/embed",
            json={
                "model": self.model,
                "input": text,
            },
            timeout=60,
        )

        response.raise_for_status()

        data = response.json()

        embeddings = data.get(
            "embeddings"
        )

        if not embeddings:
            raise RuntimeError(
                "Ollama returned no embeddings."
            )

        vector = embeddings[0]

        if len(vector) != 768:
            raise RuntimeError(
                (
                    "Expected a 768-dimensional "
                    "embedding from Ollama, "
                    f"received {len(vector)}."
                )
            )

        return vector


class OpenAIEmbeddingProvider:
    """
    Cloud embedding provider used by the live CivicFlow
    deployment.
    """

    def __init__(
        self,
        model: str | None = None,
        dimensions: int | None = None,
        client: Any | None = None,
    ):
        self.model = (
            model
            or os.getenv(
                "OPENAI_EMBEDDING_MODEL",
                "text-embedding-3-small",
            )
        )

        self.dimensions = (
            dimensions
            if dimensions is not None
            else int(
                os.getenv(
                    "OPENAI_EMBEDDING_DIMENSIONS",
                    "768",
                )
            )
        )

        self.client = (
            client
            if client is not None
            else OpenAI()
        )

    def embed(
        self,
        text: str,
    ) -> list[float]:
        response = (
            self.client.embeddings.create(
                model=self.model,
                input=text,
                dimensions=self.dimensions,
                encoding_format="float",
            )
        )

        if not response.data:
            raise RuntimeError(
                "OpenAI returned no embeddings."
            )

        vector = (
            response.data[0].embedding
        )

        if len(vector) != self.dimensions:
            raise RuntimeError(
                (
                    "Unexpected embedding size. "
                    f"Expected {self.dimensions}, "
                    f"received {len(vector)}."
                )
            )

        return vector


def get_embedding_provider(
) -> EmbeddingProvider:
    provider = os.getenv(
        "EMBEDDING_PROVIDER",
        "local",
    ).strip().lower()

    if provider in {
        "local",
        "ollama",
    }:
        return (
            OllamaEmbeddingProvider()
        )

    if provider == "openai":
        return (
            OpenAIEmbeddingProvider()
        )

    raise ValueError(
        (
            "Unsupported "
            "EMBEDDING_PROVIDER: "
            f"{provider}"
        )
    )


def embed_text(
    text: str,
) -> list[float]:
    """
    Backwards-compatible entry point used by
    CivicFlow policy ingestion and retrieval.
    """

    provider = (
        get_embedding_provider()
    )

    return provider.embed(
        text
    )