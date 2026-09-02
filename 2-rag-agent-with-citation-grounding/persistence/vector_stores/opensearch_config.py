"""Configuration required by the OpenSearch vector-store adapter."""

import os

from dotenv import load_dotenv
from pydantic import BaseModel, ConfigDict, Field, SecretStr, model_validator


class OpenSearchVectorStoreConfig(BaseModel):
    """Validated REST connection settings for one OpenSearch vector index."""

    model_config = ConfigDict(extra="forbid")

    endpoint: str = Field(min_length=1)
    index_name: str = Field(default="rag_embedded_chunks_v1", min_length=1)
    username: str | None = None
    password: SecretStr | None = None
    verify_certificates: bool = True
    vector_engine: str = Field(default="faiss", min_length=1)
    vector_space_type: str = Field(default="cosinesimil", min_length=1)

    @model_validator(mode="after")
    def validate_basic_auth_pair(self) -> "OpenSearchVectorStoreConfig":
        """Require basic-auth credentials to be supplied together when used."""

        if (self.username is None) != (self.password is None):
            raise ValueError("OPENSEARCH_USERNAME and OPENSEARCH_PASSWORD must be set together")
        return self

    @classmethod
    def from_environment(cls) -> "OpenSearchVectorStoreConfig":
        """Create configuration from the OPENSEARCH_* environment variables."""

        load_dotenv()
        return cls(
            endpoint=cls._required("OPENSEARCH_URL").rstrip("/"),
            index_name=os.getenv("OPENSEARCH_INDEX_NAME", "rag_embedded_chunks_v1"),
            username=cls._optional("OPENSEARCH_USERNAME"),
            password=cls._optional("OPENSEARCH_PASSWORD"),
            verify_certificates=cls._boolean("OPENSEARCH_VERIFY_CERTIFICATES", True),
            vector_engine=os.getenv("OPENSEARCH_VECTOR_ENGINE", "faiss"),
            vector_space_type=os.getenv("OPENSEARCH_VECTOR_SPACE_TYPE", "cosinesimil"),
        )

    @staticmethod
    def _required(variable_name: str) -> str:
        value = OpenSearchVectorStoreConfig._optional(variable_name)
        if value is None:
            raise ValueError(f"Missing required environment variable: {variable_name}")
        return value

    @staticmethod
    def _optional(variable_name: str) -> str | None:
        value = os.getenv(variable_name)
        return value.strip() if value and value.strip() else None

    @staticmethod
    def _boolean(variable_name: str, default: bool) -> bool:
        value = os.getenv(variable_name)
        if value is None:
            return default
        normalized = value.strip().lower()
        if normalized in {"true", "1", "yes"}:
            return True
        if normalized in {"false", "0", "no"}:
            return False
        raise ValueError(f"{variable_name} must be true or false")
