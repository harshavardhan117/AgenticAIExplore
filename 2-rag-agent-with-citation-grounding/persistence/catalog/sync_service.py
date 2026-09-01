"""Build normalized catalog records from raw, chunked, and embedded JSON artifacts."""

from __future__ import annotations

import json
from pathlib import Path

from persistence.catalog.data_models import CatalogChunk, CatalogEmbedding, CatalogPage
from source_processing.chunking.data_models import ChunkedPage
from embedding_pipeline.records.data_models import EmbeddedPage


class CatalogSyncService:
    """Translate existing local pipeline artifacts into relational catalog rows."""

    def build_records(
        self,
        raw_pages_directory: Path,
        chunks_directory: Path,
        embedded_chunks_directory: Path,
    ) -> tuple[list[CatalogPage], list[CatalogChunk], list[CatalogEmbedding]]:
        """Load saved pipeline JSON and return validated relational records."""

        raw_metadata_by_page_id = self._load_raw_metadata(raw_pages_directory)
        chunked_pages = self._load_chunked_pages(chunks_directory)
        embedded_pages_by_page_id = self._load_embedded_pages(embedded_chunks_directory)

        pages: list[CatalogPage] = []
        chunks: list[CatalogChunk] = []
        embeddings: list[CatalogEmbedding] = []
        for chunked_page in chunked_pages:
            raw_metadata = raw_metadata_by_page_id.get(chunked_page.page_id)
            if raw_metadata is None:
                raise ValueError(f"No raw Confluence snapshot found for page {chunked_page.page_id}")

            pages.append(
                CatalogPage(
                    page_id=chunked_page.page_id,
                    title=chunked_page.page_title,
                    page_url=chunked_page.page_url,
                    last_modified=raw_metadata["last_modified"],
                    source_version=chunked_page.source_version,
                )
            )
            chunks.extend(
                CatalogChunk(
                    chunk_id=chunk.chunk_id,
                    page_id=chunked_page.page_id,
                    strategy=chunked_page.strategy,
                    position=chunk.position,
                    heading_path=chunk.heading_path,
                    type=chunk.type,
                    content=chunk.content,
                )
                for chunk in chunked_page.chunks
            )

            embedded_page_and_path = embedded_pages_by_page_id.get(chunked_page.page_id)
            if embedded_page_and_path is None:
                continue
            embedded_page, embedded_path = embedded_page_and_path
            self._validate_embedded_page(chunked_page, embedded_page)
            embeddings.extend(
                CatalogEmbedding(
                    chunk_id=embedded_chunk.chunk_id,
                    embedding_text=embedded_chunk.embedding_text,
                    provider=embedded_chunk.embedding_provider,
                    model=embedded_chunk.embedding_model,
                    dimensions=embedded_chunk.embedding_dimensions,
                    embedded_json_path=str(embedded_path),
                )
                for embedded_chunk in embedded_page.chunks
            )

        return pages, chunks, embeddings

    @staticmethod
    def _load_raw_metadata(raw_pages_directory: Path) -> dict[str, dict[str, str]]:
        """Load the page metadata required by the pages table from raw snapshots."""

        metadata_by_page_id: dict[str, dict[str, str]] = {}
        for path in sorted(raw_pages_directory.glob("*.json")):
            raw_page = json.loads(path.read_text(encoding="utf-8"))
            page_id = str(raw_page["page_id"])
            metadata_by_page_id[page_id] = {
                "last_modified": str(raw_page["last_modified"]),
            }
        return metadata_by_page_id

    @staticmethod
    def _load_chunked_pages(chunks_directory: Path) -> list[ChunkedPage]:
        """Load all minimal chunk JSON files in a deterministic order."""

        paths = sorted(chunks_directory.glob("*.json"))
        if not paths:
            raise ValueError(f"No chunk JSON files found in: {chunks_directory}")
        return [ChunkedPage.model_validate_json(path.read_text(encoding="utf-8")) for path in paths]

    @staticmethod
    def _load_embedded_pages(embedded_chunks_directory: Path) -> dict[str, tuple[EmbeddedPage, Path]]:
        """Load completed embedded-page JSON files keyed by Confluence page ID."""

        embedded_by_page_id: dict[str, tuple[EmbeddedPage, Path]] = {}
        for path in sorted(embedded_chunks_directory.glob("*.json")):
            embedded_page = EmbeddedPage.model_validate_json(path.read_text(encoding="utf-8"))
            embedded_by_page_id[embedded_page.page_id] = (embedded_page, path)
        return embedded_by_page_id

    @staticmethod
    def _validate_embedded_page(chunked_page: ChunkedPage, embedded_page: EmbeddedPage) -> None:
        """Ensure embedding metadata belongs to the current chunked-page snapshot."""

        if embedded_page.source_version != chunked_page.source_version:
            raise ValueError(f"Embedded page version is stale: {chunked_page.page_id}")
        if embedded_page.strategy != chunked_page.strategy:
            raise ValueError(f"Embedded page strategy differs: {chunked_page.page_id}")
