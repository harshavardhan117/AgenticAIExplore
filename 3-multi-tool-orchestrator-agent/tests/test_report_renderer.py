from pathlib import Path

from engine.graph_analyzer import PipelineGraphAnalyzer
from engine.graph_builder import PipelineGraphBuilder
from engine.pipeline_parser import GitLabPipelineParser
from engine.report_renderer import PipelineReportRenderer
from engine.yaml_loader import YamlLoader


def test_render_includes_analysis_and_mermaid() -> None:
    fixture_path = Path(__file__).parent / "fixtures" / "simple_pipeline.yml"
    pipeline = GitLabPipelineParser().parse(YamlLoader().load(fixture_path))
    graph = PipelineGraphBuilder().build(pipeline)
    analysis = PipelineGraphAnalyzer().analyze(graph)

    report = PipelineReportRenderer().render(
        pipeline,
        graph,
        analysis,
        "flowchart LR\n    job_0 --> job_1\n",
    )

    assert "# GitLab CI Pipeline Report" in report
    assert "**Layer 1:** `build_api`, `lint`" in report
    assert "[INFO] **Parallel execution opportunity**" in report
    assert "```mermaid" in report
    assert "job_0 --> job_1" in report
