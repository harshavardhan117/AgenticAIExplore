"""Unit tests for the optional OpenAI adapter without network requests."""

from types import SimpleNamespace

import pytest

openai_provider = pytest.importorskip("providers.openai_provider")

from prompts.models import Prompt, PromptMessage
from providers.openai_config import OpenAiProviderConfig


def test_converts_generic_roles_to_openai_responses_input() -> None:
    system_message = openai_provider.OpenAiGenerationProvider._to_openai_input_message(
        PromptMessage(role="system", content="Return JSON")
    )
    user_message = openai_provider.OpenAiGenerationProvider._to_openai_input_message(
        PromptMessage(role="user", content="Create a ticket")
    )

    assert system_message == {"role": "developer", "content": "Return JSON"}
    assert user_message == {"role": "user", "content": "Create a ticket"}


def test_generate_normalizes_an_openai_sdk_response() -> None:
    provider = object.__new__(openai_provider.OpenAiGenerationProvider)
    provider.config = OpenAiProviderConfig(api_key="unused", model_id="model")

    class FakeResponsesApi:
        def __init__(self) -> None:
            self.arguments = None

        def create(self, **kwargs):
            self.arguments = kwargs
            return SimpleNamespace(output_text='{"summary": "done"}', _request_id="openai-request")

    responses_api = FakeResponsesApi()
    provider.client = SimpleNamespace(responses=responses_api)

    response = provider.generate(
        Prompt(messages=[PromptMessage(role="user", content="Create a ticket")])
    )

    assert responses_api.arguments == {
        "model": "model",
        "input": [{"role": "user", "content": "Create a ticket"}],
        "max_output_tokens": 1024,
    }
    assert response.text == '{"summary": "done"}'
    assert response.provider_name == "openai"
    assert response.request_id == "openai-request"
