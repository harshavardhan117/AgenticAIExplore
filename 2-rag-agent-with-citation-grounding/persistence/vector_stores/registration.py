"""Register Oracle and OpenSearch adapters shipped with this application."""

from persistence.vector_stores.interfaces import VectorStore
from persistence.vector_stores.factory import VectorStoreFactory
from persistence.vector_stores.opensearch_config import OpenSearchVectorStoreConfig
from persistence.vector_stores.opensearch_store import OpenSearchVectorStore
from persistence.vector_stores.oracle_config import OracleVectorStoreConfig
from persistence.vector_stores.oracle_store import OracleVectorStore


def register_builtin_vector_stores(factory: VectorStoreFactory) -> None:
    """Enable configured Oracle and OpenSearch adapters in one factory."""

    factory.register("oracle", build_oracle_vector_store)
    factory.register("opensearch", build_opensearch_vector_store)


def build_oracle_vector_store() -> VectorStore:
    """Create the Oracle adapter from environment configuration."""

    return OracleVectorStore(OracleVectorStoreConfig.from_environment())


def build_opensearch_vector_store() -> VectorStore:
    """Create the OpenSearch adapter from environment configuration."""

    return OpenSearchVectorStore(OpenSearchVectorStoreConfig.from_environment())
