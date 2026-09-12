from pathlib import Path

from engine.graph_analyzer import PipelineGraphAnalyzer
from engine.graph_builder import PipelineGraphBuilder
from engine.models import FindingSeverity, JobDefinition, PipelineDefinition, SourceLocation


def _job(job_id: str, needs: list[str] | None = None) -> JobDefinition:
    return JobDefinition(
        id=job_id,
        stage="test",
        needs=needs or [],
        source_location=SourceLocation(
            file_path=Path(".gitlab-ci.yml"),
            yaml_path=job_id,
        ),
    )


def test_analyze_calculates_parallel_execution_layers() -> None:
    pipeline = PipelineDefinition(
        source_file=Path(".gitlab-ci.yml"),
        stages=["test"],
        jobs={
            "build": _job("build"),
            "lint": _job("lint"),
            "test": _job("test", ["build", "lint"]),
            "deploy": _job("deploy", ["test"]),
        },
    )

    result = PipelineGraphAnalyzer().analyze(PipelineGraphBuilder().build(pipeline))

    assert result.is_acyclic is True
    assert result.execution_layers == [["build", "lint"], ["test"], ["deploy"]]
    assert result.root_job_ids == ["build", "lint"]
    assert result.terminal_job_ids == ["deploy"]
    assert result.findings[0].severity == FindingSeverity.INFO


def test_analyze_reports_dependency_cycles() -> None:
    pipeline = PipelineDefinition(
        source_file=Path(".gitlab-ci.yml"),
        stages=["test"],
        jobs={
            "job_a": _job("job_a", ["job_b"]),
            "job_b": _job("job_b", ["job_a"]),
        },
    )

    result = PipelineGraphAnalyzer().analyze(PipelineGraphBuilder().build(pipeline))

    assert result.is_acyclic is False
    assert result.execution_layers == []
    assert result.cycle_job_ids == ["job_a", "job_b"]
    assert result.findings[-1].id == "dependency-cycle-detected"
    assert result.findings[-1].severity == FindingSeverity.ERROR
