"""Unit tests for provider selection, delegation, and configuration."""

import pytest

from errors.exceptions import ProviderConfigurationError, UnsupportedProviderError
from prompts.models import Prompt, PromptMessage
from providers.factory import ProviderFactory
from providers.models import ModelResponse
from providers.oci_config import OciProviderConfig
from providers.openai_config import OpenAiProviderConfig
from providers.service import ProviderService


class FakeProvider:
    """Small provider substitute that records the received prompt."""

    def __init__(self) -> None:
        self.received_prompt: Prompt | None = None

    def generate(self, prompt: Prompt) -> ModelResponse:
        self.received_prompt = prompt
        return ModelResponse(text='{"summary": "done"}', provider_name="fake")


class FakeProviderFactory:
    """Factory substitute that always returns one controlled provider."""

    def __init__(self, provider: FakeProvider) -> None:
        self.provider = provider
        self.requested_name: str | None = None

    def create(self, provider_name: str) -> FakeProvider:
        self.requested_name = provider_name
        return self.provider


def test_factory_rejects_an_unsupported_provider() -> None:
    with pytest.raises(UnsupportedProviderError, match="Unsupported provider"):
        ProviderFactory().create("unknown")


def test_factory_normalizes_provider_name_before_selecting_a_builder() -> None:
    factory = ProviderFactory()
    fake_provider = FakeProvider()
    factory.register("oci", lambda: fake_provider)

    provider = factory.create(" OCI ")

    assert provider is fake_provider


def test_factory_rejects_a_duplicate_provider_registration() -> None:
    factory = ProviderFactory()
    factory.register("fake", FakeProvider)

    with pytest.raises(ValueError, match="already registered"):
        factory.register("FAKE", FakeProvider)


def test_provider_service_delegates_to_the_provider_created_by_its_factory() -> None:
    provider = FakeProvider()
    factory = FakeProviderFactory(provider)
    service = ProviderService(factory)  # type: ignore[arg-type]
    prompt = Prompt(messages=[PromptMessage(role="user", content="hello")])

    response = service.generate(prompt, "fake")

    assert factory.requested_name == "fake"
    assert provider.received_prompt == prompt
    assert response.provider_name == "fake"


def test_oci_configuration_reads_required_values_from_environment(monkeypatch) -> None:
    monkeypatch.setenv("OCI_COMPARTMENT_ID", "compartment")
    monkeypatch.setenv("OCI_ENDPOINT", "https://oci.example")
    monkeypatch.setenv("OCI_MODEL_ID", "model")

    config = OciProviderConfig.from_environment()

    assert config.compartment_id == "compartment"
    assert config.profile_name == "DEFAULT"
    assert config.config_file_path == "~/.oci/config"


def test_openai_configuration_rejects_a_missing_api_key(monkeypatch) -> None:
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    monkeypatch.setenv("OPENAI_MODEL_ID", "model")

    with pytest.raises(ProviderConfigurationError, match="OPENAI_API_KEY"):
        OpenAiProviderConfig.from_environment()


def test_oci_configuration_rejects_a_blank_required_value(monkeypatch) -> None:
    monkeypatch.setenv("OCI_COMPARTMENT_ID", " ")

    with pytest.raises(ProviderConfigurationError, match="OCI_COMPARTMENT_ID"):
        OciProviderConfig.from_environment()
