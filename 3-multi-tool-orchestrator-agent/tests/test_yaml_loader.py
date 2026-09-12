from pathlib import Path

import pytest

from engine.yaml_loader import YamlLoadError, YamlLoader


def test_load_returns_a_mapping_for_valid_gitlab_yaml(tmp_path: Path) -> None:
    yaml_file = tmp_path / ".gitlab-ci.yml"
    yaml_file.write_text(
        """stages:\n  - build\n  - test\n\n"
        ".job_template: &job_template\n  image: python:3.12\n\n"
        "test:\n  <<: *job_template\n  stage: test\n  script: pytest\n""",
        encoding="utf-8",
    )

    document = YamlLoader().load(yaml_file)

    assert document.source_file == yaml_file.resolve()
    assert document.content["stages"] == ["build", "test"]
    assert document.content["test"]["image"] == "python:3.12"


def test_load_rejects_a_missing_file(tmp_path: Path) -> None:
    missing_file = tmp_path / ".gitlab-ci.yml"

    with pytest.raises(YamlLoadError, match="does not exist"):
        YamlLoader().load(missing_file)


def test_load_rejects_malformed_yaml(tmp_path: Path) -> None:
    yaml_file = tmp_path / ".gitlab-ci.yml"
    yaml_file.write_text("stages: [build\n", encoding="utf-8")

    with pytest.raises(YamlLoadError, match="Malformed YAML"):
        YamlLoader().load(yaml_file)


def test_load_rejects_a_non_mapping_root(tmp_path: Path) -> None:
    yaml_file = tmp_path / ".gitlab-ci.yml"
    yaml_file.write_text("- build\n- test\n", encoding="utf-8")

    with pytest.raises(YamlLoadError, match="mapping at its root"):
        YamlLoader().load(yaml_file)


def test_load_rejects_an_oversized_file(tmp_path: Path) -> None:
    yaml_file = tmp_path / ".gitlab-ci.yml"
    yaml_file.write_text("stages: [build]\n", encoding="utf-8")

    with pytest.raises(YamlLoadError, match="size limit"):
        YamlLoader(max_file_size_bytes=1).load(yaml_file)
