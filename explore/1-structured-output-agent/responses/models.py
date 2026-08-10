"""Final response models returned by the structured-output agent."""

from typing import Any

from pydantic import BaseModel

from errors.codes import ErrorCode


class ExecutionResponse(BaseModel):
    """The provider-neutral result of one structured-output execution."""

    success: bool
    message: str
    error_code: ErrorCode | None = None
    output: dict[str, Any] | None = None
    provider_name: str | None = None
    request_id: str | None = None
    retry_count: int
    confidence_score: float | None = None
