"""Pydantic models shared by all vector-store adapters."""

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

from source_processing.chunking.data_models import ChunkType


ScoreKind = Literal["similarity", "distance", "bm25", "rrf"]


class UpsertResult(BaseModel):
    """Summary returned after one vector-store write operation."""

    model_config = ConfigDict(extra="forbid")

    backend_name: str = Field(min_length=1)
    stored_count: int = Field(ge=0)


class SearchResult(BaseModel):
    """One citation-ready chunk returned from a vector similarity search."""

    model_config = ConfigDict(extra="forbid")

    backend_name: str = Field(min_length=1)
    rank: int = Field(ge=1)
    score: float
    score_kind: ScoreKind
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
