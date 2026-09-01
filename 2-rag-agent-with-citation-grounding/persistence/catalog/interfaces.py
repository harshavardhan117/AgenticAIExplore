"""Backend-neutral contract for the relational Confluence content catalog."""

from typing import Protocol

from persistence.catalog.data_models import CatalogChunk, CatalogEmbedding, CatalogPage


class ContentCatalog(Protocol):
    """Persist pages, chunks, and embedding provenance as one consistent catalog."""

    def initialize(self) -> None:
        """Create the schema if it does not yet exist."""
        ...

    def synchronize(
        self,
        pages: list[CatalogPage],
        chunks: list[CatalogChunk],
        embeddings: list[CatalogEmbedding],
    ) -> None:
        """Upsert a complete catalog snapshot in one transaction."""
        ...

    def close(self) -> None:
        """Release backend resources."""
        ...
