"""Create provider adapters from a requested provider name."""

from collections.abc import Callable

from errors.exceptions import UnsupportedProviderError
from providers.contracts import GenerationProvider


class ProviderFactory:
    """Create provider adapters from builders registered by the application."""

    def __init__(self) -> None:
        """Start with no providers; application wiring decides what to enable."""
        self._provider_builders: dict[str, Callable[[], GenerationProvider]] = {}

    def register(
        self,
        provider_name: str,
        provider_builder: Callable[[], GenerationProvider],
    ) -> None:
        """Register one provider builder under a normalized provider name."""
        normalized_provider_name = provider_name.strip().lower()

        if not normalized_provider_name:
            raise ValueError("provider_name must be non-empty text")

        if normalized_provider_name in self._provider_builders:
            raise ValueError(f"Provider is already registered: {provider_name}")

        self._provider_builders[normalized_provider_name] = provider_builder

    def create(self, provider_name: str) -> GenerationProvider:
        """Create the provider requested by name."""
        normalized_provider_name = provider_name.strip().lower()
        provider_builder = self._provider_builders.get(normalized_provider_name)

        if provider_builder is None:
            raise UnsupportedProviderError(f"Unsupported provider: {provider_name}")

        return provider_builder()
