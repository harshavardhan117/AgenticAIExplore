from pathlib import Path

from engine.graph_builder import PipelineGraphBuilder
from engine.mermaid_renderer import MermaidRenderer
from engine.pipeline_parser import GitLabPipelineParser
from engine.yaml_loader import YamlLoader


def test_render_groups_jobs_by_stage_and_renders_needs_edges() -> None:
    fixture_path = Path(__file__).parent / "fixtures" / "simple_pipeline.yml"
    pipeline = GitLabPipelineParser().parse(YamlLoader().load(fixture_path))
    graph = PipelineGraphBuilder().build(pipeline)

    mermaid = MermaidRenderer().render(pipeline, graph)

    assert 'subgraph stage_0["build"]' in mermaid
    assert 'job_0["build_api"]' in mermaid
    assert 'subgraph stage_1["test"]' in mermaid
    assert "job_0 --> job_2" in mermaid
    assert "job_1 --> job_2" in mermaid
    assert "job_2 --> job_3" in mermaid
