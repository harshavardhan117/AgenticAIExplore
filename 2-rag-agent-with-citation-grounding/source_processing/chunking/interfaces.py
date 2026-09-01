"""Interfaces shared by chunking strategies."""

from typing import Protocol

from source_processing.chunking.data_models import Chunk, ParsedPage


class ChunkingStrategy(Protocol):
    """Turn a parsed page into chunks using one named algorithm."""

    name: str

    def chunk(self, page: ParsedPage) -> list[Chunk]:
        """Create chunks for one parsed Confluence page."""
        ...
