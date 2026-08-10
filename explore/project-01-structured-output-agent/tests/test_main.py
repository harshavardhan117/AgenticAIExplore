"""Unit tests for the thin outer application boundary."""

import main

from errors.codes import ErrorCode
from errors.exceptions import InvalidInputError
from responses.models import ExecutionResponse


class SuccessfulOrchestrator:
    """Controlled orchestrator that returns a completed response."""

    def execute(self, _user_request) -> ExecutionResponse:
        return ExecutionResponse(
            success=True,
            message="done",
            output={"summary": "done"},
            retry_count=0,
        )


class InvalidInputOrchestrator:
    """Controlled orchestrator that simulates a known request error."""

    def execute(self, _user_request) -> ExecutionResponse:
        raise InvalidInputError("user_summary must be non-empty text")


class BrokenOrchestrator:
    """Controlled orchestrator that simulates an unhandled implementation error."""

    def execute(self, _user_request) -> ExecutionResponse:
        raise RuntimeError("database password should never be exposed")


def test_run_returns_the_orchestrator_response(monkeypatch) -> None:
    monkeypatch.setattr(main, "StructuredOutputOrchestrator", SuccessfulOrchestrator)

    response = main.run({"user_summary": "anything"})

    assert response.success is True
    assert response.output == {"summary": "done"}


def test_run_converts_a_known_exception_to_a_safe_error_response(monkeypatch) -> None:
    monkeypatch.setattr(main, "StructuredOutputOrchestrator", InvalidInputOrchestrator)

    response = main.run({})

    assert response.success is False
    assert response.error_code == ErrorCode.INVALID_INPUT
    assert response.message == "user_summary must be non-empty text"


def test_run_hides_unexpected_error_details(monkeypatch) -> None:
    monkeypatch.setattr(main, "StructuredOutputOrchestrator", BrokenOrchestrator)

    response = main.run({})

    assert response.success is False
    assert response.error_code == ErrorCode.INTERNAL_ERROR
    assert response.message == "Unexpected internal error"
