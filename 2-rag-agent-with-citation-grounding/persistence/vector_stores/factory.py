"""Create vector-store adapters from a requested backend name."""

from collections.abc import Callable

from persistence.vector_stores.interfaces import VectorStore


class VectorStoreFactory:
    """Create stores from builders registered by the application."""

    def __init__(self) -> None:
        self._store_builders: dict[str, Callable[[], VectorStore]] = {}

    def register(
        self,
        backend_name: str,
        store_builder: Callable[[], VectorStore],
    ) -> None:
        """Register a store builder under a normalized backend name."""

        name = backend_name.strip().lower()
        if not name:
            raise ValueError("backend_name must be non-empty text")
        if name in self._store_builders:
            raise ValueError(f"Vector store is already registered: {backend_name}")
        self._store_builders[name] = store_builder

    def create(self, backend_name: str) -> VectorStore:
        """Create the vector store requested by name."""

        name = backend_name.strip().lower()
        store_builder = self._store_builders.get(name)
        if store_builder is None:
            raise ValueError(f"Unsupported vector store: {backend_name}")
        return store_builder()
