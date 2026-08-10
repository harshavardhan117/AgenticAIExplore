"""Build repair prompts after JSON-output validation failures."""

from prompts.models import Prompt, PromptMessage
from validation.json_response_validator import JsonValidationResult


REPAIR_INSTRUCTION = (
    "Your previous response did not meet the required JSON format. "
    "Correct the errors below and return one JSON object only. "
    "Do not include Markdown or an explanation."
)


class RepairPromptBuilder:
    """Append validation feedback to an original prompt for one retry."""

    def build(
        self,
        original_prompt: Prompt,
        validation_result: JsonValidationResult,
    ) -> Prompt:
        """Create a retry prompt containing the reported validation errors."""
        error_lines = "\n".join(f"- {error}" for error in validation_result.errors)
        repair_content = f"{REPAIR_INSTRUCTION}\n\nErrors to correct:\n{error_lines}"

        return Prompt(
            messages=[
                *original_prompt.messages,
                PromptMessage(role="user", content=repair_content),
            ]
        )
