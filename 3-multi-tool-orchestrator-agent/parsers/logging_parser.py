"""Decorator-pattern wrapper: same Parser interface, adds logging around parse()."""

import logging
import time

from domain.models import LoadedYamlDocument, PipelineDefinition
from observability.context import current_run_id
from parsers.base import Parser


class LoggingParser(Parser):
    def __init__(self, inner: Parser) -> None:
        self._inner = inner
        self._logger = logging.getLogger(type(inner).__module__)

    def can_parse(self, document: LoadedYamlDocument) -> bool:
        return self._inner.can_parse(document)

    def parse(self, document: LoadedYamlDocument) -> PipelineDefinition:
        tool_name = type(self._inner).__name__
        start = time.monotonic()
        try:
            result = self._inner.parse(document)
        except Exception as e:
            duration_ms = round((time.monotonic() - start) * 1000, 1)
            self._logger.info(f"trace_id={current_run_id()} tool={tool_name} status=error duration_ms={duration_ms} error={e}")
            raise
        duration_ms = round((time.monotonic() - start) * 1000, 1)
        self._logger.info(f"trace_id={current_run_id()} tool={tool_name} status=success duration_ms={duration_ms}")
        return result
