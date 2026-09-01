"""Backend-neutral interface that every vector-store adapter must satisfy."""

from typing import Protocol

from embedding_pipeline.records.data_models import EmbeddedChunk
from persistence.vector_stores.data_models import SearchResult, UpsertResult


class VectorStore(Protocol):
    """Persist embedded chunks and retrieve the closest matching chunks."""

    def ensure_ready(self, vector_dimensions: int) -> None:
        """Verify that this backend can store vectors with these dimensions."""
        ...

    def upsert(self, chunks: list[EmbeddedChunk]) -> UpsertResult:
        """Create or replace embedded chunks using their chunk IDs."""
        ...

    def search(
        self,
        query_vector: list[float],
        limit: int = 5,
    ) -> list[SearchResult]:
        """Return up to ``limit`` vector-nearest citation-ready chunks."""
        ...

    def close(self) -> None:
        """Release resources held by the backend client or connection."""
        ...
