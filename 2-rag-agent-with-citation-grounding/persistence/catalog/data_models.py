"""Pydantic records persisted by the relational Confluence content catalog."""

from pydantic import BaseModel, ConfigDict, Field

from source_processing.chunking.data_models import ChunkType


class CatalogPage(BaseModel):
    """One current Confluence-page snapshot represented in the local catalog."""

    model_config = ConfigDict(extra="forbid")

    page_id: str = Field(min_length=1)
    title: str = Field(min_length=1)
    page_url: str = Field(min_length=1)
    last_modified: str = Field(min_length=1)
    source_version: int = Field(ge=1)


class CatalogChunk(BaseModel):
    """One searchable section whose parent is a Confluence page."""

    model_config = ConfigDict(extra="forbid")

    chunk_id: str = Field(min_length=1)
    page_id: str = Field(min_length=1)
    strategy: str = Field(min_length=1)
    position: int = Field(ge=0)
    heading_path: str = Field(min_length=1)
    type: ChunkType
    content: str = Field(min_length=1)


class CatalogEmbedding(BaseModel):
    """Provenance for the one current embedding retained for a chunk."""

    model_config = ConfigDict(extra="forbid")

    chunk_id: str = Field(min_length=1)
    embedding_text: str = Field(min_length=1)
    provider: str = Field(min_length=1)
    model: str = Field(min_length=1)
    dimensions: int = Field(ge=1)
    embedded_json_path: str = Field(min_length=1)
