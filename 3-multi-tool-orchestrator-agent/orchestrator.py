"""Service layer: wires loading, parsing, graph building, analysis, and rendering.

Owns the sequence, not the logic — every step's actual behavior lives in its
own independent module (parsers, graph, rendering). This function only calls
them in order and assembles the result.
"""

from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

from ai.factory import build_ai_reviewer
from checkers.registry import build_default_checkers
from domain.models import AIReviewInput, PipelineReport
from graph.graph_analyzer import analyze_graph
from graph.graph_builder import build_graph
from observability.context import new_run_id
from parsers.registry import build_default_registry
from rendering.renderer import render
from tools.yaml_loader import load_yaml_document


def run(yaml_path: Path, ai_mode: bool = False) -> PipelineReport:
    new_run_id()

    document = load_yaml_document(yaml_path)

    registry = build_default_registry()
    pipeline = registry.parse(document)

    checkers = build_default_checkers()
    with ThreadPoolExecutor(max_workers=len(checkers)) as pool:
        futures = [pool.submit(checker.check, pipeline) for checker in checkers]
        checker_findings = [finding for future in futures for finding in future.result()]

    graph, graph_findings = build_graph(pipeline)
    validation_findings = checker_findings + graph_findings
    analysis = analyze_graph(graph)

    all_findings = validation_findings + analysis.findings
    mermaid, report_markdown = render(pipeline, graph, analysis, all_findings)

    ai_review, ai_error = None, None
    if ai_mode:
        try:
            reviewer = build_ai_reviewer()
            ai_review = reviewer.chat(
                AIReviewInput(validation_findings=validation_findings, analysis=analysis)
            )
        except Exception as e:  # noqa: BLE001 - any failure here must fall back, not crash
            ai_error = f"AI call failed: {e}"

    return PipelineReport(
        pipeline=pipeline,
        graph=graph,
        analysis=analysis,
        validation_findings=validation_findings,
        mermaid=mermaid,
        report_markdown=report_markdown,
        ai_review=ai_review,
        ai_error=ai_error,
    )
