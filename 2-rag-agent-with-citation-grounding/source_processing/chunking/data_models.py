"""Pydantic data models used between the chunking module's layers."""

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


ChunkType = Literal["text", "code", "table", "mixed"]


class ParsedBlock(BaseModel):
    """One meaningful block extracted from a Confluence page's HTML."""

    model_config = ConfigDict(extra="forbid")

    position: int = Field(ge=0)
    heading_path: list[str] = Field(min_length=1)
    block_type: ChunkType
    content: str = Field(min_length=1)


class ParsedPage(BaseModel):
    """A raw Confluence snapshot after its HTML has been structurally parsed."""

    model_config = ConfigDict(extra="forbid")

    page_id: str = Field(min_length=1)
    page_title: str = Field(min_length=1)
    page_url: str = Field(min_length=1)
    source_version: int = Field(ge=1)
    blocks: list[ParsedBlock]


class Chunk(BaseModel):
    """One self-contained, retrievable unit produced by a chunking strategy."""

    model_config = ConfigDict(extra="forbid")

    chunk_id: str = Field(min_length=1)
    position: int = Field(ge=0)
    heading_path: str = Field(min_length=1)
    type: ChunkType
    content: str = Field(min_length=1)


class ChunkedPage(BaseModel):
    """The JSON output for one page and one chunking strategy."""

    model_config = ConfigDict(extra="forbid")

    page_id: str = Field(min_length=1)
    page_title: str = Field(min_length=1)
    page_url: str = Field(min_length=1)
    source_version: int = Field(ge=1)
    strategy: str = Field(min_length=1)
    chunks: list[Chunk]
