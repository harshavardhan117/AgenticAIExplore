"""Upload existing local embeddings to OpenSearch without calling OCI again."""

from __future__ import annotations

import argparse
from pathlib import Path

from embedding_pipeline.records.data_models import EmbeddedChunk, EmbeddedPage
from persistence.vector_stores.factory import VectorStoreFactory
from persistence.vector_stores.registration import register_builtin_vector_stores


PROJECT_ROOT = Path(__file__).resolve().parent
DEFAULT_EMBEDDED_CHUNKS_DIRECTORY = (
    PROJECT_ROOT / "data" / "embedded_chunks" / "section_as_chunk_v1"
)


def parse_arguments() -> argparse.Namespace:
    """Read the local embedded JSON location and OpenSearch bulk batch size."""

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--embedded-chunks-dir",
        type=Path,
        default=DEFAULT_EMBEDDED_CHUNKS_DIRECTORY,
        help=(
            "Directory containing page-level embedded JSON files "
            f"(default: {DEFAULT_EMBEDDED_CHUNKS_DIRECTORY})."
        ),
    )
    parser.add_argument(
        "--batch-size",
        type=int,
        default=100,
        help="Chunks per OpenSearch Bulk API request (default: 100).",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Validate local records and print the plan without contacting OpenSearch.",
    )
    return parser.parse_args()


def load_embedded_chunks(directory: Path) -> list[EmbeddedChunk]:
    """Load all embedded-page JSON files and verify stable unique chunk IDs."""

    paths = sorted(directory.glob("*.json"))
    if not paths:
        raise ValueError(f"No embedded-page JSON files found in: {directory}")

    chunks: list[EmbeddedChunk] = []
    seen_chunk_ids: set[str] = set()
    for path in paths:
        page = EmbeddedPage.model_validate_json(path.read_text(encoding="utf-8"))
        for chunk in page.chunks:
            if chunk.chunk_id in seen_chunk_ids:
                raise ValueError(f"Duplicate chunk ID in embedded JSON files: {chunk.chunk_id}")
            seen_chunk_ids.add(chunk.chunk_id)
            chunks.append(chunk)
    if not chunks:
        raise ValueError("Embedded-page JSON files contain no chunks to upload")
    return chunks


def split_batches(chunks: list[EmbeddedChunk], batch_size: int) -> list[list[EmbeddedChunk]]:
    """Split records into predictable OpenSearch Bulk API request sizes."""

    if batch_size < 1:
        raise ValueError("--batch-size must be at least 1")
    return [chunks[start : start + batch_size] for start in range(0, len(chunks), batch_size)]


def main() -> int:
    """Validate existing vectors and upsert them into the configured OpenSearch index."""

    arguments = parse_arguments()
    chunks = load_embedded_chunks(arguments.embedded_chunks_dir)
    batches = split_batches(chunks, arguments.batch_size)
    dimensions = {chunk.embedding_dimensions for chunk in chunks}
    models = {chunk.embedding_model for chunk in chunks}
    if len(dimensions) != 1:
        raise ValueError(f"Embedded chunks have inconsistent vector dimensions: {sorted(dimensions)}")

    print(f"Embedded chunks found: {len(chunks)}")
    print(f"Vector dimensions: {dimensions.pop()}")
    print(f"Embedding models: {', '.join(sorted(models))}")
    print(f"OpenSearch bulk requests: {len(batches)}")
    if arguments.dry_run:
        print("Dry run only: OpenSearch was not contacted and no documents were written.")
        return 0

    store_factory = VectorStoreFactory()
    register_builtin_vector_stores(store_factory)
    store = store_factory.create("opensearch")
    stored_count = 0
    try:
        store.ensure_ready(chunks[0].embedding_dimensions)
        for batch_number, batch in enumerate(batches, start=1):
            result = store.upsert(batch)
            stored_count += result.stored_count
            print(f"Uploaded request {batch_number}/{len(batches)}: {result.stored_count} chunks")
    finally:
        store.close()

    print("\nOpenSearch upload complete")
    print(f"Documents upserted: {stored_count}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
