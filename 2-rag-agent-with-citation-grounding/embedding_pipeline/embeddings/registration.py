"""Register embedding providers shipped with this application."""

from embedding_pipeline.embeddings.interfaces import EmbeddingProvider
from embedding_pipeline.embeddings.factory import EmbeddingProviderFactory
from embedding_pipeline.embeddings.oci_config import OciEmbeddingConfig
from embedding_pipeline.embeddings.oci_provider import OciEmbeddingProvider


def register_builtin_embedding_providers(factory: EmbeddingProviderFactory) -> None:
    """Enable OCI without coupling the factory to OCI implementation details."""
    factory.register("oci", build_oci_embedding_provider)


def build_oci_embedding_provider() -> EmbeddingProvider:
    """Create an OCI embedding provider from environment configuration."""
    return OciEmbeddingProvider(OciEmbeddingConfig.from_environment())
