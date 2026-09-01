"""Strategy 1: emit one chunk for each complete heading section."""

from itertools import groupby

from source_processing.chunking.data_models import Chunk, ChunkType, ParsedBlock, ParsedPage


class SectionAsChunkStrategy:
    """Keep all consecutive content under one heading path in one chunk."""

    name = "section_as_chunk_v1"

    def chunk(self, page: ParsedPage) -> list[Chunk]:
        """Combine each page section's structural blocks into one final chunk."""

        chunks: list[Chunk] = []
        for heading_path, block_group in groupby(
            page.blocks,
            key=lambda block: tuple(block.heading_path),
        ):
            blocks = list(block_group)
            chunks.append(
                Chunk(
                    chunk_id=(
                        f"{page.page_id}:{self.name}:{blocks[0].position:04d}"
                    ),
                    position=blocks[0].position,
                    heading_path=" > ".join(heading_path),
                    type=_combined_type(blocks),
                    content="\n\n".join(_format_block(block) for block in blocks),
                )
            )
        return chunks


def _combined_type(blocks: list[ParsedBlock]) -> ChunkType:
    """Use the single block type when possible; otherwise mark mixed content."""

    block_types = {block.block_type for block in blocks}
    return blocks[0].block_type if len(block_types) == 1 else "mixed"


def _format_block(block: ParsedBlock) -> str:
    """Preserve code and table boundaries when combining blocks into a section."""

    if block.block_type == "code":
        return f"```\n{block.content}\n```"
    if block.block_type == "table":
        return f"Table:\n{block.content}"
    return block.content
