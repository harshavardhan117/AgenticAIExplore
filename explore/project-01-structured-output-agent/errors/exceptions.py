"""Exception classes used by the structured-output agent."""

from errors.codes import ErrorCode


class StructuredOutputError(Exception):
    """Base exception carrying a stable error code and safe message."""

    code: ErrorCode

    def __init__(self, message: str) -> None:
        """Store the message and initialize Python's base exception."""
        self.message = message
        super().__init__(message)


class InvalidInputError(StructuredOutputError):
    """Raised when the caller provides an incomplete or invalid request."""

    code = ErrorCode.INVALID_INPUT


class ArtifactNotFoundError(StructuredOutputError):
    """Raised when a requested stored artifact does not exist."""

    code = ErrorCode.ARTIFACT_NOT_FOUND


class InvalidArtifactError(StructuredOutputError):
    """Raised when a stored artifact exists but has invalid content."""

    code = ErrorCode.INVALID_ARTIFACT


class UnsupportedProviderError(StructuredOutputError):
    """Raised when the requested provider has no registered adapter."""

    code = ErrorCode.UNSUPPORTED_PROVIDER


class ProviderConfigurationError(StructuredOutputError):
    """Raised when a provider's required configuration is invalid or missing."""

    code = ErrorCode.PROVIDER_CONFIGURATION_ERROR


class ProviderRequestError(StructuredOutputError):
    """Raised when a configured provider fails while serving a request."""

    code = ErrorCode.PROVIDER_REQUEST_ERROR


class InternalError(StructuredOutputError):
    """Raised for unexpected application failures with a safe message."""

    code = ErrorCode.INTERNAL_ERROR
