"""Contract implemented by every Confluence retrieval strategy."""

from typing import Protocol

from rag.models import RAGRequest, RetrievedChunk


class RetrievalStrategy(Protocol):
    """Return citation-ready chunks for one retrieval request."""

    name: str

    def retrieve(self, request: RAGRequest) -> list[RetrievedChunk]:
        """Run this strategy and return ranked chunks."""
        ...
