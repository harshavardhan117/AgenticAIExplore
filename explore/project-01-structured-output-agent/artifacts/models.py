"""Data models used by the artifact module."""

from typing import Any

from pydantic import BaseModel


class ResolvedArtifact(BaseModel):
    """The normalized information produced after artifact resolution."""

    user_summary: str
    output_format: dict[str, Any]
    provider_name: str
