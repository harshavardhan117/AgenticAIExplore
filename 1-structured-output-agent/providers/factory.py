"""Create provider adapters from a requested provider name."""

from collections.abc import Callable

from errors.exceptions import UnsupportedProviderError
from providers.contracts import GenerationProvider


class ProviderFactory:
    """Create the configured adapter for a supported generation provider."""

    def __init__(self) -> None:
        """Register provider names with the functions that build them."""
        self._provider_builders: dict[str, Callable[[], GenerationProvider]] = {
            "oci": self._create_oci_provider,
            "openai": self._create_openai_provider,
        }

    def create(self, provider_name: str) -> GenerationProvider:
        """Create an OCI or OpenAI provider from the requested name."""
        normalized_provider_name = provider_name.strip().lower()
        provider_builder = self._provider_builders.get(normalized_provider_name)

        if provider_builder is None:
            raise UnsupportedProviderError(f"Unsupported provider: {provider_name}")

        return provider_builder()

    @staticmethod
    def _create_oci_provider() -> GenerationProvider:
        """Create an OCI provider using its environment configuration."""
        from providers.oci_config import OciProviderConfig
        from providers.oci_provider import OciGenerationProvider

        return OciGenerationProvider(OciProviderConfig.from_environment())

    @staticmethod
    def _create_openai_provider() -> GenerationProvider:
        """Create an OpenAI provider using its environment configuration."""
        from providers.openai_config import OpenAiProviderConfig
        from providers.openai_provider import OpenAiGenerationProvider

        return OpenAiGenerationProvider(OpenAiProviderConfig.from_environment())
