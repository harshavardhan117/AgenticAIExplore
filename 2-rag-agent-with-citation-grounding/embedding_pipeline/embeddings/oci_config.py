"""Configuration values required by the OCI embedding provider."""

import os

from pydantic import BaseModel


class OciEmbeddingConfig(BaseModel):
    """OCI connection and Cohere embedding-model settings."""

    config_file_path: str
    profile_name: str = "DEFAULT"
    compartment_id: str
    endpoint: str
    model_id: str

    @classmethod
    def from_environment(cls) -> "OciEmbeddingConfig":
        """Create OCI configuration from environment variables."""
        return cls(
            config_file_path=os.getenv("OCI_CONFIG_FILE_PATH", "~/.oci/config"),
            profile_name=os.getenv("OCI_PROFILE_NAME", "DEFAULT"),
            compartment_id=cls._required("OCI_COMPARTMENT_ID"),
            endpoint=cls._required("OCI_ENDPOINT"),
            model_id=cls._required("OCI_EMBEDDING_MODEL_ID"),
        )

    @staticmethod
    def _required(variable_name: str) -> str:
        value = os.getenv(variable_name)
        if not value or not value.strip():
            raise ValueError(f"Missing required environment variable: {variable_name}")
        return value.strip()
