"""Chunk all locally saved Confluence pages with the minimal section strategy."""

from __future__ import annotations

import argparse
from pathlib import Path

from source_processing.chunking.engine import ChunkingEngine
from source_processing.chunking.factory import build_default_chunking_strategy_factory
from source_processing.chunking.json_writer import ChunkJsonWriter


PROJECT_ROOT = Path(__file__).resolve().parent
DEFAULT_RAW_PAGES_DIRECTORY = PROJECT_ROOT / "data" / "raw_pages"
DEFAULT_OUTPUT_DIRECTORY = PROJECT_ROOT / "data" / "chunks"
MINIMAL_STRATEGY = "section_as_chunk_v1"


def parse_arguments() -> argparse.Namespace:
    """Read optional input and output locations for a batch chunking run."""

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--raw-pages-dir",
        type=Path,
        default=DEFAULT_RAW_PAGES_DIRECTORY,
        help=f"Raw Confluence JSON directory (default: {DEFAULT_RAW_PAGES_DIRECTORY}).",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=DEFAULT_OUTPUT_DIRECTORY,
        help=f"Chunk JSON root directory (default: {DEFAULT_OUTPUT_DIRECTORY}).",
    )
    return parser.parse_args()


def main() -> int:
    """Create low-count, section-level chunks for every saved raw page."""

    arguments = parse_arguments()
    raw_page_paths = sorted(arguments.raw_pages_dir.glob("*.json"))
    if not raw_page_paths:
        print(f"No raw-page JSON files found in: {arguments.raw_pages_dir}")
        return 1

    engine = ChunkingEngine(build_default_chunking_strategy_factory())
    writer = ChunkJsonWriter(arguments.output_dir)
    total_chunks = 0
    failures = 0

    print(f"Strategy: {MINIMAL_STRATEGY}")
    print(f"Raw pages found: {len(raw_page_paths)}")

    for position, raw_page_path in enumerate(raw_page_paths, start=1):
        try:
            chunked_page = engine.chunk_raw_page_file(raw_page_path, MINIMAL_STRATEGY)
            writer.write(chunked_page)
        except (OSError, ValueError) as error:
            failures += 1
            print(f"Failed {position}/{len(raw_page_paths)}: {raw_page_path.name} | {error}")
            continue

        chunk_count = len(chunked_page.chunks)
        total_chunks += chunk_count
        print(
            f"Chunked {position}/{len(raw_page_paths)}: "
            f"{chunked_page.page_id} | {chunk_count} chunks | {chunked_page.page_title}"
        )

    successful_pages = len(raw_page_paths) - failures
    average_chunks = total_chunks / successful_pages if successful_pages else 0
    print("\nFinished batch chunking")
    print(f"Pages chunked: {successful_pages}")
    print(f"Pages failed: {failures}")
    print(f"Total chunks: {total_chunks}")
    print(f"Average chunks per page: {average_chunks:.2f}")
    print(f"Output directory: {arguments.output_dir / MINIMAL_STRATEGY}")
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
