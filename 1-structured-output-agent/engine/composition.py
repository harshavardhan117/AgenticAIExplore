"""Create and connect the concrete objects used by the application."""

from pathlib import Path

from artifacts.resolver import ArtifactResolver
from artifacts.strategies import InlineArtifactStrategy, StoredFileArtifactStrategy
from engine.orchestrator import StructuredOutputOrchestrator
from prompts.builder import PromptBuilder
from prompts.repair_builder import RepairPromptBuilder
from providers.factory import ProviderFactory
from providers.service import ProviderService
from validation.json_response_validator import JsonResponseValidator


def build_orchestrator() -> StructuredOutputOrchestrator:
    """Create the application's real collaborators and connect them."""
    artifact_root = Path(__file__).parent.parent / "artifacts"
    artifact_resolver = ArtifactResolver(
        strategies=[
            InlineArtifactStrategy(),
            StoredFileArtifactStrategy(artifact_root),
        ]
    )

    return StructuredOutputOrchestrator(
        artifact_resolver=artifact_resolver,
        prompt_builder=PromptBuilder(),
        repair_prompt_builder=RepairPromptBuilder(),
        provider_service=ProviderService(ProviderFactory()),
        response_validator=JsonResponseValidator(),
    )
