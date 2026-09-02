"""Hybrid retrieval that fuses dense and keyword rankings with RRF."""

from rag.models import RAGRequest, RetrievedChunk
from rag.retrieval.interfaces import RetrievalStrategy


class HybridRrfRetrievalStrategy:
    """Combine dense and keyword candidates without comparing raw score scales."""

    name = "hybrid_rrf"

    def __init__(self, dense: RetrievalStrategy, keyword: RetrievalStrategy, rrf_constant: int = 60) -> None:
        self._dense = dense
        self._keyword = keyword
        self._rrf_constant = rrf_constant

    def retrieve(self, request: RAGRequest) -> list[RetrievedChunk]:
        dense_results = self._dense.retrieve(request)
        keyword_results = self._keyword.retrieve(request)
        candidates: dict[str, tuple[RetrievedChunk, float]] = {}
        for result_set in (dense_results, keyword_results):
            for result in result_set:
                current, score = candidates.get(result.chunk_id, (result, 0.0))
                candidates[result.chunk_id] = (
                    current,
                    score + 1.0 / (self._rrf_constant + result.rank),
                )
        ranked = sorted(candidates.values(), key=lambda item: (-item[1], item[0].chunk_id))
        return [
            result.model_copy(update={"rank": rank, "score": score, "score_kind": "rrf"})
            for rank, (result, score) in enumerate(ranked[: request.limit], start=1)
        ]
