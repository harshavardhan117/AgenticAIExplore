"""Inspect retrieved Confluence chunks without calling the chat model."""

from __future__ import annotations

import argparse
from pathlib import Path

from embedding_pipeline.embeddings.factory import EmbeddingProviderFactory
from embedding_pipeline.embeddings.registration import register_builtin_embedding_providers
from rag.models import RAGRequest
from rag.service import RAGService
from persistence.vector_stores.factory import VectorStoreFactory
from persistence.vector_stores.registration import register_builtin_vector_stores


PROJECT_ROOT = Path(__file__).resolve().parent
DEFAULT_DATABASE_PATH = PROJECT_ROOT / "data" / "rag_catalog.db"


def parse_arguments() -> argparse.Namespace:
    """Read one user question, backend choice, and retrieval limit."""

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("question", help="Natural-language Confluence question to retrieve against.")
    parser.add_argument(
        "--backend",
        choices=("oracle", "opensearch"),
        default="oracle",
        help="Vector backend to query (default: oracle).",
    )
    parser.add_argument("--limit", type=int, default=5, help="Maximum chunks to return (default: 5).")
    parser.add_argument(
        "--database-path",
        type=Path,
        default=DEFAULT_DATABASE_PATH,
        help=f"SQLite citation catalog path (default: {DEFAULT_DATABASE_PATH}).",
    )
    return parser.parse_args()


def build_rag_service(database_path: Path) -> RAGService:
    """Compose the dependencies required by the small runtime RAG service."""

    embedding_factory = EmbeddingProviderFactory()
    register_builtin_embedding_providers(embedding_factory)
    vector_store_factory = VectorStoreFactory()
    register_builtin_vector_stores(vector_store_factory)
    return RAGService(
        embedding_provider=embedding_factory.create("oci"),
        vector_store_factory=vector_store_factory,
        catalog_path=database_path,
    )


def content_preview(content: str, maximum_length: int = 300) -> str:
    """Render source content compactly for this learning-oriented CLI output."""

    normalized = " ".join(content.split())
    return normalized if len(normalized) <= maximum_length else f"{normalized[:maximum_length]}..."


def main() -> int:
    """Execute a common retrieval request and display its citation-ready chunks."""

    arguments = parse_arguments()
    response = build_rag_service(arguments.database_path).retrieve(
        RAGRequest(
            question=arguments.question,
            backend_name=arguments.backend,
            limit=arguments.limit,
        )
    )
    print(f"Question: {arguments.question}")
    print(f"Backend: {arguments.backend}")
    print(f"Results returned: {len(response)}")
    for result in response:
        score_label = "cosine distance" if result.score_kind == "distance" else "k-NN score"
        print(f"\nRank {result.rank} | {score_label}: {result.score:.6f}")
        print(f"  Chunk ID: {result.chunk_id}")
        print(f"  Page ID: {result.page_id}")
        print(f"  Page title: {result.citation.page_title}")
        print(f"  Section heading: {result.heading_path}")
        print(f"  Confluence URL: {result.citation.page_url}")
        print(f"  Content preview: {content_preview(result.content)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
