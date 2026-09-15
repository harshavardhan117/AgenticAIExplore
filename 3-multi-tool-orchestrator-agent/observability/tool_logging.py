"""Shared tool-call logging decorator."""

import functools
import logging
import time

from observability.context import current_run_id


def log_tool_call(fn):
    logger = logging.getLogger(fn.__module__)

    @functools.wraps(fn)
    def wrapper(*args, **kwargs):
        start = time.monotonic()
        try:
            result = fn(*args, **kwargs)
        except Exception as e:
            duration_ms = round((time.monotonic() - start) * 1000, 1)
            logger.info(f"trace_id={current_run_id()} tool={fn.__name__} status=error duration_ms={duration_ms} error={e}")
            raise
        duration_ms = round((time.monotonic() - start) * 1000, 1)
        logger.info(f"trace_id={current_run_id()} tool={fn.__name__} status=success duration_ms={duration_ms}")
        return result

    return wrapper
