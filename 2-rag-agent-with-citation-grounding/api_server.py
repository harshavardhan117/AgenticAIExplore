"""Local FastAPI server for grounded Confluence RAG questions."""

from __future__ import annotations

import logging
from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from pydantic import BaseModel, ConfigDict, Field

from embedding_pipeline.embeddings.factory import EmbeddingProviderFactory
from embedding_pipeline.embeddings.registration import register_builtin_embedding_providers
from persistence.vector_stores.factory import VectorStoreFactory
from persistence.vector_stores.registration import register_builtin_vector_stores
from rag.models import RAGRequest, RAGResponse
from rag.oci_chat import OciChatClient
from rag.service import RAGService


PROJECT_ROOT = Path(__file__).resolve().parent
DEFAULT_DATABASE_PATH = PROJECT_ROOT / "data" / "rag_catalog.db"
UI_PATH = PROJECT_ROOT / "web" / "index.html"
logger = logging.getLogger(__name__)


class AskApiRequest(BaseModel):
    """Safe input shape accepted by the local browser UI and API clients."""

    model_config = ConfigDict(extra="forbid")

    question: str = Field(min_length=1, max_length=4_000)
    backend_name: str = Field(default="oracle", pattern="^(oracle|opensearch)$")
    retrieval_strategy: str = Field(default="dense", pattern="^(dense|keyword|hybrid_rrf)$")
    limit: int = Field(default=5, ge=1, le=20)


def build_service(database_path: Path = DEFAULT_DATABASE_PATH) -> RAGService:
    """Compose one request-safe RAG service from environment configuration."""

    embedding_factory = EmbeddingProviderFactory()
    register_builtin_embedding_providers(embedding_factory)
    vector_store_factory = VectorStoreFactory()
    register_builtin_vector_stores(vector_store_factory)
    return RAGService(
        embedding_provider=embedding_factory.create("oci"),
        vector_store_factory=vector_store_factory,
        catalog_path=database_path,
        chat_client=OciChatClient(),
    )


app = FastAPI(title="Confluence RAG", version="2.0.0")


@app.get("/", include_in_schema=False)
def index() -> FileResponse:
    """Serve the small local browser UI."""

    return FileResponse(UI_PATH)


@app.get("/health")
def health() -> dict[str, str]:
    """Provide a dependency-free liveness signal for local development."""

    return {"status": "ok"}


@app.post("/api/ask", response_model=RAGResponse)
def ask(request: AskApiRequest) -> RAGResponse:
    """Answer one question with selected backend, retrieval strategy, and citations."""

    try:
        return build_service().ask(
            RAGRequest(
                question=request.question,
                backend_name=request.backend_name,
                retrieval_strategy=request.retrieval_strategy,
                limit=request.limit,
            )
        )
    except Exception:
        logger.exception("Grounded RAG request failed")
        raise HTTPException(
            status_code=500,
            detail="RAG request failed. Check local configuration and server logs.",
        ) from None
