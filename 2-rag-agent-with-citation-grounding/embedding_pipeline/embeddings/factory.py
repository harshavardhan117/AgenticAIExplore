"""Create embedding-provider adapters from a requested provider name."""

from collections.abc import Callable

from embedding_pipeline.embeddings.interfaces import EmbeddingProvider


class EmbeddingProviderFactory:
    """Create adapters from builders registered by the application."""

    def __init__(self) -> None:
        self._provider_builders: dict[str, Callable[[], EmbeddingProvider]] = {}

    def register(
        self,
        provider_name: str,
        provider_builder: Callable[[], EmbeddingProvider],
    ) -> None:
        """Register an embedding provider under a normalized name."""
        name = provider_name.strip().lower()
        if not name:
            raise ValueError("provider_name must be non-empty text")
        if name in self._provider_builders:
            raise ValueError(f"Provider is already registered: {provider_name}")
        self._provider_builders[name] = provider_builder

    def create(self, provider_name: str) -> EmbeddingProvider:
        """Create the embedding provider requested by name."""
        name = provider_name.strip().lower()
        provider_builder = self._provider_builders.get(name)
        if provider_builder is None:
            raise ValueError(f"Unsupported embedding provider: {provider_name}")
        return provider_builder()
