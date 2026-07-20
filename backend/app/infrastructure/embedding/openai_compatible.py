"""OpenAI-compatible embedding adapter for hosted or local BGE-M3 services."""

from __future__ import annotations

from typing import Any, Callable

from openai import (
    APIConnectionError,
    APIStatusError,
    APITimeoutError,
    AuthenticationError,
    OpenAI,
    RateLimitError,
)

from .provider import (
    EmbeddingConfigurationError,
    EmbeddingProvider,
    EmbeddingResponseError,
    EmbeddingServiceError,
    normalize_vector,
)


class OpenAICompatibleEmbeddingProvider(EmbeddingProvider):
    """Call a configurable OpenAI-compatible embeddings endpoint."""

    def __init__(
        self,
        *,
        model: str,
        dimension: int,
        base_url: str,
        api_key: str,
        client_factory: Callable[..., Any] | None = None,
    ) -> None:
        self.model = model.strip()
        self._dimension = dimension
        self.base_url = base_url.strip()
        self.api_key = api_key.strip()
        self.client_factory = client_factory

    @property
    def dimension(self) -> int:
        return self._dimension

    def _client(self) -> Any:
        if not self.model or not self.base_url or not self.api_key:
            raise EmbeddingConfigurationError(
                "embedding service is not configured; set model, base URL, and API key",
                status_code=503,
            )
        factory = self.client_factory or OpenAI
        return factory(
            api_key=self.api_key,
            base_url=self.base_url,
            timeout=30.0,
            max_retries=1,
        )

    def embed_texts(self, texts: list[str]) -> list[list[float]]:
        if not texts:
            return []
        if any(not text.strip() for text in texts):
            raise EmbeddingResponseError("embedding input must not be blank")
        try:
            response = self._client().embeddings.create(model=self.model, input=texts)
        except EmbeddingServiceError:
            raise
        except APITimeoutError as exc:
            raise EmbeddingServiceError("embedding request timed out", status_code=504) from exc
        except AuthenticationError as exc:
            raise EmbeddingServiceError("embedding authentication failed", status_code=502) from exc
        except RateLimitError as exc:
            raise EmbeddingServiceError("embedding rate limit exceeded", status_code=503) from exc
        except APIConnectionError as exc:
            raise EmbeddingServiceError("cannot connect to embedding service", status_code=502) from exc
        except APIStatusError as exc:
            raise EmbeddingServiceError("embedding service is unavailable", status_code=502) from exc

        try:
            ordered = sorted(response.data, key=lambda item: item.index)
            vectors = [list(item.embedding) for item in ordered]
        except (AttributeError, TypeError) as exc:
            raise EmbeddingResponseError("embedding response format is invalid") from exc
        if len(vectors) != len(texts):
            raise EmbeddingResponseError("embedding response count does not match input count")
        return [normalize_vector(vector, self.dimension) for vector in vectors]

    def embed_query(self, query: str) -> list[float]:
        if not query.strip():
            raise EmbeddingResponseError("query must not be blank")
        return self.embed_texts([query])[0]
