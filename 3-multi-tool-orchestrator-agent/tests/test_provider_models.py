from pathlib import Path

from engine.models import PipelineDefinition, PipelineGraph
from providers.models import PipelineReviewInput, ReviewMode


def test_review_input_has_safe_defaults_and_serializes() -> None:
    pipeline = PipelineDefinition(
        source_file=Path(".gitlab-ci.yml"),
        stages=["test"],
        jobs={},
    )
    graph = PipelineGraph(nodes={}, edges=[])

    review_input = PipelineReviewInput(
        review_mode=ReviewMode.OPTIMIZE,
        pipeline=pipeline,
        graph=graph,
        mermaid="flowchart LR\n",
    )

    assert review_input.constraints.max_recommendations == 3
    assert review_input.constraints.allow_yaml_patch is False
    assert review_input.model_dump(mode="json")["schema_version"] == "v1"
