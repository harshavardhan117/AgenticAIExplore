"""Factory for relational catalog implementations."""

from collections.abc import Callable

from persistence.catalog.interfaces import ContentCatalog


class ContentCatalogFactory:
    """Create named relational catalog adapters from registered builders."""

    def __init__(self) -> None:
        self._catalog_builders: dict[str, Callable[[], ContentCatalog]] = {}

    def register(self, backend_name: str, catalog_builder: Callable[[], ContentCatalog]) -> None:
        """Register one catalog builder under a normalized backend name."""

        name = backend_name.strip().lower()
        if not name:
            raise ValueError("backend_name must be non-empty text")
        if name in self._catalog_builders:
            raise ValueError(f"Catalog backend is already registered: {backend_name}")
        self._catalog_builders[name] = catalog_builder

    def create(self, backend_name: str) -> ContentCatalog:
        """Create the requested catalog backend."""

        catalog_builder = self._catalog_builders.get(backend_name.strip().lower())
        if catalog_builder is None:
            raise ValueError(f"Unsupported catalog backend: {backend_name}")
        return catalog_builder()
