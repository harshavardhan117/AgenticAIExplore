from pathlib import Path

from engine.orchestrator import PipelineVisualizationOrchestrator


def test_visualize_runs_the_first_deterministic_workflow() -> None:
    fixture_path = Path(__file__).parent / "fixtures" / "simple_pipeline.yml"

    result = PipelineVisualizationOrchestrator().visualize(fixture_path)

    assert set(result.graph.nodes) == {
        "build_api",
        "lint",
        "test_api",
        "deploy_staging",
    }
    assert result.analysis.execution_layers == [
        ["build_api", "lint"],
        ["test_api"],
        ["deploy_staging"],
    ]
    assert "flowchart LR" in result.mermaid
    assert "# GitLab CI Pipeline Report" in result.report_markdown
