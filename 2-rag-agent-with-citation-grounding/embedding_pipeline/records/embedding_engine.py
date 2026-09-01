"""Turn chunked pages into embedded records using a provider-neutral adapter."""

from embedding_pipeline.embeddings.interfaces import EmbeddingProvider
from embedding_pipeline.embeddings.data_models import EmbeddingRequest
from source_processing.chunking.data_models import Chunk, ChunkedPage
from embedding_pipeline.records.embedding_text import build_embedding_text
from embedding_pipeline.records.data_models import EmbeddedChunk


class EmbeddingEngine:
    """Create storage-ready embedded chunks from one chunked Confluence page."""

    def __init__(self, embedding_provider: EmbeddingProvider) -> None:
        self._embedding_provider = embedding_provider

    def embed_chunked_page(self, page: ChunkedPage) -> list[EmbeddedChunk]:
        """Embed every chunk in one page sequentially and preserve page order."""

        return [self.embed_chunk(page, chunk) for chunk in page.chunks]

    def embed_chunk(self, page: ChunkedPage, chunk: Chunk) -> EmbeddedChunk:
        """Embed one chunk and retain all data required for a citation-aware index."""

        embedding_text = build_embedding_text(page, chunk)
        response = self._embedding_provider.embed(
            EmbeddingRequest(text=embedding_text, input_type="SEARCH_DOCUMENT")
        )
        return EmbeddedChunk(
            chunk_id=chunk.chunk_id,
            page_id=page.page_id,
            page_title=page.page_title,
            page_url=page.page_url,
            source_version=page.source_version,
            strategy=page.strategy,
            position=chunk.position,
            heading_path=chunk.heading_path,
            type=chunk.type,
            content=chunk.content,
            embedding_text=embedding_text,
            embedding=response.embedding,
            embedding_provider=response.provider_name,
            embedding_model=response.model_id,
        )
