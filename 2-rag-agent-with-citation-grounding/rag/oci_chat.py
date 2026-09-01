"""Minimal OCI chat client used by the Confluence RAG service."""

import os

import oci

from rag.oci_chat_formats import OciChatFormat, builtin_chat_formats


class OciChatClient:
    """Read OCI configuration and send one prompt using its required API format."""

    def __init__(self) -> None:
        config_file_path = os.getenv("OCI_CONFIG_FILE_PATH", "~/.oci/config")
        profile_name = os.getenv("OCI_PROFILE_NAME", "DEFAULT")
        self._compartment_id = self._required("OCI_COMPARTMENT_ID")
        self._endpoint = self._required("OCI_ENDPOINT")
        self.model_id = self._required("OCI_CHAT_MODEL_ID")
        self._request_format = os.getenv("OCI_CHAT_REQUEST_FORMAT", "cohere").strip().lower()
        self._chat_format = self._select_chat_format(self._request_format)
        self._max_tokens = int(os.getenv("OCI_CHAT_MAX_TOKENS", "800"))
        self._temperature = float(os.getenv("OCI_CHAT_TEMPERATURE", "0"))
        profile = oci.config.from_file(config_file_path, profile_name)
        oci.config.validate_config(profile)
        self._client = oci.generative_ai_inference.GenerativeAiInferenceClient(
            config=profile,
            service_endpoint=self._endpoint,
            retry_strategy=oci.retry.NoneRetryStrategy(),
            timeout=(10, 240),
        )

    def generate(self, prompt: str) -> str:
        """Return the non-empty text generated for one grounded prompt."""

        details = oci.generative_ai_inference.models.ChatDetails(
            compartment_id=self._compartment_id,
            serving_mode=oci.generative_ai_inference.models.OnDemandServingMode(
                model_id=self.model_id
            ),
            chat_request=self._chat_format.build_request(
                prompt,
                self._temperature,
                self._max_tokens,
            ),
        )
        response = self._client.chat(details)
        text = self._chat_format.response_text(response.data.chat_response)
        if not text or not text.strip():
            raise ValueError("OCI chat returned an empty answer.")
        return text.strip()

    @staticmethod
    def _select_chat_format(format_name: str) -> OciChatFormat:
        """Resolve a clear user-facing format name to its OCI adapter."""

        formats = builtin_chat_formats()
        try:
            return formats[format_name]
        except KeyError as error:
            supported = ", ".join(sorted(formats))
            raise ValueError(
                f"OCI_CHAT_REQUEST_FORMAT must be one of: {supported}."
            ) from error

    @staticmethod
    def _required(variable_name: str) -> str:
        value = os.getenv(variable_name)
        if not value or not value.strip():
            raise ValueError(f"Missing required environment variable: {variable_name}")
        return value.strip()
