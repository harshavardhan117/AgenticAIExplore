"""Build provider-neutral prompts from resolved artifacts."""

import json

from artifacts.models import ResolvedArtifact
from prompts.models import Prompt, PromptMessage


DEFAULT_SYSTEM_INSTRUCTION = (
    "Return one valid JSON object only. "
    "Use the required output format as the exact structure for your response."
)


class PromptBuilder:
    """Create the default prompt used for structured-output generation."""

    def build(self, resolved_artifact: ResolvedArtifact) -> Prompt:
        """Create system and user messages from a resolved artifact."""
        output_format_json = json.dumps(resolved_artifact.output_format, indent=2)
        user_content = (
            "User summary:\n"
            f"{resolved_artifact.user_summary}\n\n"
            "Required output format:\n"
            f"{output_format_json}"
        )

        return Prompt(
            messages=[
                PromptMessage(
                    role="system",
                    content=DEFAULT_SYSTEM_INSTRUCTION,
                ),
                PromptMessage(role="user", content=user_content),
            ]
        )
