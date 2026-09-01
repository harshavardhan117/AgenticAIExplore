"""Coordinate raw-page loading, parsing, strategy selection, and chunk creation."""

from pathlib import Path
from typing import Any, Mapping

from source_processing.chunking.factory import ChunkingStrategyFactory
from source_processing.chunking.html_parser import parse_raw_page, parse_raw_page_file
from source_processing.chunking.data_models import ChunkedPage, ParsedPage


class ChunkingEngine:
    """Create a complete chunked-page result using a named strategy."""

    def __init__(self, strategy_factory: ChunkingStrategyFactory) -> None:
        self._strategy_factory = strategy_factory

    def chunk_raw_page(
        self,
        raw_page: Mapping[str, Any],
        strategy_name: str,
    ) -> ChunkedPage:
        """Parse and chunk one raw Confluence page JSON object."""

        parsed_page = parse_raw_page(raw_page)
        return self.chunk_parsed_page(parsed_page, strategy_name)

    def chunk_raw_page_file(self, path: Path, strategy_name: str) -> ChunkedPage:
        """Load, parse, and chunk one saved raw-page JSON file."""

        parsed_page = parse_raw_page_file(path)
        return self.chunk_parsed_page(parsed_page, strategy_name)

    def chunk_parsed_page(
        self,
        parsed_page: ParsedPage,
        strategy_name: str,
    ) -> ChunkedPage:
        """Apply a selected strategy to an already parsed page."""

        strategy = self._strategy_factory.create(strategy_name)
        return ChunkedPage(
            page_id=parsed_page.page_id,
            page_title=parsed_page.page_title,
            page_url=parsed_page.page_url,
            source_version=parsed_page.source_version,
            strategy=strategy.name,
            chunks=strategy.chunk(parsed_page),
        )
