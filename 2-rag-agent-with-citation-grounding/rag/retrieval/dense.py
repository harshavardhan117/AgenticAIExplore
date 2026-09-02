"""Dense-vector retrieval through the selected vector-store backend."""

from embedding_pipeline.embeddings.data_models import EmbeddingRequest
from embedding_pipeline.embeddings.interfaces import EmbeddingProvider
from persistence.vector_stores.factory import VectorStoreFactory
from rag.models import Citation, RAGRequest, RetrievedChunk
from rag.retrieval.catalog_reader import CatalogReader


class DenseRetrievalStrategy:
    """Embed the question and return nearest chunks from Oracle or OpenSearch."""

    name = "dense"

    def __init__(
        self,
        embedding_provider: EmbeddingProvider,
        vector_store_factory: VectorStoreFactory,
        catalog_reader: CatalogReader,
    ) -> None:
        self._embedding_provider = embedding_provider
        self._vector_store_factory = vector_store_factory
        self._catalog_reader = catalog_reader

    def retrieve(self, request: RAGRequest) -> list[RetrievedChunk]:
        embedding = self._embedding_provider.embed(
            EmbeddingRequest(text=request.question, input_type="SEARCH_QUERY")
        )
        vector_store = self._vector_store_factory.create(request.backend_name)
        try:
            search_results = vector_store.search(embedding.embedding, limit=request.limit)
        finally:
            vector_store.close()

        pages = self._catalog_reader.find_pages([result.page_id for result in search_results])
        return [
            RetrievedChunk(
                rank=result.rank,
                score=result.score,
                score_kind=result.score_kind,
                chunk_id=result.chunk_id,
                page_id=result.page_id,
                heading_path=result.heading_path,
                content=result.content,
                citation=Citation(
                    page_id=result.page_id,
                    page_title=pages.get(result.page_id, (result.page_title, result.page_url))[0],
                    page_url=pages.get(result.page_id, (result.page_title, result.page_url))[1],
                ),
            )
            for result in search_results
        ]
