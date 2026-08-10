"""Entry point for coordinating structured-output generation."""

from pathlib import Path
from typing import Any

from artifacts.models import ResolvedArtifact
from artifacts.resolver import ArtifactResolver
from artifacts.strategies import InlineArtifactStrategy, StoredFileArtifactStrategy
from errors.codes import ErrorCode
from prompts.builder import PromptBuilder
from prompts.models import Prompt
from prompts.repair_builder import RepairPromptBuilder
from providers.factory import ProviderFactory
from providers.models import ModelResponse
from providers.service import ProviderService
from responses.models import ExecutionResponse
from validation.json_response_validator import JsonResponseValidator, JsonValidationResult


MAX_REPAIR_ATTEMPTS = 2


class StructuredOutputOrchestrator:
    """Accepts a request and will coordinate the project modules."""

    def __init__(self) -> None:
        """Register the artifact strategies available to this application."""
        artifact_root = Path(__file__).parent.parent / "artifacts"

        self.artifact_resolver = ArtifactResolver(
            strategies=[
                InlineArtifactStrategy(),
                StoredFileArtifactStrategy(artifact_root),
            ]
        )
        self.prompt_builder = PromptBuilder()
        self.repair_prompt_builder = RepairPromptBuilder()
        self.provider_service = ProviderService(ProviderFactory())
        self.response_validator = JsonResponseValidator()

    def execute(self, user_request: dict[str, Any]) -> ExecutionResponse:
        """Resolve a request, generate output, and validate its JSON shape.

        Retry handling will be added here one module at a time.
        """
        resolved_artifact: ResolvedArtifact = self.artifact_resolver.resolve(
            user_request
        )
        prompt: Prompt = self.prompt_builder.build(resolved_artifact)
        current_prompt = prompt

        for attempt_number in range(MAX_REPAIR_ATTEMPTS + 1):
            model_response: ModelResponse = self.provider_service.generate(
                prompt=current_prompt,
                provider_name=resolved_artifact.provider_name,
            )
            validation_result = self.response_validator.validate(
                model_response=model_response,
                expected_output_format=resolved_artifact.output_format,
            )

            if validation_result.is_valid:
                return ExecutionResponse(
                    success=True,
                    message="Structured output generated successfully",
                    output=validation_result.parsed_output,
                    provider_name=model_response.provider_name,
                    request_id=model_response.request_id,
                    retry_count=attempt_number,
                )

            if attempt_number == MAX_REPAIR_ATTEMPTS:
                return ExecutionResponse(
                    success=False,
                    message="Model output did not match the required JSON format",
                    error_code=ErrorCode.MODEL_OUTPUT_INVALID,
                    provider_name=model_response.provider_name,
                    request_id=model_response.request_id,
                    retry_count=attempt_number,
                )

            current_prompt = self.repair_prompt_builder.build(
                original_prompt=prompt,
                validation_result=validation_result,
            )

        raise RuntimeError("Retry loop ended unexpectedly")
