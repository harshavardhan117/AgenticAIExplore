"""Persist portable embedded-page records as local JSON files."""

from pathlib import Path

from embedding_pipeline.records.data_models import EmbeddedPage


class EmbeddedPageJsonWriter:
    """Write one embedded page under a folder organized by chunk strategy."""

    def __init__(self, output_root: Path) -> None:
        self._output_root = output_root

    def path_for(self, strategy: str, page_id: str) -> Path:
        """Return the stable output path for a page embedding record."""

        return self._output_root / strategy / f"{page_id}.json"

    def write(self, embedded_page: EmbeddedPage) -> Path:
        """Atomically write an embedded-page JSON file and return its path."""

        output_path = self.path_for(embedded_page.strategy, embedded_page.page_id)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        temporary_path = output_path.with_suffix(".json.tmp")
        temporary_path.write_text(
            embedded_page.model_dump_json(indent=2),
            encoding="utf-8",
        )
        temporary_path.replace(output_path)
        return output_path
