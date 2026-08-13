"""Unit tests for resolving inline and stored output artifacts."""

import json

import pytest

from artifacts.resolver import ArtifactResolver
from artifacts.strategies import InlineArtifactStrategy, StoredFileArtifactStrategy
from errors.exceptions import ArtifactNotFoundError, InvalidArtifactError, InvalidInputError


def make_resolver(artifact_root):
    """Create a resolver with both supported resolution strategies."""
    resolver = ArtifactResolver()
    resolver.register(InlineArtifactStrategy())
    resolver.register(StoredFileArtifactStrategy(artifact_root))
    return resolver


def test_resolves_an_inline_output_format_and_defaults_to_oci(tmp_path) -> None:
    artifact = make_resolver(tmp_path).resolve(
        {
            "user_summary": "  Create a bug ticket  ",
            "output_format": {"summary": ""},
        }
    )

    assert artifact.user_summary == "Create a bug ticket"
    assert artifact.output_format == {"summary": ""}
    assert artifact.provider_name == "oci"


def test_resolves_a_named_artifact_from_its_versioned_folder(tmp_path) -> None:
    artifact_file = tmp_path / "jira" / "v1" / "output_format.json"
    artifact_file.parent.mkdir(parents=True)
    artifact_file.write_text(json.dumps({"fields": {"summary": ""}}), encoding="utf-8")

    artifact = make_resolver(tmp_path).resolve(
        {
            "user_summary": "Create a bug ticket",
            "output_format": "jira",
            "output_format_version": "v1",
            "provider": "openai",
        }
    )

    assert artifact.output_format == {"fields": {"summary": ""}}
    assert artifact.provider_name == "openai"


def test_rejects_a_request_without_a_user_summary(tmp_path) -> None:
    with pytest.raises(InvalidInputError, match="user_summary"):
        make_resolver(tmp_path).resolve({"output_format": {"summary": ""}})


def test_rejects_a_missing_named_artifact(tmp_path) -> None:
    with pytest.raises(ArtifactNotFoundError):
        make_resolver(tmp_path).resolve(
            {
                "user_summary": "Create a bug ticket",
                "output_format": "jira",
                "output_format_version": "v1",
            }
        )


def test_rejects_an_unsafe_artifact_name(tmp_path) -> None:
    with pytest.raises(InvalidInputError, match="output_format"):
        make_resolver(tmp_path).resolve(
            {
                "user_summary": "Create a bug ticket",
                "output_format": "../secrets",
                "output_format_version": "v1",
            }
        )


def test_rejects_a_stored_artifact_with_invalid_json(tmp_path) -> None:
    artifact_file = tmp_path / "jira" / "v1" / "output_format.json"
    artifact_file.parent.mkdir(parents=True)
    artifact_file.write_text("{invalid json", encoding="utf-8")

    with pytest.raises(InvalidArtifactError, match="invalid JSON"):
        make_resolver(tmp_path).resolve(
            {
                "user_summary": "Create a bug ticket",
                "output_format": "jira",
                "output_format_version": "v1",
            }
        )


def test_rejects_a_stored_artifact_that_is_not_a_json_object(tmp_path) -> None:
    artifact_file = tmp_path / "jira" / "v1" / "output_format.json"
    artifact_file.parent.mkdir(parents=True)
    artifact_file.write_text('["not", "an object"]', encoding="utf-8")

    with pytest.raises(InvalidArtifactError, match="JSON object"):
        make_resolver(tmp_path).resolve(
            {
                "user_summary": "Create a bug ticket",
                "output_format": "jira",
                "output_format_version": "v1",
            }
        )


def test_rejects_an_unsupported_output_format_shape(tmp_path) -> None:
    with pytest.raises(InvalidInputError, match="unsupported shape"):
        make_resolver(tmp_path).resolve(
            {"user_summary": "Create a bug ticket", "output_format": ["summary"]}
        )
