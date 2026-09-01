"""Pydantic contracts for the Confluence RAG evaluation dataset and results."""

from pydantic import BaseModel, ConfigDict, Field


class EvaluationCase(BaseModel):
    """One known question and the evidence or behavior expected from the RAG."""

    model_config = ConfigDict(extra="forbid")

    id: str = Field(min_length=1)
    question: str = Field(min_length=1)
    reference_answer: str | None = None
    expected_source_urls: list[str] = Field(default_factory=list)
    expected_keywords: list[str] = Field(default_factory=list)
    should_abstain: bool = False


class EvaluationResult(BaseModel):
    """One RAG execution retained for metrics and later debugging."""

    model_config = ConfigDict(extra="forbid")

    case_id: str = Field(min_length=1)
    question: str = Field(min_length=1)
    answer: str = Field(min_length=1)
    retrieved_source_urls: list[str] = Field(default_factory=list)
    metric_values: dict[str, float | bool] = Field(default_factory=dict)
    metric_reasons: dict[str, str] = Field(default_factory=dict)


class AnswerRelevancyJudgment(BaseModel):
    """One evaluator-model judgment of whether an answer addresses its question."""

    model_config = ConfigDict(extra="forbid")

    score: float = Field(ge=0.0, le=1.0)
    reason: str = Field(min_length=1)


class CitationCorrectnessJudgment(BaseModel):
    """One evaluator-model judgment of whether answer citations support their claims."""

    model_config = ConfigDict(extra="forbid")

    score: float = Field(ge=0.0, le=1.0)
    reason: str = Field(min_length=1)
