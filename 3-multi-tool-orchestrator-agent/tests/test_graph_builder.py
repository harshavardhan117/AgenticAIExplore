from pathlib import Path

import pytest

from engine.graph_builder import GraphBuildError, PipelineGraphBuilder
from engine.models import JobDefinition, PipelineDefinition, SourceLocation


def _job(job_id: str, stage: str, needs: list[str] | None = None) -> JobDefinition:
    return JobDefinition(
        id=job_id,
        stage=stage,
        needs=needs or [],
        source_location=SourceLocation(
            file_path=Path(".gitlab-ci.yml"),
            yaml_path=job_id,
        ),
    )


def test_build_creates_nodes_and_prerequisite_to_dependent_edges() -> None:
    pipeline = PipelineDefinition(
        source_file=Path(".gitlab-ci.yml"),
        stages=["build", "test", "deploy"],
        jobs={
            "build": _job("build", "build"),
            "lint": _job("lint", "build"),
            "test": _job("test", "test", ["build", "lint"]),
            "deploy": _job("deploy", "deploy", ["test"]),
        },
    )

    graph = PipelineGraphBuilder().build(pipeline)

    assert set(graph.nodes) == {"build", "lint", "test", "deploy"}
    assert {(edge.source_job_id, edge.target_job_id) for edge in graph.edges} == {
        ("build", "test"),
        ("lint", "test"),
        ("test", "deploy"),
    }


def test_build_rejects_a_missing_needed_job() -> None:
    pipeline = PipelineDefinition(
        source_file=Path(".gitlab-ci.yml"),
        stages=["test"],
        jobs={"test": _job("test", "test", ["build"])},
    )

    with pytest.raises(GraphBuildError, match="needs missing job 'build'"):
        PipelineGraphBuilder().build(pipeline)


def test_build_rejects_a_duplicate_needed_job() -> None:
    pipeline = PipelineDefinition(
        source_file=Path(".gitlab-ci.yml"),
        stages=["build", "test"],
        jobs={
            "build": _job("build", "build"),
            "test": _job("test", "test", ["build", "build"]),
        },
    )

    with pytest.raises(GraphBuildError, match="duplicate need 'build'"):
        PipelineGraphBuilder().build(pipeline)
