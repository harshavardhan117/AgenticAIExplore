"""Register the provider implementations shipped with this application."""

from providers.contracts import GenerationProvider
from providers.factory import ProviderFactory
from providers.oci_config import OciProviderConfig
from providers.oci_provider import OciGenerationProvider
from providers.openai_config import OpenAiProviderConfig
from providers.openai_provider import OpenAiGenerationProvider


def register_builtin_providers(factory: ProviderFactory) -> None:
    """Enable OCI and OpenAI without making the factory know their details.

    Keep built-in provider choices here. To add a provider later, add its adapter
    and builder, then register that builder here or in another application's setup.
    """
    factory.register("oci", build_oci_provider)
    factory.register("openai", build_openai_provider)


def build_oci_provider() -> GenerationProvider:
    """Create an OCI provider using its environment configuration."""
    return OciGenerationProvider(OciProviderConfig.from_environment())


def build_openai_provider() -> GenerationProvider:
    """Create an OpenAI provider using its environment configuration."""
    return OpenAiGenerationProvider(OpenAiProviderConfig.from_environment())
