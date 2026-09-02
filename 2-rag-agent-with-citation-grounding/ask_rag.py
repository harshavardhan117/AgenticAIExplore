"""Ask a grounded Confluence question using Oracle 23ai or OpenSearch."""

from __future__ import annotations

import argparse
from pathlib import Path

from embedding_pipeline.embeddings.factory import EmbeddingProviderFactory
from embedding_pipeline.embeddings.registration import register_builtin_embedding_providers
from persistence.vector_stores.factory import VectorStoreFactory
from persistence.vector_stores.registration import register_builtin_vector_stores
from rag.models import RAGRequest
from rag.oci_chat import OciChatClient
from rag.service import RAGService


PROJECT_ROOT = Path(__file__).resolve().parent
DEFAULT_DATABASE_PATH = PROJECT_ROOT / "data" / "rag_catalog.db"


def parse_arguments() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("question", help="Natural-language Confluence question to answer.")
    parser.add_argument("--backend", choices=("oracle", "opensearch"), default="oracle")
    parser.add_argument(
        "--retrieval-strategy",
        choices=("dense", "keyword", "hybrid_rrf"),
        default="dense",
    )
    parser.add_argument("--limit", type=int, default=5)
    parser.add_argument("--database-path", type=Path, default=DEFAULT_DATABASE_PATH)
    return parser.parse_args()


def main() -> int:
    arguments = parse_arguments()
    embedding_factory = EmbeddingProviderFactory()
    register_builtin_embedding_providers(embedding_factory)
    vector_store_factory = VectorStoreFactory()
    register_builtin_vector_stores(vector_store_factory)
    service = RAGService(
        embedding_provider=embedding_factory.create("oci"),
        vector_store_factory=vector_store_factory,
        catalog_path=arguments.database_path,
        chat_client=OciChatClient(),
    )
    result = service.ask(
        RAGRequest(
            question=arguments.question,
            backend_name=arguments.backend,
            retrieval_strategy=arguments.retrieval_strategy,
            limit=arguments.limit,
        )
    )
    print(f"Question: {result.question}\n")
    print("Answer:")
    print(result.answer)
    print("\nConfluence sources:")
    for citation in result.citations:
        print(f"- {citation.page_title} ({citation.page_url})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
