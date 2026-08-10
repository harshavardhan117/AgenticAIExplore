"""Unit tests for the OCI adapter without making an OCI network request."""

from types import SimpleNamespace

from prompts.models import Prompt, PromptMessage
from providers.oci_config import OciProviderConfig
from providers.oci_provider import OciGenerationProvider


def make_config() -> OciProviderConfig:
    """Return safe fake configuration used only to build local SDK objects."""
    return OciProviderConfig(
        config_file_path="unused",
        compartment_id="compartment",
        endpoint="https://oci.example",
        model_id="model",
    )


def test_build_chat_details_converts_generic_prompt_to_oci_request() -> None:
    provider = object.__new__(OciGenerationProvider)
    provider.config = make_config()
    prompt = Prompt(
        messages=[
            PromptMessage(role="system", content="Return JSON"),
            PromptMessage(role="user", content="Create a ticket"),
        ]
    )

    details = provider._build_chat_details(prompt)

    assert details.compartment_id == "compartment"
    assert details.serving_mode.model_id == "model"
    assert details.chat_request.max_completion_tokens == 1024
    assert [message.role for message in details.chat_request.messages] == ["SYSTEM", "USER"]
    assert details.chat_request.messages[1].content[0].text == "Create a ticket"


def test_extract_response_text_joins_text_content_and_handles_empty_choices() -> None:
    response = SimpleNamespace(
        data=SimpleNamespace(
            chat_response=SimpleNamespace(
                choices=[
                    SimpleNamespace(
                        message=SimpleNamespace(
                            content=[
                                SimpleNamespace(text="first"),
                                SimpleNamespace(text="second"),
                            ]
                        )
                    )
                ]
            )
        )
    )
    empty_response = SimpleNamespace(
        data=SimpleNamespace(chat_response=SimpleNamespace(choices=[]))
    )

    assert OciGenerationProvider._extract_response_text(response) == "first\nsecond"
    assert OciGenerationProvider._extract_response_text(empty_response) == ""


def test_generate_normalizes_the_oci_sdk_response() -> None:
    provider = object.__new__(OciGenerationProvider)
    provider.config = make_config()
    request_details = object()
    provider._build_chat_details = lambda _prompt: request_details

    sdk_response = SimpleNamespace(
        request_id="oci-request",
        data=SimpleNamespace(
            chat_response=SimpleNamespace(
                choices=[
                    SimpleNamespace(
                        message=SimpleNamespace(content=[SimpleNamespace(text="{\"summary\": \"done\"}")])
                    )
                ]
            )
        ),
    )

    class FakeOciClient:
        def __init__(self) -> None:
            self.received_details = None

        def chat(self, details):
            self.received_details = details
            return sdk_response

    provider.client = FakeOciClient()

    response = provider.generate(Prompt(messages=[]))

    assert provider.client.received_details is request_details
    assert response.text == '{"summary": "done"}'
    assert response.provider_name == "oci"
    assert response.request_id == "oci-request"
