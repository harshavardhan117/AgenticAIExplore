"""Unit tests for retry behaviour in the main orchestration layer."""

from artifacts.models import ResolvedArtifact
from engine.orchestrator import StructuredOutputOrchestrator
from errors.codes import ErrorCode
from prompts.builder import PromptBuilder
from prompts.repair_builder import RepairPromptBuilder
from providers.models import ModelResponse
from validation.json_response_validator import JsonResponseValidator


class FixedArtifactResolver:
    """Return one artifact so the test avoids filesystem concerns."""

    def resolve(self, _user_request) -> ResolvedArtifact:
        return ResolvedArtifact(
            user_summary="Create a bug ticket",
            output_format={"summary": ""},
            provider_name="fake",
        )


class SequencedProviderService:
    """Return preselected model responses and record the prompts received."""

    def __init__(self, responses: list[ModelResponse]) -> None:
        self.responses = responses
        self.prompts = []

    def generate(self, prompt, provider_name: str) -> ModelResponse:
        self.prompts.append((prompt, provider_name))
        return self.responses.pop(0)


def build_orchestrator_with(responses: list[ModelResponse]):
    """Build an orchestrator with controlled test dependencies."""
    provider_service = SequencedProviderService(responses)
    orchestrator = StructuredOutputOrchestrator(
        artifact_resolver=FixedArtifactResolver(),
        prompt_builder=PromptBuilder(),
        repair_prompt_builder=RepairPromptBuilder(),
        provider_service=provider_service,
        response_validator=JsonResponseValidator(),
    )
    return orchestrator, provider_service


def test_retries_once_when_first_model_output_is_invalid_then_returns_success() -> None:
    orchestrator, provider_service = build_orchestrator_with(
        [
            ModelResponse(text="not json", provider_name="fake", request_id="first"),
            ModelResponse(
                text='{"summary": "Login failure"}',
                provider_name="fake",
                request_id="second",
            ),
        ]
    )

    response = orchestrator.execute({"not": "used by this isolated test"})

    assert response.success is True
    assert response.output == {"summary": "Login failure"}
    assert response.retry_count == 1
    assert response.request_id == "second"
    assert len(provider_service.prompts) == 2
    assert len(provider_service.prompts[1][0].messages) == 3


def test_returns_final_invalid_response_after_two_repairs() -> None:
    orchestrator, provider_service = build_orchestrator_with(
        [ModelResponse(text="not json", provider_name="fake")] * 3
    )

    response = orchestrator.execute({"not": "used by this isolated test"})

    assert response.success is False
    assert response.error_code == ErrorCode.MODEL_OUTPUT_INVALID
    assert response.retry_count == 2
    assert len(provider_service.prompts) == 3
