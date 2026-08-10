"""Contracts that every generation provider must satisfy."""

from typing import Protocol

from prompts.models import Prompt
from providers.models import ModelResponse


class GenerationProvider(Protocol):
    """Generate a normalized response from a provider-neutral prompt."""

    def generate(self, prompt: Prompt) -> ModelResponse:
        """Send a prompt to the provider and return its normalized response."""
        ...
