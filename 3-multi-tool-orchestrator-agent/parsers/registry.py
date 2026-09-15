"""Registry that picks the right parser strategy for a given document."""

from domain.models import LoadedYamlDocument, PipelineDefinition
from parsers.base import Parser
from parsers.gitlab import GitLabParser
from parsers.logging_parser import LoggingParser


class ParserRegistry:
    """Holds registered parser strategies and resolves the one that matches."""

    def __init__(self) -> None:
        self._parsers: list[Parser] = []

    def register(self, parser: Parser) -> None:
        self._parsers.append(parser)

    def resolve(self, document: LoadedYamlDocument) -> Parser:
        for parser in self._parsers:
            if parser.can_parse(document):
                return parser
        raise ValueError(f"No registered parser can handle '{document.source_file}'.")

    def parse(self, document: LoadedYamlDocument) -> PipelineDefinition:
        return self.resolve(document).parse(document)


def build_default_registry() -> ParserRegistry:
    """Registers every built-in parser strategy. Add new platforms here only."""
    registry = ParserRegistry()
    registry.register(LoggingParser(GitLabParser()))
    return registry
