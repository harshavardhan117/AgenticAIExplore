"""Entry point for coordinating structured-output generation."""

from typing import Any

from artifacts.models import ResolvedArtifact
from artifacts.resolver import ArtifactResolver
from errors.codes import ErrorCode
from prompts.builder import PromptBuilder
from prompts.models import Prompt
from prompts.repair_builder import RepairPromptBuilder
from providers.models import ModelResponse
from providers.service import ProviderService
from responses.models import ExecutionResponse
from validation.json_response_validator import JsonResponseValidator, JsonValidationResult


MAX_REPAIR_ATTEMPTS = 2


class StructuredOutputOrchestrator:
    """Accepts a request and will coordinate the project modules."""

    def __init__(
        self,
        artifact_resolver: ArtifactResolver,
        prompt_builder: PromptBuilder,
        repair_prompt_builder: RepairPromptBuilder,
        provider_service: ProviderService,
        response_validator: JsonResponseValidator,
    ) -> None:
        """Store the collaborators needed to coordinate one request."""
        self.artifact_resolver = artifact_resolver
        self.prompt_builder = prompt_builder
        self.repair_prompt_builder = repair_prompt_builder
        self.provider_service = provider_service
        self.response_validator = response_validator

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
