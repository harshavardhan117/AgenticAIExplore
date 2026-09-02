"""One small service that performs the complete Confluence RAG request."""

from __future__ import annotations

import re
import os
from pathlib import Path

from embedding_pipeline.embeddings.interfaces import EmbeddingProvider
from persistence.vector_stores.factory import VectorStoreFactory
from rag.models import Citation, CitedSource, RAGRequest, RAGResponse, RetrievedChunk
from rag.oci_chat import OciChatClient
from rag.prompt_builder import PromptBuilder
from rag.retrieval.catalog_reader import CatalogReader
from rag.retrieval.factory import RetrievalStrategyFactory, build_default_retrieval_strategy_factory


class RAGService:
    """Embed, search, enrich, prompt, and answer one Confluence question."""

    def __init__(
        self,
        embedding_provider: EmbeddingProvider,
        vector_store_factory: VectorStoreFactory,
        catalog_path: Path,
        chat_client: OciChatClient | None = None,
        prompt_builder: PromptBuilder | None = None,
        retrieval_strategy_factory: RetrievalStrategyFactory | None = None,
    ) -> None:
        self._embedding_provider = embedding_provider
        self._vector_store_factory = vector_store_factory
        self._catalog_path = catalog_path
        self._chat_client = chat_client
        self._prompt_builder = prompt_builder or PromptBuilder()
        # The two backends expose different score scales. Keep their cutoffs explicit
        # and independently configurable instead of pretending their scores match.
        self._max_cosine_distance = float(os.getenv("RAG_MAX_COSINE_DISTANCE", "0.45"))
        self._min_knn_score = float(os.getenv("RAG_MIN_KNN_SCORE", "0.75"))
        self._retrieval_strategy_factory = retrieval_strategy_factory or build_default_retrieval_strategy_factory(
            embedding_provider,
            vector_store_factory,
            CatalogReader(catalog_path),
        )

    def retrieve(self, request: RAGRequest) -> list[RetrievedChunk]:
        """Select and run dense, keyword, or hybrid retrieval."""

        return self._retrieval_strategy_factory.create(request.retrieval_strategy).retrieve(request)

    def ask(self, request: RAGRequest) -> RAGResponse:
        """Retrieve evidence, call OCI chat, and return answer plus source pages."""

        results = self.retrieve(request)
        abstention_reason = self._abstention_reason(results)
        if abstention_reason is not None:
            return RAGResponse(
                question=request.question,
                backend_name=request.backend_name,
                retrieval_strategy=request.retrieval_strategy,
                answer="I cannot answer reliably from the retrieved Confluence documentation.",
                answer_model="not_called",
                abstained=True,
                abstention_reason=abstention_reason,
                # Preserve raw nearest-neighbour results for debugging and retrieval
                # evaluation, but never present them as citations for an abstention.
                results=results,
                citations=[],
                cited_sources=[],
                unresolved_source_numbers=[],
            )

        if self._chat_client is None:
            raise RuntimeError("This RAGService was created for retrieval only and has no chat client.")
        answer = self._chat_client.generate(self._prompt_builder.build(request.question, results))
        citations = list({citation.page_id: citation for citation in (r.citation for r in results)}.values())
        return RAGResponse(
            question=request.question,
            backend_name=request.backend_name,
            retrieval_strategy=request.retrieval_strategy,
            answer=answer,
            answer_model=self._chat_client.model_id,
            abstained=False,
            abstention_reason=None,
            results=results,
            citations=citations,
            cited_sources=self._resolve_cited_sources(answer, results),
            unresolved_source_numbers=self._unresolved_source_numbers(answer, results),
        )

    def _abstention_reason(self, results: list[RetrievedChunk]) -> str | None:
        """Return why generation must be skipped when retrieval evidence is weak."""

        if not results:
            return "The vector store returned no chunks."

        best_result = results[0]
        if best_result.score_kind == "distance":
            if best_result.score > self._max_cosine_distance:
                return (
                    "Best cosine distance "
                    f"{best_result.score:.4f} exceeds RAG_MAX_COSINE_DISTANCE "
                    f"({self._max_cosine_distance:.4f})."
                )
            return None

        if best_result.score_kind == "similarity" and best_result.score < self._min_knn_score:
            return (
                f"Best k-NN score {best_result.score:.4f} is below RAG_MIN_KNN_SCORE "
                f"({self._min_knn_score:.4f})."
            )
        return None

    @staticmethod
    def _resolve_cited_sources(answer: str, results: list[RetrievedChunk]) -> list[CitedSource]:
        """Map inline [Source N] labels in the LLM answer back to retrieved evidence."""

        results_by_rank = {result.rank: result for result in results}
        source_numbers = sorted({int(value) for value in re.findall(r"\[Source\s+(\d+)\]", answer)})
        return [
            CitedSource(
                source_number=source_number,
                chunk_id=results_by_rank[source_number].chunk_id,
                heading_path=results_by_rank[source_number].heading_path,
                content=results_by_rank[source_number].content,
                citation=results_by_rank[source_number].citation,
            )
            for source_number in source_numbers
            if source_number in results_by_rank
        ]

    @staticmethod
    def _unresolved_source_numbers(answer: str, results: list[RetrievedChunk]) -> list[int]:
        """Keep invalid source labels visible for later citation-correctness evaluation."""

        valid_numbers = {result.rank for result in results}
        source_numbers = {int(value) for value in re.findall(r"\[Source\s+(\d+)\]", answer)}
        return sorted(source_numbers - valid_numbers)
