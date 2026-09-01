"""Build the contextual text passed to an embedding model."""

from source_processing.chunking.data_models import Chunk, ChunkedPage


def build_embedding_text(page: ChunkedPage, chunk: Chunk) -> str:
    """Combine page context and chunk content into one OCI embedding input."""

    return (
        f"Page title: {page.page_title}\n"
        f"Section: {chunk.heading_path}\n"
        f"Content type: {chunk.type}\n"
        f"Content:\n{chunk.content}"
    )
