"""Tests for the interchangeable embedding provider contract."""

from types import SimpleNamespace

import pytest

from backend.app.infrastructure.embedding.openai_compatible import (
    OpenAICompatibleEmbeddingProvider,
)
from backend.app.infrastructure.embedding.provider import EmbeddingResponseError


class FakeEmbeddingsEndpoint:
    def __init__(self, vectors: list[list[float]]) -> None:
        self.vectors = vectors
        self.calls: list[dict[str, object]] = []

    def create(self, **kwargs):
        self.calls.append(kwargs)
        return SimpleNamespace(
            data=[
                SimpleNamespace(index=index, embedding=vector)
                for index, vector in enumerate(self.vectors)
            ]
        )


def _provider(endpoint: FakeEmbeddingsEndpoint, dimension: int = 3):
    client = SimpleNamespace(embeddings=endpoint)
    return OpenAICompatibleEmbeddingProvider(
        model="BAAI/bge-m3",
        dimension=dimension,
        base_url="https://embedding.example.test/v1",
        api_key="test-key",
        client_factory=lambda **_kwargs: client,
    )


def test_embed_texts_preserves_order_and_normalizes_vectors() -> None:
    endpoint = FakeEmbeddingsEndpoint([[3.0, 4.0, 0.0], [0.0, 0.0, 2.0]])
    provider = _provider(endpoint)

    vectors = provider.embed_texts(["first", "second"])

    assert vectors == [[0.6, 0.8, 0.0], [0.0, 0.0, 1.0]]
    assert endpoint.calls == [{"model": "BAAI/bge-m3", "input": ["first", "second"]}]


def test_embed_query_uses_the_same_provider_contract() -> None:
    endpoint = FakeEmbeddingsEndpoint([[1.0, 0.0, 0.0]])
    assert _provider(endpoint).embed_query("FastAPI") == [1.0, 0.0, 0.0]


def test_provider_rejects_wrong_vector_dimension() -> None:
    endpoint = FakeEmbeddingsEndpoint([[1.0, 0.0]])
    with pytest.raises(EmbeddingResponseError, match="dimension mismatch"):
        _provider(endpoint).embed_texts(["text"])
