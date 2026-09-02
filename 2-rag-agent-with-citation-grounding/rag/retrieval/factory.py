"""Factory for retrieval strategies selected by a request field."""

from collections.abc import Callable

from embedding_pipeline.embeddings.interfaces import EmbeddingProvider
from persistence.vector_stores.factory import VectorStoreFactory
from rag.retrieval.catalog_reader import CatalogReader
from rag.retrieval.dense import DenseRetrievalStrategy
from rag.retrieval.hybrid_rrf import HybridRrfRetrievalStrategy
from rag.retrieval.interfaces import RetrievalStrategy
from rag.retrieval.keyword import KeywordRetrievalStrategy


class RetrievalStrategyFactory:
    """Register and create retrieval strategies using normalized names."""

    def __init__(self) -> None:
        self._builders: dict[str, Callable[[], RetrievalStrategy]] = {}

    def register(self, name: str, builder: Callable[[], RetrievalStrategy]) -> None:
        normalized = name.strip().lower()
        if not normalized:
            raise ValueError("Retrieval strategy name must be non-empty text")
        if normalized in self._builders:
            raise ValueError(f"Retrieval strategy is already registered: {name}")
        self._builders[normalized] = builder

    def create(self, name: str) -> RetrievalStrategy:
        normalized = name.strip().lower()
        builder = self._builders.get(normalized)
        if builder is None:
            raise ValueError(
                f"Unsupported retrieval strategy: {name}. Available: {', '.join(sorted(self._builders))}"
            )
        return builder()


def build_default_retrieval_strategy_factory(
    embedding_provider: EmbeddingProvider,
    vector_store_factory: VectorStoreFactory,
    catalog_reader: CatalogReader,
) -> RetrievalStrategyFactory:
    """Register the strategies included in the prototype."""

    factory = RetrievalStrategyFactory()
    factory.register(
        "dense",
        lambda: DenseRetrievalStrategy(embedding_provider, vector_store_factory, catalog_reader),
    )
    factory.register("keyword", lambda: KeywordRetrievalStrategy(catalog_reader))
    factory.register(
        "hybrid_rrf",
        lambda: HybridRrfRetrievalStrategy(
            DenseRetrievalStrategy(embedding_provider, vector_store_factory, catalog_reader),
            KeywordRetrievalStrategy(catalog_reader),
        ),
    )
    return factory
