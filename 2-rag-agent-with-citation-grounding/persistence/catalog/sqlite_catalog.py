"""SQLite implementation of the normalized Confluence content catalog."""

from __future__ import annotations

import sqlite3
from collections import defaultdict

from persistence.catalog.data_models import CatalogChunk, CatalogEmbedding, CatalogPage
from persistence.catalog.sqlite_config import SqliteCatalogConfig


class SqliteContentCatalog:
    """Store current Confluence pages, chunks, and embedding provenance in SQLite."""

    backend_name = "sqlite"

    def __init__(self, config: SqliteCatalogConfig) -> None:
        self._config = config
        self._connection: sqlite3.Connection | None = None

    def initialize(self) -> None:
        """Open SQLite and create the normalized schema and useful lookup indexes."""

        self._config.database_path.parent.mkdir(parents=True, exist_ok=True)
        connection = self._get_connection()
        connection.executescript(
            """
            CREATE TABLE IF NOT EXISTS pages (
                page_id TEXT PRIMARY KEY,
                title TEXT NOT NULL,
                page_url TEXT NOT NULL,
                last_modified TEXT NOT NULL,
                source_version INTEGER NOT NULL CHECK (source_version >= 1)
            );

            CREATE TABLE IF NOT EXISTS chunks (
                chunk_id TEXT PRIMARY KEY,
                page_id TEXT NOT NULL,
                strategy TEXT NOT NULL,
                position INTEGER NOT NULL CHECK (position >= 0),
                heading_path TEXT NOT NULL,
                chunk_type TEXT NOT NULL,
                content TEXT NOT NULL,
                FOREIGN KEY (page_id) REFERENCES pages(page_id) ON DELETE CASCADE,
                UNIQUE (page_id, strategy, position)
            );

            CREATE TABLE IF NOT EXISTS embeddings (
                chunk_id TEXT PRIMARY KEY,
                embedding_text TEXT NOT NULL,
                provider TEXT NOT NULL,
                model TEXT NOT NULL,
                dimensions INTEGER NOT NULL CHECK (dimensions >= 1),
                embedded_json_path TEXT NOT NULL,
                FOREIGN KEY (chunk_id) REFERENCES chunks(chunk_id) ON DELETE CASCADE
            );

            CREATE INDEX IF NOT EXISTS idx_chunks_page_id ON chunks(page_id);
            CREATE INDEX IF NOT EXISTS idx_embeddings_model ON embeddings(model);
            """
        )
        connection.commit()

    def synchronize(
        self,
        pages: list[CatalogPage],
        chunks: list[CatalogChunk],
        embeddings: list[CatalogEmbedding],
    ) -> None:
        """Upsert current data and remove obsolete chunks for refreshed pages."""

        connection = self._get_connection()
        self._validate_relationships(pages, chunks, embeddings)
        chunks_by_page_and_strategy: dict[tuple[str, str], list[str]] = defaultdict(list)
        for chunk in chunks:
            chunks_by_page_and_strategy[(chunk.page_id, chunk.strategy)].append(chunk.chunk_id)

        with connection:
            connection.executemany(
                """
                INSERT INTO pages (page_id, title, page_url, last_modified, source_version)
                VALUES (:page_id, :title, :page_url, :last_modified, :source_version)
                ON CONFLICT(page_id) DO UPDATE SET
                    title = excluded.title,
                    page_url = excluded.page_url,
                    last_modified = excluded.last_modified,
                    source_version = excluded.source_version
                """,
                [page.model_dump() for page in pages],
            )
            connection.executemany(
                """
                INSERT INTO chunks (
                    chunk_id, page_id, strategy, position, heading_path, chunk_type, content
                ) VALUES (
                    :chunk_id, :page_id, :strategy, :position, :heading_path, :type, :content
                )
                ON CONFLICT(chunk_id) DO UPDATE SET
                    page_id = excluded.page_id,
                    strategy = excluded.strategy,
                    position = excluded.position,
                    heading_path = excluded.heading_path,
                    chunk_type = excluded.chunk_type,
                    content = excluded.content
                """,
                [chunk.model_dump() for chunk in chunks],
            )
            self._delete_obsolete_chunks(connection, chunks_by_page_and_strategy)
            connection.executemany(
                """
                INSERT INTO embeddings (
                    chunk_id, embedding_text, provider, model, dimensions, embedded_json_path
                ) VALUES (
                    :chunk_id, :embedding_text, :provider, :model, :dimensions, :embedded_json_path
                )
                ON CONFLICT(chunk_id) DO UPDATE SET
                    embedding_text = excluded.embedding_text,
                    provider = excluded.provider,
                    model = excluded.model,
                    dimensions = excluded.dimensions,
                    embedded_json_path = excluded.embedded_json_path
                """,
                [embedding.model_dump() for embedding in embeddings],
            )

    def close(self) -> None:
        """Close the SQLite connection, if one was opened."""

        if self._connection is not None:
            self._connection.close()
            self._connection = None

    def _get_connection(self) -> sqlite3.Connection:
        """Return one connection with foreign keys enabled for this process."""

        if self._connection is None:
            self._connection = sqlite3.connect(self._config.database_path)
            self._connection.execute("PRAGMA foreign_keys = ON")
        return self._connection

    @staticmethod
    def _validate_relationships(
        pages: list[CatalogPage],
        chunks: list[CatalogChunk],
        embeddings: list[CatalogEmbedding],
    ) -> None:
        """Fail early when records would violate page/chunk relationships."""

        page_ids = {page.page_id for page in pages}
        chunk_ids = {chunk.chunk_id for chunk in chunks}
        unknown_page_ids = {chunk.page_id for chunk in chunks} - page_ids
        unknown_chunk_ids = {embedding.chunk_id for embedding in embeddings} - chunk_ids
        if unknown_page_ids:
            raise ValueError(f"Chunks reference pages not included in this sync: {sorted(unknown_page_ids)}")
        if unknown_chunk_ids:
            raise ValueError(f"Embeddings reference chunks not included in this sync: {sorted(unknown_chunk_ids)}")

    @staticmethod
    def _delete_obsolete_chunks(
        connection: sqlite3.Connection,
        chunks_by_page_and_strategy: dict[tuple[str, str], list[str]],
    ) -> None:
        """Remove chunks no longer emitted for a synchronized page and strategy."""

        for (page_id, strategy), retained_chunk_ids in chunks_by_page_and_strategy.items():
            placeholders = ", ".join("?" for _ in retained_chunk_ids)
            connection.execute(
                f"DELETE FROM chunks WHERE page_id = ? AND strategy = ? AND chunk_id NOT IN ({placeholders})",
                [page_id, strategy, *retained_chunk_ids],
            )
