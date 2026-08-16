"""OCI implementation of the generation-provider contract."""

import logging
import time

import oci

from prompts.models import Prompt, PromptMessage
from providers.oci_config import OciProviderConfig
from providers.models import ModelResponse


MAX_COMPLETION_TOKENS = 1024
logger = logging.getLogger(__name__)


class OciGenerationProvider:
    """Create and hold an authenticated OCI Generative AI client."""

    def __init__(self, config: OciProviderConfig) -> None:
        """Load OCI profile authentication and create the SDK client."""
        self.config = config

        oci_profile_config = oci.config.from_file(
            file_location=self.config.config_file_path,
            profile_name=self.config.profile_name,
        )
        oci.config.validate_config(oci_profile_config)

        self.client = oci.generative_ai_inference.GenerativeAiInferenceClient(
            config=oci_profile_config,
            service_endpoint=self.config.endpoint,
            retry_strategy=oci.retry.NoneRetryStrategy(),
            timeout=(10, 240),
        )

    @staticmethod
    def _to_oci_message(prompt_message: PromptMessage):
        """Convert one generic prompt message into an OCI SDK message."""
        content = oci.generative_ai_inference.models.TextContent()
        content.text = prompt_message.content

        oci_message = oci.generative_ai_inference.models.Message()
        oci_message.role = prompt_message.role.upper()
        oci_message.content = [content]

        return oci_message

    def _build_chat_details(self, prompt: Prompt):
        """Build the complete OCI chat request from a generic prompt."""
        chat_request = oci.generative_ai_inference.models.GenericChatRequest()
        chat_request.api_format = (
            oci.generative_ai_inference.models.BaseChatRequest.API_FORMAT_GENERIC
        )
        chat_request.messages = [
            self._to_oci_message(prompt_message)
            for prompt_message in prompt.messages
        ]
        chat_request.max_completion_tokens = MAX_COMPLETION_TOKENS

        chat_details = oci.generative_ai_inference.models.ChatDetails()
        chat_details.serving_mode = (
            oci.generative_ai_inference.models.OnDemandServingMode(
                model_id=self.config.model_id
            )
        )
        chat_details.chat_request = chat_request
        chat_details.compartment_id = self.config.compartment_id

        return chat_details

    def generate(self, prompt: Prompt) -> ModelResponse:
        """Send a prompt to OCI and return a normalized model response."""
        started_at = time.perf_counter()
        logger.info("OCI model call started")

        try:
            response = self.client.chat(self._build_chat_details(prompt))
        except Exception as error:
            duration_ms = round((time.perf_counter() - started_at) * 1000)
            logger.warning(
                "OCI model call failed",
                extra={
                    "provider": "oci",
                    "duration_ms": duration_ms,
                    "error_type": type(error).__name__,
                },
            )
            raise

        request_id = getattr(response, "request_id", None)
        duration_ms = round((time.perf_counter() - started_at) * 1000)
        logger.info(
            "OCI model call finished",
            extra={
                "provider": "oci",
                "request_id": request_id,
                "duration_ms": duration_ms,
            },
        )

        return ModelResponse(
            text=self._extract_response_text(response),
            provider_name="oci",
            request_id=request_id,
        )

    @staticmethod
    def _extract_response_text(response) -> str:
        """Extract text from the first response choice returned by OCI."""
        choices = response.data.chat_response.choices

        if not choices:
            return ""

        message = choices[0].message
        if not message or not message.content:
            return ""

        text_parts = []
        for content_item in message.content:
            text = getattr(content_item, "text", None)
            if text:
                text_parts.append(text)

        return "\n".join(text_parts).strip()
