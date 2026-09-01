"""OCI request/response adapters for supported chat model families."""

from typing import Protocol

import oci


class OciChatFormat(Protocol):
    """Convert one grounded prompt to and from an OCI model-family format."""

    def build_request(self, prompt: str, temperature: float, token_limit: int):
        """Create the provider-specific OCI chat request."""
        ...

    def response_text(self, chat_response) -> str | None:
        """Extract generated text from the provider-specific OCI response."""
        ...


class CohereChatFormat:
    """OCI's Cohere request format for Cohere Command chat models."""

    def build_request(self, prompt: str, temperature: float, token_limit: int):
        return oci.generative_ai_inference.models.CohereChatRequest(
            message=prompt,
            temperature=temperature,
            max_tokens=token_limit,
        )

    def response_text(self, chat_response) -> str | None:
        return getattr(chat_response, "text", None)


class OpenAiChatFormat:
    """OCI generic request format used by OpenAI-style chat models in OCI."""

    def build_request(self, prompt: str, temperature: float, token_limit: int):
        models = oci.generative_ai_inference.models
        return models.GenericChatRequest(
            messages=[models.UserMessage(content=[models.TextContent(text=prompt)])],
            temperature=temperature,
            max_completion_tokens=token_limit,
        )

    def response_text(self, chat_response) -> str | None:
        choices = getattr(chat_response, "choices", None) or []
        if not choices:
            return None
        content = getattr(getattr(choices[0], "message", None), "content", None) or []
        text_parts = [getattr(item, "text", "") for item in content]
        text = "".join(part for part in text_parts if part)
        return text or None


def builtin_chat_formats() -> dict[str, OciChatFormat]:
    """Return the only supported user-facing OCI chat format choices."""

    return {
        "cohere": CohereChatFormat(),
        "openai": OpenAiChatFormat(),
    }
