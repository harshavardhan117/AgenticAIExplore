"""OpenAI implementation of the generation-provider contract."""

import logging
import time

from openai import OpenAI

from prompts.models import Prompt, PromptMessage
from providers.openai_config import OpenAiProviderConfig
from providers.models import ModelResponse


MAX_OUTPUT_TOKENS = 1024
logger = logging.getLogger(__name__)


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
        started_at = time.perf_counter()
        logger.info("OpenAI model call started")

        try:
            response = self.client.responses.create(
                model=self.config.model_id,
                input=[
                    self._to_openai_input_message(prompt_message)
                    for prompt_message in prompt.messages
                ],
                max_output_tokens=MAX_OUTPUT_TOKENS,
            )
        except Exception as error:
            duration_ms = round((time.perf_counter() - started_at) * 1000)
            logger.warning(
                "OpenAI model call failed",
                extra={
                    "provider": "openai",
                    "duration_ms": duration_ms,
                    "error_type": type(error).__name__,
                },
            )
            raise

        request_id = getattr(response, "_request_id", None)
        duration_ms = round((time.perf_counter() - started_at) * 1000)
        logger.info(
            "OpenAI model call finished",
            extra={
                "provider": "openai",
                "request_id": request_id,
                "duration_ms": duration_ms,
            },
        )

        return ModelResponse(
            text=response.output_text,
            provider_name="openai",
            request_id=request_id,
        )
