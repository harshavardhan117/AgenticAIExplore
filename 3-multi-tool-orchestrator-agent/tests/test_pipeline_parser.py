from pathlib import Path

import pytest

from engine.models import LoadedYamlDocument
from engine.pipeline_parser import DEFAULT_STAGES, GitLabPipelineParser, PipelineParseError


def test_parse_extracts_visible_jobs_stages_and_needs() -> None:
    document = LoadedYamlDocument(
        source_file=Path(".gitlab-ci.yml"),
        content={
            "stages": ["build", "test"],
            "variables": {"ENVIRONMENT": "test"},
            ".base_job": {"stage": "test"},
            "build_api": {"stage": "build"},
            "test_api": {"stage": "test", "needs": "build_api"},
        },
    )

    pipeline = GitLabPipelineParser().parse(document)

    assert pipeline.stages == ["build", "test"]
    assert set(pipeline.jobs) == {"build_api", "test_api"}
    assert pipeline.jobs["test_api"].needs == ["build_api"]


def test_parse_uses_gitlab_default_stages_and_default_job_stage() -> None:
    document = LoadedYamlDocument(
        source_file=Path(".gitlab-ci.yml"),
        content={"unit_test": {"script": "pytest"}},
    )

    pipeline = GitLabPipelineParser().parse(document)

    assert pipeline.stages == list(DEFAULT_STAGES)
    assert pipeline.jobs["unit_test"].stage == "test"


def test_parse_rejects_an_undefined_stage() -> None:
    document = LoadedYamlDocument(
        source_file=Path(".gitlab-ci.yml"),
        content={
            "stages": ["build"],
            "unit_test": {"stage": "test"},
        },
    )

    with pytest.raises(PipelineParseError, match="undefined stage 'test'"):
        GitLabPipelineParser().parse(document)


def test_parse_rejects_unsupported_needs_object_syntax() -> None:
    document = LoadedYamlDocument(
        source_file=Path(".gitlab-ci.yml"),
        content={
            "build": {"stage": "build"},
            "test": {
                "stage": "test",
                "needs": [{"job": "build", "artifacts": True}],
            },
        },
    )

    with pytest.raises(PipelineParseError, match="unsupported 'needs' syntax"):
        GitLabPipelineParser().parse(document)
