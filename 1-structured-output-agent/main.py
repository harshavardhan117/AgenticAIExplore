"""Thin entry point for running the structured-output agent."""

import logging
from typing import Any

from engine.composition import build_orchestrator
from errors.codes import ErrorCode
from errors.exceptions import StructuredOutputError
from responses.models import ExecutionResponse


logger = logging.getLogger(__name__)


def run(user_request: dict[str, Any]) -> ExecutionResponse:
    """Run one user request and return a JSON-ready execution response."""
    try:
        logger.info("Structured-output request started")
        orchestrator = build_orchestrator()
        response = orchestrator.execute(user_request)
        logger.info(
            "Structured-output request finished",
            extra={
                "success": response.success,
                "provider": response.provider_name,
                "request_id": response.request_id,
                "retry_count": response.retry_count,
            },
        )
        return response
    except StructuredOutputError as error:
        logger.warning(
            "Structured-output request rejected",
            extra={"error_code": error.code},
        )
        return ExecutionResponse(
            success=False,
            message=error.message,
            error_code=error.code,
            retry_count=0,
        )
    except Exception:
        logger.warning("Structured-output request failed unexpectedly")
        return ExecutionResponse(
            success=False,
            message="Unexpected internal error",
            error_code=ErrorCode.INTERNAL_ERROR,
            retry_count=0,
        )
