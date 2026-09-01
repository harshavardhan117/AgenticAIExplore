"""Contracts that every embedding provider must satisfy."""

from typing import Protocol

from embedding_pipeline.embeddings.data_models import EmbeddingRequest, EmbeddingResponse


class EmbeddingProvider(Protocol):
    """Create a normalized vector from provider-neutral text input."""

    def embed(self, request: EmbeddingRequest) -> EmbeddingResponse:
        """Embed one text value and return its vector."""
        ...
