"""Oracle AI Database adapter for embedded Confluence chunks."""

from __future__ import annotations

from array import array
from typing import Any

from embedding_pipeline.records.data_models import EmbeddedChunk
from persistence.vector_stores.data_models import SearchResult, UpsertResult
from persistence.vector_stores.oracle_config import OracleVectorStoreConfig


class OracleVectorStore:
    """Store and retrieve vectors with Oracle's VECTOR data type."""

    backend_name = "oracle"

    def __init__(
        self,
        config: OracleVectorStoreConfig,
        connection: Any | None = None,
    ) -> None:
        self._config = config
        self._connection = connection or self._connect()
        self._is_initialized = False

    def ensure_ready(self, vector_dimensions: int) -> None:
        """Ensure the table exists before writing vectors to it.

        Oracle's ``VECTOR(*, FLOAT32)`` column accepts any positive vector
        dimension, so the dimension is validated here but does not alter DDL.
        """

        if vector_dimensions < 1:
            raise ValueError("vector_dimensions must be at least 1")
        self.initialize()

    def initialize(self) -> None:
        """Create the embedded-chunk table when it does not already exist."""

        if self._is_initialized:
            return

        try:
            cursor = self._connection.cursor()
            try:
                cursor.execute(self._create_table_sql())
            finally:
                cursor.close()
        except Exception as error:
            if self._oracle_error_code(error) != 955:  # ORA-00955: name already used
                raise
        self._connection.commit()
        self._is_initialized = True

    def upsert(self, chunks: list[EmbeddedChunk]) -> UpsertResult:
        """Create or replace chunks using a MERGE keyed by ``chunk_id``."""

        if not chunks:
            return UpsertResult(backend_name=self.backend_name, stored_count=0)

        vector_dimensions = chunks[0].embedding_dimensions
        if any(chunk.embedding_dimensions != vector_dimensions for chunk in chunks):
            raise ValueError("All chunks in one upsert call must have matching dimensions")
        self.ensure_ready(vector_dimensions)

        cursor = self._connection.cursor()
        try:
            self._set_chunk_input_sizes(cursor)
            for chunk in chunks:
                try:
                    cursor.execute(self._merge_sql(), self._bind_chunk(chunk))
                except Exception as error:
                    raise RuntimeError(
                        f"Oracle upsert failed for chunk {chunk.chunk_id}"
                    ) from error
            self._connection.commit()
        finally:
            cursor.close()
        return UpsertResult(backend_name=self.backend_name, stored_count=len(chunks))

    def search(self, query_vector: list[float], limit: int = 5) -> list[SearchResult]:
        """Return nearest chunks ordered by cosine distance (lowest is best)."""

        if not query_vector:
            raise ValueError("query_vector must contain at least one value")
        if limit < 1:
            raise ValueError("limit must be at least 1")

        cursor = self._connection.cursor()
        try:
            cursor.execute(
                self._search_sql(limit),
                {"query_vector": array("f", query_vector)},
            )
            rows = cursor.fetchall()
        finally:
            cursor.close()

        return [
            SearchResult(
                backend_name=self.backend_name,
                rank=rank,
                score=float(row[11]),
                score_kind="distance",
                chunk_id=row[0],
                page_id=row[1],
                page_title=row[2],
                page_url=row[3],
                source_version=int(row[4]),
                strategy=row[5],
                position=int(row[6]),
                heading_path=row[7],
                type=row[8],
                content=self._read_text_value(row[9]),
            )
            for rank, row in enumerate(rows, start=1)
        ]

    def close(self) -> None:
        """Close the underlying database connection."""

        self._connection.close()

    def _connect(self) -> Any:
        try:
            import oracledb
        except ModuleNotFoundError as error:
            raise RuntimeError(
                "python-oracledb is required for OracleVectorStore. "
                "Install it with: pip install oracledb"
            ) from error

        return oracledb.connect(
            user=self._config.username,
            password=self._config.password.get_secret_value(),
            dsn=self._config.dsn,
        )

    def _create_table_sql(self) -> str:
        return f"""
            CREATE TABLE {self._config.table_name} (
                chunk_id VARCHAR2(255) PRIMARY KEY,
                page_id VARCHAR2(255) NOT NULL,
                page_title VARCHAR2(1000) NOT NULL,
                page_url VARCHAR2(2000) NOT NULL,
                source_version NUMBER(10) NOT NULL,
                strategy VARCHAR2(100) NOT NULL,
                chunk_position NUMBER(10) NOT NULL,
                heading_path VARCHAR2(4000) NOT NULL,
                content_type VARCHAR2(20) NOT NULL,
                content CLOB NOT NULL,
                embedding_text CLOB NOT NULL,
                embedding VECTOR(*, FLOAT32) NOT NULL,
                embedding_provider VARCHAR2(100) NOT NULL,
                embedding_model VARCHAR2(255) NOT NULL,
                updated_at TIMESTAMP DEFAULT SYSTIMESTAMP NOT NULL
            )
        """

    def _merge_sql(self) -> str:
        table_name = self._config.table_name
        return f"""
            MERGE INTO {table_name} target
            USING (SELECT :chunk_id AS chunk_id FROM dual) source
            ON (target.chunk_id = source.chunk_id)
            WHEN MATCHED THEN UPDATE SET
                page_id = :page_id,
                page_title = :page_title,
                page_url = :page_url,
                source_version = :source_version,
                strategy = :strategy,
                chunk_position = :position,
                heading_path = :heading_path,
                content_type = :content_type,
                content = :content,
                embedding_text = :embedding_text,
                embedding = :embedding,
                embedding_provider = :embedding_provider,
                embedding_model = :embedding_model,
                updated_at = SYSTIMESTAMP
            WHEN NOT MATCHED THEN INSERT (
                chunk_id, page_id, page_title, page_url, source_version, strategy,
                chunk_position, heading_path, content_type, content, embedding_text,
                embedding, embedding_provider, embedding_model
            ) VALUES (
                :chunk_id, :page_id, :page_title, :page_url, :source_version, :strategy,
                :position, :heading_path, :content_type, :content, :embedding_text,
                :embedding, :embedding_provider, :embedding_model
            )
        """

    def _search_sql(self, limit: int) -> str:
        return f"""
            SELECT
                chunk_id, page_id, page_title, page_url, source_version, strategy,
                chunk_position, heading_path, content_type, content,
                embedding_model,
                VECTOR_DISTANCE(embedding, :query_vector, COSINE) AS distance
            FROM {self._config.table_name}
            ORDER BY VECTOR_DISTANCE(embedding, :query_vector, COSINE)
            FETCH FIRST {limit} ROWS ONLY
        """

    @staticmethod
    def _bind_chunk(chunk: EmbeddedChunk) -> dict[str, Any]:
        return {
            "chunk_id": chunk.chunk_id,
            "page_id": chunk.page_id,
            "page_title": chunk.page_title,
            "page_url": chunk.page_url,
            "source_version": chunk.source_version,
            "strategy": chunk.strategy,
            "position": chunk.position,
            "heading_path": chunk.heading_path,
            "content_type": chunk.type,
            "content": chunk.content,
            "embedding_text": chunk.embedding_text,
            "embedding": array("f", chunk.embedding),
            "embedding_provider": chunk.embedding_provider,
            "embedding_model": chunk.embedding_model,
        }

    @staticmethod
    def _set_chunk_input_sizes(cursor: Any) -> None:
        """Bind potentially large section text as CLOB rather than inferred VARCHAR."""

        try:
            import oracledb
        except ModuleNotFoundError as error:
            raise RuntimeError(
                "python-oracledb is required for OracleVectorStore. "
                "Install it with: pip install oracledb"
            ) from error
        cursor.setinputsizes(
            content=oracledb.DB_TYPE_CLOB,
            embedding_text=oracledb.DB_TYPE_CLOB,
        )

    @staticmethod
    def _read_text_value(value: Any) -> str:
        """Convert Oracle CLOB values returned by python-oracledb into text."""

        read = getattr(value, "read", None)
        return str(read() if callable(read) else value)

    @staticmethod
    def _oracle_error_code(error: Exception) -> int | None:
        """Extract an Oracle error code without importing the optional driver."""

        if not error.args:
            return None
        return getattr(error.args[0], "code", None)
