"""Run all enabled Confluence RAG metrics for Oracle or OpenSearch retrieval."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from evaluation.answer_relevancy import AnswerRelevancyJudge
from evaluation.citation_correctness import CitationCorrectnessJudge
from evaluation.runner import DenseRagEvaluator, build_rag_service, load_cases, summarize
from rag.oci_chat import OciChatClient


PROJECT_ROOT = Path(__file__).resolve().parent
DEFAULT_DATASET_PATH = PROJECT_ROOT / "data" / "evaluation" / "evaluation_dataset.json"
DEFAULT_DATABASE_PATH = PROJECT_ROOT / "data" / "rag_catalog.db"


def parse_arguments() -> argparse.Namespace:
    """Read common RAG configuration for the all-metrics evaluation run."""

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--backend", choices=("oracle", "opensearch"), default="oracle")
    parser.add_argument("--limit", type=int, default=5)
    parser.add_argument("--dataset-path", type=Path, default=DEFAULT_DATASET_PATH)
    parser.add_argument("--database-path", type=Path, default=DEFAULT_DATABASE_PATH)
    parser.add_argument("--output-path", type=Path, default=None)
    return parser.parse_args()


def main() -> int:
    """Run all current metrics and save one combined, inspectable evaluation report."""

    arguments = parse_arguments()
    chat_client = OciChatClient()
    evaluator = DenseRagEvaluator(
        service=build_rag_service(arguments.database_path, chat_client),
        relevancy_judge=AnswerRelevancyJudge(chat_client),
        citation_judge=CitationCorrectnessJudge(chat_client),
        backend=arguments.backend,
        limit=arguments.limit,
    )
    results = evaluator.evaluate_all(load_cases(arguments.dataset_path))
    summary = summarize(results)
    print(f"\nHit Rate@{arguments.limit}: {summary['hit_rate']:.2%} ({summary['hits']}/{summary['evaluated_case_count']})")
    print(f"MRR@{arguments.limit}: {summary['mrr']:.4f}")
    print(f"Mean Answer Relevancy: {summary['mean_answer_relevancy']:.4f}")
    print(f"Mean Citation Correctness: {summary['mean_citation_correctness']:.4f}")
    print(
        "Abstention Accuracy: "
        f"{summary['abstention_accuracy']:.2%} "
        f"({summary['abstention_correct_count']}/{summary['abstention_case_count']})"
    )

    output_path = arguments.output_path or (
        PROJECT_ROOT / "data" / "evaluation" / "runs" / f"dense_vector_{arguments.backend}_all_metrics.json"
    )
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(
        json.dumps(
            {
                "backend": arguments.backend,
                "strategy": "dense_vector",
                "limit": arguments.limit,
                "metrics": [
                    "hit_at_k",
                    "mrr_at_k",
                    "answer_relevancy",
                    "citation_correctness",
                    "abstention_accuracy",
                ],
                **summary,
                "results": [result.model_dump() for result in results],
            },
            indent=2,
        ),
        encoding="utf-8",
    )
    print(f"Report saved: {output_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
