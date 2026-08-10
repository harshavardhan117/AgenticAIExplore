"""Configuration values required by the OCI generation provider."""

import os

from pydantic import BaseModel

from errors.exceptions import ProviderConfigurationError

class OciProviderConfig(BaseModel):
    """OCI connection and model settings supplied by application configuration."""

    config_file_path: str
    profile_name: str = "DEFAULT"
    compartment_id: str
    endpoint: str
    model_id: str

    @classmethod
    def from_environment(cls) -> "OciProviderConfig":
        """Create OCI configuration from environment variables."""
        return cls(
            config_file_path=os.getenv("OCI_CONFIG_FILE_PATH", "~/.oci/config"),
            profile_name=os.getenv("OCI_PROFILE_NAME", "DEFAULT"),
            compartment_id=cls._get_required_environment_value("OCI_COMPARTMENT_ID"),
            endpoint=cls._get_required_environment_value("OCI_ENDPOINT"),
            model_id=cls._get_required_environment_value("OCI_MODEL_ID"),
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
