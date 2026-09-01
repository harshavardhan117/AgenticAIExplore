"""Preview or create OCI embeddings for all minimal Confluence section chunks."""

from __future__ import annotations

import argparse
import json
from datetime import UTC, datetime
from decimal import Decimal
from pathlib import Path

from source_processing.chunking.data_models import ChunkedPage
from embedding_pipeline.embeddings.factory import EmbeddingProviderFactory
from embedding_pipeline.embeddings.oci_config import OciEmbeddingConfig
from embedding_pipeline.embeddings.registration import register_builtin_embedding_providers
from embedding_pipeline.records.data_models import EmbeddedChunk, EmbeddedPage
from embedding_pipeline.records.embedding_engine import EmbeddingEngine
from embedding_pipeline.records.embedding_text import build_embedding_text
from embedding_pipeline.records.json_writer import EmbeddedPageJsonWriter


PROJECT_ROOT = Path(__file__).resolve().parent
DEFAULT_CHUNKS_DIRECTORY = PROJECT_ROOT / "data" / "chunks" / "section_as_chunk_v1"
DEFAULT_OUTPUT_DIRECTORY = PROJECT_ROOT / "data" / "embedded_chunks"
DEFAULT_SUMMARY_PATH = DEFAULT_OUTPUT_DIRECTORY / "embedding_run_summary.json"
# This is an estimate only. Set --price-per-10000-characters from your OCI
# pricing page or tenancy agreement before a paid run.
DEFAULT_PRICE_PER_10K_CHARACTERS = Decimal("0.0013106")


def parse_arguments() -> argparse.Namespace:
    """Read the batch embedding request and its explicit cost safeguards."""

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--all",
        action="store_true",
        help="Make OCI calls for every chunk not already embedded locally.",
    )
    parser.add_argument(
        "--chunks-dir",
        type=Path,
        default=DEFAULT_CHUNKS_DIRECTORY,
        help=f"Minimal chunk JSON directory (default: {DEFAULT_CHUNKS_DIRECTORY}).",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=DEFAULT_OUTPUT_DIRECTORY,
        help=f"Embedded JSON output root (default: {DEFAULT_OUTPUT_DIRECTORY}).",
    )
    parser.add_argument(
        "--price-per-10000-characters",
        type=Decimal,
        default=DEFAULT_PRICE_PER_10K_CHARACTERS,
        help=(
            "USD price for 10,000 OCI Embed Cohere input characters used only "
            f"for the estimate (default: {DEFAULT_PRICE_PER_10K_CHARACTERS})."
        ),
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Recreate embeddings even when a matching local embedded JSON exists.",
    )
    return parser.parse_args()


def load_chunked_pages(chunks_directory: Path) -> list[ChunkedPage]:
    """Load all saved minimal-strategy chunk pages in stable page-ID order."""

    paths = sorted(chunks_directory.glob("*.json"))
    if not paths:
        raise ValueError(f"No chunk JSON files found in: {chunks_directory}")
    return [ChunkedPage.model_validate_json(path.read_text(encoding="utf-8")) for path in paths]


