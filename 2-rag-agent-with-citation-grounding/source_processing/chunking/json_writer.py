"""Persist validated chunking output as JSON without applying business logic."""

from pathlib import Path

from source_processing.chunking.data_models import ChunkedPage


class ChunkJsonWriter:
    """Write one chunked page beneath an output root organized by strategy."""

    def __init__(self, output_root: Path) -> None:
        self._output_root = output_root

    def write(self, chunked_page: ChunkedPage) -> Path:
        """Atomically write a chunked-page JSON file and return its path."""

        strategy_directory = self._output_root / chunked_page.strategy
        strategy_directory.mkdir(parents=True, exist_ok=True)
        output_path = strategy_directory / f"{chunked_page.page_id}.json"
        temporary_path = output_path.with_suffix(".json.tmp")

        temporary_path.write_text(
            chunked_page.model_dump_json(indent=2),
            encoding="utf-8",
        )
        temporary_path.replace(output_path)
        return output_path
