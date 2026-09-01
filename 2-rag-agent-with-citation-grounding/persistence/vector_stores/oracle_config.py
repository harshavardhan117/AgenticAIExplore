"""Configuration required by the Oracle AI Database vector-store adapter."""

import os

from pydantic import BaseModel, ConfigDict, Field, SecretStr


class OracleVectorStoreConfig(BaseModel):
    """Validated connection settings for the Oracle FREEPDB1 vector store."""

    model_config = ConfigDict(extra="forbid")

    host: str = Field(min_length=1)
    port: int = Field(default=8123, ge=1, le=65535)
    service_name: str = Field(default="FREEPDB1", min_length=1)
    username: str = Field(min_length=1)
    password: SecretStr
    table_name: str = Field(
        default="RAG_EMBEDDED_CHUNKS",
        pattern=r"^[A-Za-z][A-Za-z0-9_$#]{0,127}$",
    )

    @property
    def dsn(self) -> str:
        """Return the Oracle Easy Connect descriptor used by python-oracledb."""

        return f"{self.host}:{self.port}/{self.service_name}"

    @classmethod
    def from_environment(cls) -> "OracleVectorStoreConfig":
        """Create configuration from the ORACLE_VECTOR_* environment variables."""

        return cls(
            host=cls._required("ORACLE_VECTOR_HOST"),
            port=int(os.getenv("ORACLE_VECTOR_PORT", "8123")),
            service_name=os.getenv("ORACLE_VECTOR_SERVICE_NAME", "FREEPDB1"),
            username=cls._required("ORACLE_VECTOR_USERNAME"),
            password=cls._required("ORACLE_VECTOR_PASSWORD"),
            table_name=os.getenv("ORACLE_VECTOR_TABLE_NAME", "RAG_EMBEDDED_CHUNKS"),
        )

    @staticmethod
    def _required(variable_name: str) -> str:
        value = os.getenv(variable_name)
        if not value or not value.strip():
            raise ValueError(f"Missing required environment variable: {variable_name}")
        return value.strip()
