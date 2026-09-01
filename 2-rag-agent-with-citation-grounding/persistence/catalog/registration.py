"""Register relational catalog implementations bundled with the application."""

from pathlib import Path

from persistence.catalog.factory import ContentCatalogFactory
from persistence.catalog.interfaces import ContentCatalog
from persistence.catalog.sqlite_catalog import SqliteContentCatalog
from persistence.catalog.sqlite_config import SqliteCatalogConfig


def register_builtin_catalogs(
    factory: ContentCatalogFactory,
    database_path: Path,
) -> None:
    """Register the local SQLite catalog at the caller-selected file location."""

    factory.register("sqlite", lambda: build_sqlite_catalog(database_path))


def build_sqlite_catalog(database_path: Path) -> ContentCatalog:
    """Create one SQLite content catalog without creating its schema yet."""

    return SqliteContentCatalog(SqliteCatalogConfig(database_path=database_path))
