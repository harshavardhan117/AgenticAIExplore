"""Coordinate provider selection and model generation."""

from prompts.models import Prompt
from providers.factory import ProviderFactory
from providers.models import ModelResponse


class ProviderService:
    """Use the requested provider to generate a normalized model response."""

    def __init__(self, provider_factory: ProviderFactory) -> None:
        """Store the factory that creates supported provider adapters."""
        self.provider_factory = provider_factory

    def generate(self, prompt: Prompt, provider_name: str) -> ModelResponse:
        """Create the requested provider and generate a model response."""
        provider = self.provider_factory.create(provider_name)
        return provider.generate(prompt)
