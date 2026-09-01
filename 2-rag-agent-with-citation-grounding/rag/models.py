"""Small request and response shapes for the Confluence RAG runtime."""

from pydantic import BaseModel, ConfigDict, Field


class RAGRequest(BaseModel):
    """One Confluence question and the vector backend used to answer it."""

    model_config = ConfigDict(extra="forbid")

    question: str = Field(min_length=1)
    backend_name: str = Field(min_length=1)
    limit: int = Field(default=5, ge=1, le=100)


class Citation(BaseModel):
    """Canonical Confluence information shown with an answer."""

    model_config = ConfigDict(extra="forbid")

    page_id: str = Field(min_length=1)
    page_title: str = Field(min_length=1)
    page_url: str = Field(min_length=1)


class RetrievedChunk(BaseModel):
    """One vector-search result with page metadata from the SQLite catalog."""

    model_config = ConfigDict(extra="forbid")

    rank: int = Field(ge=1)
    score: float
    score_kind: str = Field(min_length=1)
    chunk_id: str = Field(min_length=1)
    page_id: str = Field(min_length=1)
    heading_path: str = Field(min_length=1)
    content: str = Field(min_length=1)
    citation: Citation


class CitedSource(BaseModel):
    """One inline [Source N] label resolved to the retrieved Confluence evidence it names."""

    model_config = ConfigDict(extra="forbid")

    source_number: int = Field(ge=1)
    chunk_id: str = Field(min_length=1)
    heading_path: str = Field(min_length=1)
    content: str = Field(min_length=1)
    citation: Citation


class RAGResponse(BaseModel):
    """Answer, evidence, and citations returned by the complete RAG flow."""

    model_config = ConfigDict(extra="forbid")

    question: str = Field(min_length=1)
    backend_name: str = Field(min_length=1)
    answer: str = Field(min_length=1)
    answer_model: str = Field(min_length=1)
    abstained: bool = False
    abstention_reason: str | None = None
    results: list[RetrievedChunk]
    citations: list[Citation]
    cited_sources: list[CitedSource] = Field(default_factory=list)
    unresolved_source_numbers: list[int] = Field(default_factory=list)
