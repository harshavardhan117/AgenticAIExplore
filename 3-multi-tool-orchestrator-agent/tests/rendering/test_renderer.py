from pathlib import Path

from graph.graph_analyzer import analyze_graph
from graph.graph_builder import build_graph
from parsers.gitlab import GitLabParser
from rendering.renderer import render
from tools.yaml_loader import load_yaml_document

FIXTURE = Path(__file__).parent.parent / "fixtures" / "simple_pipeline.yml"


def _analyze_fixture():
    document = load_yaml_document(FIXTURE)
    pipeline = GitLabParser().parse(document)
    graph, _ = build_graph(pipeline)
    analysis = analyze_graph(graph)
    return pipeline, graph, analysis


def test_render_mermaid_contains_stages_and_edges():
    pipeline, graph, analysis = _analyze_fixture()

    mermaid, _ = render(pipeline, graph, analysis, findings=[])

    assert "flowchart TD" in mermaid
    assert "subgraph build" in mermaid
    assert "build_api --> test_api" in mermaid


def test_render_report_contains_summary_and_layers():
    pipeline, graph, analysis = _analyze_fixture()

    _, report_markdown = render(pipeline, graph, analysis, findings=[])

    assert "Acyclic: yes" in report_markdown
    assert "## Execution layers" in report_markdown
    assert "## Findings" in report_markdown
    assert "No findings." in report_markdown


def test_render_report_lists_passed_in_findings():
    pipeline, graph, analysis = _analyze_fixture()
    from domain.models import Finding, FindingSeverity

    finding = Finding(
        id="example",
        severity=FindingSeverity.ERROR,
        title="Example finding",
        description="Something worth flagging.",
    )

    _, report_markdown = render(pipeline, graph, analysis, findings=[finding])

    assert "Example finding" in report_markdown
    assert "No findings." not in report_markdown
