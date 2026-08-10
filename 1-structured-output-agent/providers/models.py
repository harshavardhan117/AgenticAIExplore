"""Provider-neutral data models for model generation results."""

from pydantic import BaseModel


class ModelResponse(BaseModel):
    """The normalized result returned by any generation provider."""

    text: str
    provider_name: str
    request_id: str | None = None
