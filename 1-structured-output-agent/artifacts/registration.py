"""Register the artifact-resolution strategies shipped with this application."""

from pathlib import Path

from artifacts.resolver import ArtifactResolver
from artifacts.strategies import InlineArtifactStrategy, StoredFileArtifactStrategy


def register_builtin_strategies(
    resolver: ArtifactResolver,
    artifact_root: Path,
) -> None:
    """Enable built-in strategies in their intended selection order.

    The resolver uses the first strategy whose can_resolve() method matches.
    To add a strategy later, add it here or in another application's setup.
    """
    resolver.register(InlineArtifactStrategy())
    resolver.register(StoredFileArtifactStrategy(artifact_root))
