"""Stable error codes exposed by the structured-output agent."""

from enum import Enum


class ErrorCode(str, Enum):
    """Machine-readable error codes returned by the application."""

    INVALID_INPUT = "INVALID_INPUT"
    ARTIFACT_NOT_FOUND = "ARTIFACT_NOT_FOUND"
    INVALID_ARTIFACT = "INVALID_ARTIFACT"
    UNSUPPORTED_PROVIDER = "UNSUPPORTED_PROVIDER"
    PROVIDER_CONFIGURATION_ERROR = "PROVIDER_CONFIGURATION_ERROR"
    PROVIDER_REQUEST_ERROR = "PROVIDER_REQUEST_ERROR"
    MODEL_OUTPUT_INVALID = "MODEL_OUTPUT_INVALID"
    INTERNAL_ERROR = "INTERNAL_ERROR"
