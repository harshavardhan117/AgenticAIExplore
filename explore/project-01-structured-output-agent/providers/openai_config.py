"""Configuration values required by the OpenAI generation provider."""

import os

from pydantic import BaseModel

from errors.exceptions import ProviderConfigurationError

class OpenAiProviderConfig(BaseModel):
    """OpenAI API settings supplied by application configuration."""

    api_key: str
    model_id: str

    @classmethod
    def from_environment(cls) -> "OpenAiProviderConfig":
        """Create OpenAI configuration from environment variables."""
        return cls(
            api_key=cls._get_required_environment_value("OPENAI_API_KEY"),
            model_id=cls._get_required_environment_value("OPENAI_MODEL_ID"),
        )

    @staticmethod
    def _get_required_environment_value(variable_name: str) -> str:
        """Return a non-empty environment variable value."""
        value = os.getenv(variable_name)

        if not value or not value.strip():
            raise ProviderConfigurationError(
                f"Missing required environment variable: {variable_name}"
            )

        return value.strip()
