from pathlib import Path

from graph.graph_builder import build_graph
from parsers.gitlab import GitLabParser
from tools.yaml_loader import load_yaml_document

FIXTURE = Path(__file__).parent.parent / "fixtures" / "simple_pipeline.yml"


def _load_pipeline():
    doc = load_yaml_document(FIXTURE)
    return GitLabParser().parse(doc)


def test_build_graph_creates_expected_edges():
    graph, findings = build_graph(_load_pipeline())

    assert set(graph.nodes) == {"build_api", "lint", "test_api", "deploy_staging"}
    edges = {(e.source_job_id, e.target_job_id) for e in graph.edges}
    assert edges == {
        ("build_api", "test_api"),
        ("lint", "test_api"),
        ("test_api", "deploy_staging"),
    }
    assert findings == []


def test_build_graph_reports_finding_on_unknown_need():
    pipeline = _load_pipeline()
    pipeline.jobs["test_api"].needs.append("nonexistent_job")

    graph, findings = build_graph(pipeline)

    edges = {(e.source_job_id, e.target_job_id) for e in graph.edges}
    assert ("nonexistent_job", "test_api") not in edges

    assert len(findings) == 1
    assert findings[0].title == "Dangling needs reference"
    assert "nonexistent_job" in findings[0].description
