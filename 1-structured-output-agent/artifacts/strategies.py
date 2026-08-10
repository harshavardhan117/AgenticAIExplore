"""Strategies for resolving different artifact input formats."""

import json
import re
from pathlib import Path
from typing import Any, Protocol

from artifacts.models import ResolvedArtifact
from errors.exceptions import (
    ArtifactNotFoundError,
    InvalidArtifactError,
    InvalidInputError,
)


class ArtifactResolutionStrategy(Protocol):
    """Common shape used by every artifact-resolution strategy."""

    def can_resolve(self, output_format: Any) -> bool:
        """Return whether this strategy can resolve the supplied format."""
        ...

    def resolve(self, user_request: dict[str, Any]) -> ResolvedArtifact:
        """Resolve a request into a normalized artifact."""
        ...


def _get_user_summary(user_request: dict[str, Any]) -> str:
    """Return a required, non-empty user summary."""
    user_summary = user_request.get("user_summary")

    if not isinstance(user_summary, str) or not user_summary.strip():
        raise InvalidInputError("user_summary must be non-empty text")

    return user_summary.strip()


def _get_provider_name(user_request: dict[str, Any]) -> str:
    """Return the selected provider, defaulting to OCI."""
    provider_name = user_request.get("provider", "oci")

    if not isinstance(provider_name, str) or not provider_name.strip():
        raise InvalidInputError("provider must be non-empty text")

    return provider_name.strip()


class InlineArtifactStrategy:
    """Resolve an output format supplied directly in the user request."""

    def can_resolve(self, output_format: Any) -> bool:
        """Return whether this strategy handles inline JSON objects."""
        return isinstance(output_format, dict)

    def resolve(self, user_request: dict[str, Any]) -> ResolvedArtifact:
        """Create a resolved artifact from an inline JSON object."""
        output_format = user_request["output_format"]

        try:
            json.dumps(output_format)
        except (TypeError, ValueError) as error:
            raise InvalidInputError("output_format must be JSON serializable") from error

        return ResolvedArtifact(
            user_summary=_get_user_summary(user_request),
            output_format=output_format,
            provider_name=_get_provider_name(user_request),
        )


class StoredFileArtifactStrategy:
    """Resolve an artifact name and version from a local JSON file."""

    def __init__(self, artifact_root: Path) -> None:
        """Store the directory that contains named artifact folders."""
        self.artifact_root = artifact_root

    def can_resolve(self, output_format: Any) -> bool:
        """Return whether this strategy handles named artifacts."""
        return isinstance(output_format, str)

    def resolve(self, user_request: dict[str, Any]) -> ResolvedArtifact:
        """Load a named artifact and create a resolved artifact."""
        artifact_name = self._get_identifier(user_request, "output_format")
        artifact_version = self._get_identifier(
            user_request, "output_format_version"
        )
        artifact_path = (
            self.artifact_root
            / artifact_name
            / artifact_version
            / "output_format.json"
        )

        try:
            with artifact_path.open(encoding="utf-8") as artifact_file:
                output_format = json.load(artifact_file)
        except FileNotFoundError as error:
            raise ArtifactNotFoundError("Stored artifact was not found") from error
        except json.JSONDecodeError as error:
            raise InvalidArtifactError("Stored artifact contains invalid JSON") from error

        if not isinstance(output_format, dict):
            raise InvalidArtifactError("Stored artifact must contain a JSON object")

        return ResolvedArtifact(
            user_summary=_get_user_summary(user_request),
            output_format=output_format,
            provider_name=_get_provider_name(user_request),
        )

    def _get_identifier(self, user_request: dict[str, Any], field_name: str) -> str:
        """Return a safe artifact name or version for use in a file path."""
        value = user_request.get(field_name)

        if not isinstance(value, str) or not re.fullmatch(r"[A-Za-z0-9_-]+", value):
            raise InvalidInputError(
                f"{field_name} must contain letters, numbers, _ or -"
            )

        return value
