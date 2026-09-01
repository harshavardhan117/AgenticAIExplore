"""Central runner for the currently enabled Confluence RAG evaluation metrics."""

from __future__ import annotations

import json
from pathlib import Path

from embedding_pipeline.embeddings.factory import EmbeddingProviderFactory
from embedding_pipeline.embeddings.registration import register_builtin_embedding_providers
from evaluation.answer_relevancy import AnswerRelevancyJudge
from evaluation.citation_correctness import CitationCorrectnessJudge
from evaluation.data_models import EvaluationCase, EvaluationResult
from evaluation.retrieval_metrics import hit_at_k, reciprocal_rank_at_k
from persistence.vector_stores.factory import VectorStoreFactory
from persistence.vector_stores.registration import register_builtin_vector_stores
from rag.models import RAGRequest
from rag.oci_chat import OciChatClient
from rag.service import RAGService


def load_cases(dataset_path: Path) -> list[EvaluationCase]:
    """Load and validate the manually curated Confluence golden dataset."""

    return [
        EvaluationCase.model_validate(item)
        for item in json.loads(dataset_path.read_text(encoding="utf-8"))
    ]


def build_rag_service(database_path: Path, chat_client: OciChatClient) -> RAGService:
    """Compose the existing OCI, vector-store, and SQLite dependencies."""

    embedding_factory = EmbeddingProviderFactory()
    register_builtin_embedding_providers(embedding_factory)
    vector_store_factory = VectorStoreFactory()
    register_builtin_vector_stores(vector_store_factory)
    return RAGService(
        embedding_provider=embedding_factory.create("oci"),
        vector_store_factory=vector_store_factory,
        catalog_path=database_path,
        chat_client=chat_client,
    )


class DenseRagEvaluator:
    """Run every currently enabled metric for one dense-vector RAG configuration."""

    def __init__(
        self,
        service: RAGService,
        relevancy_judge: AnswerRelevancyJudge,
        citation_judge: CitationCorrectnessJudge,
        backend: str,
        limit: int,
    ) -> None:
        self._service = service
        self._relevancy_judge = relevancy_judge
        self._citation_judge = citation_judge
        self._backend = backend
        self._limit = limit

    def evaluate_case(self, case: EvaluationCase) -> EvaluationResult:
        """Run retrieval, answer, citation, and abstention checks for one case."""

        response = self._service.ask(
            RAGRequest(question=case.question, backend_name=self._backend, limit=self._limit)
        )
        retrieved_urls = list(dict.fromkeys(chunk.citation.page_url for chunk in response.results))

        predicted_abstention = response.abstained or _contains_full_model_abstention(
            response.answer,
            has_citations=bool(response.cited_sources),
        )
        abstention_correct = predicted_abstention == case.should_abstain

        if case.should_abstain:
            return EvaluationResult(
                case_id=case.id,
                question=case.question,
                answer=response.answer,
                retrieved_source_urls=retrieved_urls,
                metric_values={"abstention_correct": abstention_correct},
                metric_reasons={
                    "abstention": (
                        response.abstention_reason
                        or "The model abstained in its answer."
                        if predicted_abstention
                        else "The system answered an unsupported question instead of abstaining."
                    )
                },
            )

        relevancy = self._relevancy_judge.judge(case.question, response.answer)
        citation_correctness = self._citation_judge.judge(
            response.answer,
            response.cited_sources,
            response.unresolved_source_numbers,
        )
        return EvaluationResult(
            case_id=case.id,
            question=case.question,
            answer=response.answer,
            retrieved_source_urls=retrieved_urls,
            metric_values={
                "hit_at_k": hit_at_k(case.expected_source_urls, retrieved_urls),
                "reciprocal_rank_at_k": reciprocal_rank_at_k(
                    case.expected_source_urls,
                    retrieved_urls,
                ),
                "answer_relevancy": relevancy.score,
                "citation_correctness": citation_correctness.score,
                "abstention_correct": abstention_correct,
            },
            metric_reasons={
                "answer_relevancy": relevancy.reason,
                "citation_correctness": citation_correctness.reason,
            },
        )

    def evaluate_all(self, cases: list[EvaluationCase]) -> list[EvaluationResult]:
        """Evaluate every case, printing concise progress and all per-case metric values."""

        results: list[EvaluationResult] = []
        for index, case in enumerate(cases, start=1):
            result = self.evaluate_case(case)
            results.append(result)
            if case.should_abstain:
                print(
                    f"{index}/{len(cases)} {case.id}: "
                    f"abstention correct={result.metric_values['abstention_correct']} | {case.question}"
                )
                continue
            print(
                f"{index}/{len(cases)} {case.id}: "
                f"hit={result.metric_values['hit_at_k']} | "
                f"reciprocal rank={result.metric_values['reciprocal_rank_at_k']:.2f} | "
                f"answer relevancy={result.metric_values['answer_relevancy']:.2f} | "
                f"citation correctness={result.metric_values['citation_correctness']:.2f}"
            )
        return results


def summarize(results: list[EvaluationResult]) -> dict[str, float | int]:
    """Calculate one aggregate value for every metric enabled by the central runner."""

    evaluated = [result for result in results if "hit_at_k" in result.metric_values]
    hits = sum(bool(result.metric_values["hit_at_k"]) for result in evaluated)
    count = len(evaluated)
    abstention_results = [result for result in results if "abstention_correct" in result.metric_values]
    abstention_correct = sum(
        bool(result.metric_values["abstention_correct"]) for result in abstention_results
    )
    return {
        "hit_rate": hits / count if count else 0.0,
        "mrr": (
            sum(float(result.metric_values["reciprocal_rank_at_k"]) for result in evaluated) / count
            if count
            else 0.0
        ),
        "mean_answer_relevancy": (
            sum(float(result.metric_values["answer_relevancy"]) for result in evaluated) / count
            if count
            else 0.0
        ),
        "mean_citation_correctness": (
            sum(float(result.metric_values["citation_correctness"]) for result in evaluated) / count
            if count
            else 0.0
        ),
        "hits": hits,
        "evaluated_case_count": count,
        "abstention_accuracy": (
            abstention_correct / len(abstention_results) if abstention_results else 0.0
        ),
        "abstention_correct_count": abstention_correct,
        "abstention_case_count": len(abstention_results),
    }


def _contains_full_model_abstention(answer: str, *, has_citations: bool) -> bool:
    """Recognize a complete model abstention, not a useful partial answer's caveat."""

    canonical_response = "i cannot answer reliably from the retrieved confluence documentation"
    return not has_citations and answer.strip().casefold().startswith(canonical_response)
