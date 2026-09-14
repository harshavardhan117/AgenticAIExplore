"""Parser strategy interface — one implementation per CI platform."""

from abc import ABC, abstractmethod

from domain.models import LoadedYamlDocument, PipelineDefinition


class Parser(ABC):
    """Contract every platform-specific parser (GitLab, GitHub, ...) must implement."""

    @abstractmethod
    def can_parse(self, document: LoadedYamlDocument) -> bool:
        """Return True if this parser understands the given document's shape."""

    @abstractmethod
    def parse(self, document: LoadedYamlDocument) -> PipelineDefinition:
        """Convert a loaded YAML document into the common pipeline shape.

        Raises on fatal structural problems (e.g. missing stages) — a job that
        cannot be parsed into a valid PipelineDefinition should never be
        silently downgraded to a Finding.
        """
