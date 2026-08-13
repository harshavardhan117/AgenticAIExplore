"""Create and connect the concrete objects used by the application."""

from pathlib import Path

from artifacts.registration import register_builtin_strategies
from artifacts.resolver import ArtifactResolver
from engine.orchestrator import StructuredOutputOrchestrator
from prompts.builder import PromptBuilder
from prompts.repair_builder import RepairPromptBuilder
from providers.factory import ProviderFactory
from providers.registration import register_builtin_providers
from providers.service import ProviderService
from validation.json_response_validator import JsonResponseValidator


def build_orchestrator() -> StructuredOutputOrchestrator:
    """Create the application's real collaborators and connect them."""
    artifact_root = Path(__file__).parent.parent / "artifacts"
    provider_factory = ProviderFactory()
    register_builtin_providers(provider_factory)
    artifact_resolver = ArtifactResolver()
    register_builtin_strategies(artifact_resolver, artifact_root)

    return StructuredOutputOrchestrator(
        artifact_resolver=artifact_resolver,
        prompt_builder=PromptBuilder(),
        repair_prompt_builder=RepairPromptBuilder(),
        provider_service=ProviderService(provider_factory),
        response_validator=JsonResponseValidator(),
    )
