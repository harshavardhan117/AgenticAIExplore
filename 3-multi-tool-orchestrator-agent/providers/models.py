"""Vendor-neutral contracts for an optional model-based pipeline review.

These domain models are deliberately independent of OCI, OpenAI, or another
provider SDK. A future provider adapter converts ``PipelineReviewInput`` into
that provider's request format.
"""

from enum import Enum
from typing import Literal
from uuid import UUID, uuid4

from pydantic import BaseModel, Field

from engine.models import PipelineDefinition, PipelineFinding, PipelineGraph


class ReviewMode(str, Enum):
    """The bounded type of help requested from the language model."""

    EXPLAIN = "explain"
    OPTIMIZE = "optimize"


class ReviewConstraints(BaseModel):
    """Guardrails applied by every provider adapter."""

    max_recommendations: int = Field(default=3, ge=1, le=5)
    require_evidence_references: bool = True
    allow_yaml_patch: bool = False
    allow_unverified_assumptions: bool = False


class PipelineReviewInput(BaseModel):
    """Validated deterministic context supplied to a model reviewer.

    Raw YAML is intentionally excluded. This avoids sending scripts, variables,
    and possible secrets to a provider when the parsed pipeline facts are enough
    for the requested review.
    """

    schema_version: Literal["v1"] = "v1"
    request_id: UUID = Field(default_factory=uuid4)
    review_mode: ReviewMode = ReviewMode.OPTIMIZE
    pipeline: PipelineDefinition
    graph: PipelineGraph
    mermaid: str
    findings: list[PipelineFinding] = Field(default_factory=list)
    constraints: ReviewConstraints = Field(default_factory=ReviewConstraints)
