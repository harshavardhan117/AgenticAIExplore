"""Provider-neutral data models for prompts."""

from typing import Literal

from pydantic import BaseModel


class PromptMessage(BaseModel):
    """One message in a prompt conversation."""

    role: Literal["system", "user"]
    content: str


class Prompt(BaseModel):
    """A provider-neutral prompt made from ordered messages."""

    messages: list[PromptMessage]
