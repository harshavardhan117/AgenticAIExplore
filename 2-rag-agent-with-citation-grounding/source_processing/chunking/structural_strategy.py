"""Strategy 2: emit one chunk per paragraph, code block, or table block."""

from source_processing.chunking.data_models import Chunk, ParsedPage


class StructuralBlocksStrategy:
    """Keep each parser-produced structural block as a separate final chunk."""

    name = "structural_blocks_v1"

    def chunk(self, page: ParsedPage) -> list[Chunk]:
        """Create one chunk for every ordered block in a parsed page."""

        return [
            Chunk(
                chunk_id=f"{page.page_id}:{self.name}:{block.position:04d}",
                position=block.position,
                heading_path=" > ".join(block.heading_path),
                type=block.block_type,
                content=block.content,
            )
            for block in page.blocks
        ]
