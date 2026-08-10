"""Unit tests for default and repair prompt construction."""

from artifacts.models import ResolvedArtifact
from prompts.builder import PromptBuilder
from prompts.repair_builder import RepairPromptBuilder
from validation.json_response_validator import JsonValidationResult


def test_default_prompt_contains_the_summary_and_required_format() -> None:
    prompt = PromptBuilder().build(
        ResolvedArtifact(
            user_summary="Create a login bug",
            output_format={"summary": ""},
            provider_name="oci",
        )
    )

    assert [message.role for message in prompt.messages] == ["system", "user"]
    assert "Create a login bug" in prompt.messages[1].content
    assert '"summary": ""' in prompt.messages[1].content


def test_repair_prompt_preserves_original_messages_and_adds_errors() -> None:
    original_prompt = PromptBuilder().build(
        ResolvedArtifact(
            user_summary="Create a login bug",
            output_format={"summary": ""},
            provider_name="oci",
        )
    )
    validation_result = JsonValidationResult(
        is_valid=False,
        error_message="$.summary is required",
        errors=["$.summary is required"],
    )

    repaired_prompt = RepairPromptBuilder().build(original_prompt, validation_result)

    assert len(repaired_prompt.messages) == 3
    assert repaired_prompt.messages[:2] == original_prompt.messages
    assert "$.summary is required" in repaired_prompt.messages[2].content