def load_resumable_page(
    writer: EmbeddedPageJsonWriter,
    page: ChunkedPage,
    model_id: str,
    force: bool,
) -> dict[str, EmbeddedChunk]:
    """Reuse embeddings only when their page version, strategy, and model match."""

    if force:
        return {}
    output_path = writer.path_for(page.strategy, page.page_id)
    if not output_path.is_file():
        return {}

    try:
        existing = EmbeddedPage.model_validate_json(output_path.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return {}

    if (
        existing.source_version != page.source_version
        or existing.strategy != page.strategy
        or existing.embedding_model != model_id
    ):
        return {}
    return {chunk.chunk_id: chunk for chunk in existing.chunks}


def estimate_cost(input_characters: int, price_per_10k: Decimal) -> Decimal:
    """Calculate the displayed OCI character-billing estimate in USD."""

    return (Decimal(input_characters) / Decimal(10_000)) * price_per_10k


def write_summary(summary_path: Path, summary: dict[str, object]) -> None:
    """Write the run ledger used to reconcile later with OCI Cost Analysis."""

    summary_path.parent.mkdir(parents=True, exist_ok=True)
    temporary_path = summary_path.with_suffix(".json.tmp")
    temporary_path.write_text(json.dumps(summary, indent=2), encoding="utf-8")
    temporary_path.replace(summary_path)


def main() -> int:
    """Preview planned OCI spending or create resumable embedded-page JSON files."""

    arguments = parse_arguments()
    if arguments.price_per_10000_characters < 0:
        raise ValueError("--price-per-10000-characters cannot be negative")

    pages = load_chunked_pages(arguments.chunks_dir)
    config = OciEmbeddingConfig.from_environment()
    writer = EmbeddedPageJsonWriter(arguments.output_dir)

    planned: list[tuple[ChunkedPage, list[str], dict[str, EmbeddedChunk]]] = []
    existing_chunks = 0
    planned_characters = 0
    for page in pages:
        existing = load_resumable_page(writer, page, config.model_id, arguments.force)
        missing_chunk_ids: list[str] = []
        for chunk in page.chunks:
            if chunk.chunk_id in existing:
                existing_chunks += 1
                continue
            missing_chunk_ids.append(chunk.chunk_id)
            planned_characters += len(build_embedding_text(page, chunk))
        planned.append((page, missing_chunk_ids, existing))

    planned_chunks = sum(len(chunk_ids) for _, chunk_ids, _ in planned)
    planned_cost = estimate_cost(
        planned_characters,
        arguments.price_per_10000_characters,
    )
    print(f"Pages found: {len(pages)}")
    print(f"Chunks already reusable locally: {existing_chunks}")
    print(f"Chunks requiring OCI embeddings: {planned_chunks}")
    print(f"Input characters requiring OCI calls: {planned_characters}")
    print(f"Estimated OCI embedding cost: ${planned_cost:.6f} USD")

    if not arguments.all:
        print("Preview only: no OCI calls were made and no files were written.")
        print("Run again with --all to confirm this paid embedding batch.")
        return 0

    provider_factory = EmbeddingProviderFactory()
    register_builtin_embedding_providers(provider_factory)
    engine = EmbeddingEngine(provider_factory.create("oci"))
    successful_calls = 0
    successful_characters = 0
    failed_pages: list[str] = []

    for page_number, (page, missing_ids, existing) in enumerate(planned, start=1):
        if not page.chunks:
            print(f"Skipped {page_number}/{len(pages)}: {page.page_id} | no chunks")
            continue

        embedded_by_id = dict(existing)
        try:
            for chunk in page.chunks:
                if chunk.chunk_id in embedded_by_id:
                    continue
                embedded_chunk = engine.embed_chunk(page, chunk)
                embedded_by_id[chunk.chunk_id] = embedded_chunk
                successful_calls += 1
                successful_characters += len(embedded_chunk.embedding_text)

                # Save after each paid request. A later interruption resumes from
                # this page's completed chunk IDs instead of paying for them again.
                completed_chunks = [embedded_by_id[item.chunk_id] for item in page.chunks if item.chunk_id in embedded_by_id]
                writer.write(
                    EmbeddedPage(
                        page_id=page.page_id,
                        page_title=page.page_title,
                        page_url=page.page_url,
                        source_version=page.source_version,
                        strategy=page.strategy,
                        embedding_provider=embedded_chunk.embedding_provider,
                        embedding_model=embedded_chunk.embedding_model,
                        embedding_dimensions=embedded_chunk.embedding_dimensions,
                        chunks=completed_chunks,
                    )
                )
        except Exception as error:  # noqa: BLE001 - continue with independently resumable pages.
            failed_pages.append(page.page_id)
            print(f"Failed {page_number}/{len(pages)}: {page.page_id} | {error}")
            continue

        print(
            f"Embedded {page_number}/{len(pages)}: {page.page_id} | "
            f"new={len(missing_ids)}, total={len(embedded_by_id)} | {page.page_title}"
        )

    actual_estimate = estimate_cost(
        successful_characters,
        arguments.price_per_10000_characters,
    )
    summary_path = arguments.output_dir / DEFAULT_SUMMARY_PATH.name
    write_summary(
        summary_path,
        {
            "created_at_utc": datetime.now(UTC).isoformat(),
            "provider": "oci",
            "model": config.model_id,
            "price_per_10000_characters_usd": str(arguments.price_per_10000_characters),
            "planned_chunks": planned_chunks,
            "planned_input_characters": planned_characters,
            "planned_estimated_cost_usd": str(planned_cost),
            "successful_api_calls": successful_calls,
            "successful_input_characters": successful_characters,
            "successful_estimated_cost_usd": str(actual_estimate),
            "failed_page_ids": failed_pages,
            "note": (
                "Estimate calculated from successful input characters. OCI Cost Analysis "
                "is the source of truth for the actual billed amount and can be delayed."
            ),
        },
    )
    print("\nFinished embedding batch")
    print(f"Successful OCI calls: {successful_calls}")
    print(f"Successful input characters: {successful_characters}")
    print(f"Estimated successful cost: ${actual_estimate:.6f} USD")
    print(f"Run summary: {summary_path}")
    return 1 if failed_pages else 0


if __name__ == "__main__":
    raise SystemExit(main())
