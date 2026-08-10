"""Resolve a user request into a normalized artifact object."""

from typing import Any

from artifacts.models import ResolvedArtifact
from artifacts.strategies import ArtifactResolutionStrategy
from errors.exceptions import InvalidInputError


class ArtifactResolver:
    """Select a strategy that resolves a user request."""

    def __init__(self, strategies: list[ArtifactResolutionStrategy]) -> None:
        """Store the available artifact-resolution strategies."""
        self.strategies = strategies

    def resolve(self, user_request: dict[str, Any]) -> ResolvedArtifact:
        """Choose a strategy and create a resolved artifact."""
        if not isinstance(user_request, dict):
            raise InvalidInputError("user_request must be a JSON object")

        output_format = user_request.get("output_format")

        for strategy in self.strategies:
            if strategy.can_resolve(output_format):
                return strategy.resolve(user_request)

        raise InvalidInputError("output_format has an unsupported shape")
