"""Create or refresh the normalized SQLite catalog from local RAG artifacts."""

from __future__ import annotations

import argparse
from pathlib import Path

from persistence.catalog.factory import ContentCatalogFactory
from persistence.catalog.registration import register_builtin_catalogs
from persistence.catalog.sync_service import CatalogSyncService


PROJECT_ROOT = Path(__file__).resolve().parent
DEFAULT_RAW_PAGES_DIRECTORY = PROJECT_ROOT / "data" / "raw_pages"
DEFAULT_CHUNKS_DIRECTORY = PROJECT_ROOT / "data" / "chunks" / "section_as_chunk_v1"
DEFAULT_EMBEDDED_CHUNKS_DIRECTORY = PROJECT_ROOT / "data" / "embedded_chunks" / "section_as_chunk_v1"
DEFAULT_DATABASE_PATH = PROJECT_ROOT / "data" / "rag_catalog.db"


def parse_arguments() -> argparse.Namespace:
    """Read artifact locations and the target SQLite database path."""

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--database-path", type=Path, default=DEFAULT_DATABASE_PATH)
    parser.add_argument("--raw-pages-dir", type=Path, default=DEFAULT_RAW_PAGES_DIRECTORY)
    parser.add_argument("--chunks-dir", type=Path, default=DEFAULT_CHUNKS_DIRECTORY)
    parser.add_argument(
        "--embedded-chunks-dir",
        type=Path,
        default=DEFAULT_EMBEDDED_CHUNKS_DIRECTORY,
    )
    return parser.parse_args()


def main() -> int:
    """Build relational records and atomically synchronize them into SQLite."""

    arguments = parse_arguments()
    pages, chunks, embeddings = CatalogSyncService().build_records(
        raw_pages_directory=arguments.raw_pages_dir,
        chunks_directory=arguments.chunks_dir,
        embedded_chunks_directory=arguments.embedded_chunks_dir,
    )
    factory = ContentCatalogFactory()
    register_builtin_catalogs(factory, arguments.database_path)
    catalog = factory.create("sqlite")
    try:
        catalog.initialize()
        catalog.synchronize(pages, chunks, embeddings)
    finally:
        catalog.close()

    print(f"SQLite database: {arguments.database_path}")
    print(f"Pages synchronized: {len(pages)}")
    print(f"Chunks synchronized: {len(chunks)}")
    print(f"Embedding records synchronized: {len(embeddings)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
