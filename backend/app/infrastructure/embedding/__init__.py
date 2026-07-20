"""Configurable embedding provider construction."""

from ...core.config import Settings
from ..database.vector import BGE_M3_DIMENSION
from .openai_compatible import OpenAICompatibleEmbeddingProvider
from .provider import EmbeddingConfigurationError, EmbeddingProvider


def create_embedding_provider(settings: Settings) -> EmbeddingProvider:
    provider_name = settings.embedding_provider.strip().lower()
    if settings.embedding_dimension != BGE_M3_DIMENSION:
        raise EmbeddingConfigurationError(
            f"EMBEDDING_DIMENSION must match the database vector dimension ({BGE_M3_DIMENSION})",
            status_code=503,
        )
    if provider_name != "openai_compatible":
        raise EmbeddingConfigurationError(
            f"unsupported embedding provider: {provider_name}",
            status_code=503,
        )
    return OpenAICompatibleEmbeddingProvider(
        model=settings.embedding_model,
        dimension=settings.embedding_dimension,
        base_url=settings.embedding_base_url,
        api_key=settings.embedding_api_key,
    )


__all__ = ["EmbeddingProvider", "create_embedding_provider"]
