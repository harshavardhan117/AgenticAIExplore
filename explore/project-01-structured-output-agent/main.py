"""Thin entry point for running the structured-output agent."""

from typing import Any

from engine.orchestrator import StructuredOutputOrchestrator
from errors.codes import ErrorCode
from errors.exceptions import StructuredOutputError
from responses.models import ExecutionResponse


def run(user_request: dict[str, Any]) -> ExecutionResponse:
    """Run one user request and return a JSON-ready execution response."""
    try:
        orchestrator = StructuredOutputOrchestrator()
        return orchestrator.execute(user_request)
    except StructuredOutputError as error:
        return ExecutionResponse(
            success=False,
            message=error.message,
            error_code=error.code,
            retry_count=0,
        )
    except Exception:
        return ExecutionResponse(
            success=False,
            message="Unexpected internal error",
            error_code=ErrorCode.INTERNAL_ERROR,
            retry_count=0,
        )
