"""Keyword retrieval backed by SQLite FTS5 and BM25."""

from rag.models import RAGRequest, RetrievedChunk
from rag.retrieval.catalog_reader import CatalogReader


class KeywordRetrievalStrategy:
    """Search chunk headings and content with SQLite full-text search."""

    name = "keyword"

    def __init__(self, catalog_reader: CatalogReader) -> None:
        self._catalog_reader = catalog_reader

    def retrieve(self, request: RAGRequest) -> list[RetrievedChunk]:
        return self._catalog_reader.keyword_search(request.question, request.limit)
