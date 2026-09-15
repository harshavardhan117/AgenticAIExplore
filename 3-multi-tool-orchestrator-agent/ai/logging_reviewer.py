"""Decorator-pattern wrapper: same AIReviewer interface, adds logging around chat()."""

import logging
import time

from ai.base import AIReviewer
from domain.models import AIReviewInput, AIReviewOutput
from observability.context import current_run_id


class LoggingAIReviewer(AIReviewer):
    def __init__(self, inner: AIReviewer) -> None:
        self._inner = inner
        self._logger = logging.getLogger(type(inner).__module__)

    def chat(self, review_input: AIReviewInput) -> AIReviewOutput:
        tool_name = type(self._inner).__name__
        start = time.monotonic()
        try:
            result = self._inner.chat(review_input)
        except Exception as e:
            duration_ms = round((time.monotonic() - start) * 1000, 1)
            self._logger.info(f"trace_id={current_run_id()} tool={tool_name} status=error duration_ms={duration_ms} error={e}")
            raise
        duration_ms = round((time.monotonic() - start) * 1000, 1)
        self._logger.info(f"trace_id={current_run_id()} tool={tool_name} status=success duration_ms={duration_ms}")
        return result
