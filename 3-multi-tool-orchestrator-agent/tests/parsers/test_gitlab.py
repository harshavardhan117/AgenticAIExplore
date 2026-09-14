from pathlib import Path

from parsers.gitlab import GitLabParser
from tools.yaml_loader import load_yaml_document

FIXTURE = Path(__file__).parent.parent / "fixtures" / "simple_pipeline.yml"


def test_can_parse_true_for_gitlab_pipeline():
    doc = load_yaml_document(FIXTURE)
    assert GitLabParser().can_parse(doc) is True


def test_parse_builds_stages_and_jobs():
    doc = load_yaml_document(FIXTURE)
    pipeline = GitLabParser().parse(doc)

    assert pipeline.stages == ["build", "test", "deploy"]
    assert set(pipeline.jobs) == {"build_api", "lint", "test_api", "deploy_staging"}
    assert pipeline.jobs["test_api"].needs == ["build_api", "lint"]
    assert pipeline.jobs["deploy_staging"].stage == "deploy"
