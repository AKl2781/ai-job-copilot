"""Embedding provider contract, validation, and provider-facing errors."""

from __future__ import annotations

import math
from typing import Protocol


class EmbeddingServiceError(RuntimeError):
    """An embedding failure safe to expose through the API."""

    def __init__(self, public_message: str, status_code: int = 502) -> None:
        super().__init__(public_message)
        self.public_message = public_message
        self.status_code = status_code


class EmbeddingConfigurationError(EmbeddingServiceError):
    """The selected embedding provider is configured incorrectly."""


class EmbeddingResponseError(EmbeddingServiceError):
    """The provider returned invalid vectors."""


class EmbeddingProvider(Protocol):
    """Contract implemented by interchangeable embedding adapters."""

    @property
    def dimension(self) -> int:
        """Return the exact vector dimension produced by this provider."""
        ...

    def embed_texts(self, texts: list[str]) -> list[list[float]]:
        """Embed document texts in input order."""
        ...

    def embed_query(self, query: str) -> list[float]:
        """Embed a retrieval query."""
        ...


def normalize_vector(vector: list[float], expected_dimension: int) -> list[float]:
    """Validate and L2-normalize a provider vector for cosine search."""
    if len(vector) != expected_dimension:
        raise EmbeddingResponseError(
            f"embedding dimension mismatch: expected {expected_dimension}, got {len(vector)}"
        )
    values = [float(value) for value in vector]
    if any(not math.isfinite(value) for value in values):
        raise EmbeddingResponseError("embedding contains a non-finite value")
    norm = math.sqrt(sum(value * value for value in values))
    if norm == 0:
        raise EmbeddingResponseError("embedding vector must not be zero")
    return [value / norm for value in values]
