"""OpenSearch k-NN adapter for embedded Confluence chunks."""

from __future__ import annotations

from typing import Any

from embedding_pipeline.records.data_models import EmbeddedChunk
from persistence.vector_stores.data_models import SearchResult, UpsertResult
from persistence.vector_stores.opensearch_config import OpenSearchVectorStoreConfig


class OpenSearchVectorStore:
    """Store and retrieve vectors from one OpenSearch k-NN index."""

    backend_name = "opensearch"

    def __init__(
        self,
        config: OpenSearchVectorStoreConfig,
        client: Any | None = None,
    ) -> None:
        self._config = config
        self._client = client or self._connect()

    def ensure_ready(self, vector_dimensions: int) -> None:
        """Ensure the k-NN index exists for vectors of this dimension."""

        self.initialize(vector_dimensions)

    def initialize(self, vector_dimensions: int) -> None:
        """Create the k-NN index if it does not already exist."""

        if vector_dimensions < 1:
            raise ValueError("vector_dimensions must be at least 1")
        if self._client.indices.exists(index=self._config.index_name):
            self._validate_existing_vector_dimensions(vector_dimensions)
            return
        self._client.indices.create(
            index=self._config.index_name,
            body=self._index_definition(vector_dimensions),
        )

    def upsert(self, chunks: list[EmbeddedChunk]) -> UpsertResult:
        """Bulk-index chunks, using ``chunk_id`` as the stable document ID."""

        if not chunks:
            return UpsertResult(backend_name=self.backend_name, stored_count=0)

        vector_dimensions = chunks[0].embedding_dimensions
        if any(chunk.embedding_dimensions != vector_dimensions for chunk in chunks):
            raise ValueError("All chunks in one upsert call must have matching dimensions")
        self.ensure_ready(vector_dimensions)

        operations: list[dict[str, Any]] = []
        for chunk in chunks:
            operations.extend(
                [
                    {"index": {"_index": self._config.index_name, "_id": chunk.chunk_id}},
                    self._document(chunk),
                ]
            )
        response = self._client.bulk(body=operations, refresh="wait_for")
        if response.get("errors"):
            raise RuntimeError("OpenSearch rejected one or more embedded chunks")
        return UpsertResult(backend_name=self.backend_name, stored_count=len(chunks))

    def search(self, query_vector: list[float], limit: int = 5) -> list[SearchResult]:
        """Return vector-nearest chunks using the index's configured k-NN space."""

        if not query_vector:
            raise ValueError("query_vector must contain at least one value")
        if limit < 1:
            raise ValueError("limit must be at least 1")

        response = self._client.search(
            index=self._config.index_name,
            body={
                "size": limit,
                "query": {
                    "knn": {
                        "embedding": {
                            "vector": query_vector,
                            "k": limit,
                        }
                    }
                },
            },
        )
        hits = response.get("hits", {}).get("hits", [])
        return [
            self._to_search_result(hit, rank)
            for rank, hit in enumerate(hits, start=1)
        ]

    def close(self) -> None:
        """Close the underlying OpenSearch client transport."""

        self._client.close()

    def _connect(self) -> Any:
        try:
            from opensearchpy import OpenSearch
        except ModuleNotFoundError as error:
            raise RuntimeError(
                "opensearch-py is required for OpenSearchVectorStore. "
                "Install it with: pip install opensearch-py"
            ) from error

        options: dict[str, Any] = {
            "hosts": [self._config.endpoint],
            "use_ssl": self._config.endpoint.startswith("https://"),
            "verify_certs": self._config.verify_certificates,
        }
        if self._config.username is not None:
            options["http_auth"] = (
                self._config.username,
                self._config.password.get_secret_value(),
            )
        return OpenSearch(**options)

    def _index_definition(self, vector_dimensions: int) -> dict[str, Any]:
        return {
            "settings": {"index": {"knn": True}},
            "mappings": {
                "properties": {
                    "chunk_id": {"type": "keyword"},
                    "page_id": {"type": "keyword"},
                    "page_title": {"type": "text"},
                    "page_url": {"type": "keyword"},
                    "source_version": {"type": "integer"},
                    "strategy": {"type": "keyword"},
                    "position": {"type": "integer"},
                    "heading_path": {"type": "text"},
                    "type": {"type": "keyword"},
                    "content": {"type": "text"},
                    "embedding_text": {"type": "text", "index": False},
                    "embedding": {
                        "type": "knn_vector",
                        "dimension": vector_dimensions,
                        "method": {
                            "name": "hnsw",
                            "engine": self._config.vector_engine,
                            "space_type": self._config.vector_space_type,
                        },
                    },
                    "embedding_provider": {"type": "keyword"},
                    "embedding_model": {"type": "keyword"},
                }
            },
        }

    def _validate_existing_vector_dimensions(self, expected_dimensions: int) -> None:
        """Prevent uploads into an existing index built for a different model size."""

        mapping_response = self._client.indices.get_mapping(index=self._config.index_name)
        properties = mapping_response[self._config.index_name]["mappings"]["properties"]
        actual_dimensions = properties.get("embedding", {}).get("dimension")
        if actual_dimensions != expected_dimensions:
            raise ValueError(
                "Existing OpenSearch index has incompatible embedding dimensions: "
                f"expected {expected_dimensions}, found {actual_dimensions}. "
                "Set OPENSEARCH_INDEX_NAME to a new index or recreate this index."
            )

    @staticmethod
    def _document(chunk: EmbeddedChunk) -> dict[str, Any]:
        return chunk.model_dump()

    def _to_search_result(self, hit: dict[str, Any], rank: int) -> SearchResult:
        source = hit["_source"]
        return SearchResult(
            backend_name=self.backend_name,
            rank=rank,
            score=float(hit["_score"]),
            score_kind="similarity",
            chunk_id=source["chunk_id"],
            page_id=source["page_id"],
            page_title=source["page_title"],
            page_url=source["page_url"],
            source_version=int(source["source_version"]),
            strategy=source["strategy"],
            position=int(source["position"]),
            heading_path=source["heading_path"],
            type=source["type"],
            content=source["content"],
        )
