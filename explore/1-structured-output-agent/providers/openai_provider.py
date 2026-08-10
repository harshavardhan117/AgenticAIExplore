"""OpenAI implementation of the generation-provider contract."""

from openai import OpenAI

from prompts.models import Prompt, PromptMessage
from providers.openai_config import OpenAiProviderConfig
from providers.models import ModelResponse


MAX_OUTPUT_TOKENS = 1024


class OpenAiGenerationProvider:
    """Create and hold an authenticated OpenAI SDK client."""

    def __init__(self, config: OpenAiProviderConfig) -> None:
        """Create the OpenAI SDK client using the supplied API key."""
        self.config = config
        self.client = OpenAI(api_key=self.config.api_key)

    @staticmethod
    def _to_openai_input_message(prompt_message: PromptMessage) -> dict[str, str]:
        """Convert one generic prompt message into OpenAI Responses API input."""
        role_mapping = {
            "system": "developer",
            "user": "user",
        }

        return {
            "role": role_mapping[prompt_message.role],
            "content": prompt_message.content,
        }

    def generate(self, prompt: Prompt) -> ModelResponse:
        """Send a prompt to OpenAI and return a normalized model response."""
        response = self.client.responses.create(
            model=self.config.model_id,
            input=[
                self._to_openai_input_message(prompt_message)
                for prompt_message in prompt.messages
            ],
            max_output_tokens=MAX_OUTPUT_TOKENS,
        )

        return ModelResponse(
            text=response.output_text,
            provider_name="openai",
            request_id=getattr(response, "_request_id", None),
        )
