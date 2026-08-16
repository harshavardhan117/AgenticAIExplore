"""Resolve a user request into a normalized artifact object."""

from typing import Any

from artifacts.models import ResolvedArtifact
from artifacts.strategies import ArtifactResolutionStrategy
from errors.exceptions import InvalidInputError


class ArtifactResolver:
    """Select from the artifact strategies registered by the application."""

    def __init__(self) -> None:
        """Start with no strategies; application wiring decides what to enable."""
        self.strategies: list[ArtifactResolutionStrategy] = []

    def register(self, strategy: ArtifactResolutionStrategy) -> None:
        """Add one strategy to the resolver's ordered selection list."""
        self.strategies.append(strategy)

    def resolve(self, user_request: dict[str, Any]) -> ResolvedArtifact:
        """Choose a strategy and create a resolved artifact."""
        if not isinstance(user_request, dict):
            raise InvalidInputError("user_request must be a JSON object")

        output_format = user_request.get("output_format")

        for strategy in self.strategies:
            if strategy.can_resolve(output_format):
                return strategy.resolve(user_request)

        raise InvalidInputError("output_format has an unsupported shape")
