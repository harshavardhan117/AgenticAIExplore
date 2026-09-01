"""Pydantic models for records ready to store in a vector index."""

from pydantic import BaseModel, ConfigDict, Field

from source_processing.chunking.data_models import ChunkType


class EmbeddedChunk(BaseModel):
    """One Confluence chunk together with the OCI vector created from it."""

    model_config = ConfigDict(extra="forbid")

    chunk_id: str = Field(min_length=1)
    page_id: str = Field(min_length=1)
    page_title: str = Field(min_length=1)
    page_url: str = Field(min_length=1)
    source_version: int = Field(ge=1)
    strategy: str = Field(min_length=1)
    position: int = Field(ge=0)
    heading_path: str = Field(min_length=1)
    type: ChunkType
    content: str = Field(min_length=1)
    embedding_text: str = Field(min_length=1)
    embedding: list[float] = Field(min_length=1)
    embedding_provider: str = Field(min_length=1)
    embedding_model: str = Field(min_length=1)

    @property
    def embedding_dimensions(self) -> int:
        """Return the number of values in the stored vector."""

        return len(self.embedding)


class EmbeddedPage(BaseModel):
    """Portable local embedding output for one Confluence page."""

    model_config = ConfigDict(extra="forbid")

    page_id: str = Field(min_length=1)
    page_title: str = Field(min_length=1)
    page_url: str = Field(min_length=1)
    source_version: int = Field(ge=1)
    strategy: str = Field(min_length=1)
    embedding_provider: str = Field(min_length=1)
    embedding_model: str = Field(min_length=1)
    embedding_dimensions: int = Field(ge=1)
    chunks: list[EmbeddedChunk] = Field(min_length=1)
