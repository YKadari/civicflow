from types import SimpleNamespace

from app.ai.embeddings import (
    OpenAIEmbeddingProvider,
)


class FakeEmbeddings:
    def create(
        self,
        *,
        model,
        input,
        dimensions,
        encoding_format,
    ):
        assert (
            model
            == "test-embedding-model"
        )

        assert input == "test text"

        assert dimensions == 768

        assert (
            encoding_format
            == "float"
        )

        return SimpleNamespace(
            data=[
                SimpleNamespace(
                    embedding=[
                        0.1
                    ] * 768
                )
            ]
        )


class FakeClient:
    def __init__(self):
        self.embeddings = (
            FakeEmbeddings()
        )


def test_openai_embedding_provider():
    provider = (
        OpenAIEmbeddingProvider(
            model=(
                "test-embedding-model"
            ),
            dimensions=768,
            client=FakeClient(),
        )
    )

    result = provider.embed(
        "test text"
    )

    assert len(result) == 768

    assert result[0] == 0.1