"""Provider-neutral data models for embedding requests and responses."""

from typing import Literal

from pydantic import BaseModel, Field


EmbeddingInputType = Literal["SEARCH_DOCUMENT", "SEARCH_QUERY"]


class EmbeddingRequest(BaseModel):
    """One text value to embed for either indexing or retrieval."""

    text: str = Field(min_length=1)
    input_type: EmbeddingInputType = "SEARCH_DOCUMENT"


class EmbeddingResponse(BaseModel):
    """A normalized vector returned by any embedding provider."""

    embedding: list[float]
    provider_name: str
    model_id: str
    input_type: EmbeddingInputType
    request_id: str | None = None

    @property
    def dimensions(self) -> int:
        """Return the number of values in the embedding vector."""
        return len(self.embedding)
