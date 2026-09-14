from pathlib import Path

import pytest

from parsers.registry import build_default_registry
from tools.yaml_loader import load_yaml_document

FIXTURE = Path(__file__).parent.parent / "fixtures" / "simple_pipeline.yml"


def test_registry_resolves_gitlab_parser():
    document = load_yaml_document(FIXTURE)
    registry = build_default_registry()

    pipeline = registry.parse(document)

    assert set(pipeline.jobs) == {"build_api", "lint", "test_api", "deploy_staging"}


def test_registry_raises_when_no_parser_matches():
    registry = build_default_registry()
    document = load_yaml_document(FIXTURE)
    document.content = {"totally": "unrecognized shape"}

    with pytest.raises(ValueError, match="No registered parser"):
        registry.resolve(document)
