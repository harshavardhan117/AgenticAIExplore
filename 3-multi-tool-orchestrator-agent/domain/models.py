"""Domain entities for the CI/CD pipeline orchestrator."""

from enum import Enum
from pathlib import Path
from typing import Any

from pydantic import BaseModel, Field


# ---------------------------------------------------------------------------
# Job information parsed from raw YAML
# ---------------------------------------------------------------------------


class SourceLocation(BaseModel):
    """Points back to the file and logical YAML path a value came from."""

    file_path: Path
    yaml_path: str


class LoadedYamlDocument(BaseModel):
    """Raw parsed content of one YAML file, before GitLab/GitHub interpretation."""

    source_file: Path
    content: dict[str, Any]


class JobDefinition(BaseModel):
    """One executable job, after platform-specific parsing."""

    id: str
    stage: str
    needs: list[str] = Field(default_factory=list)
    source_location: SourceLocation


class PipelineDefinition(BaseModel):
    """The common, platform-neutral shape every parser strategy must produce."""

    source_file: Path
    stages: list[str]
    jobs: dict[str, JobDefinition]


# ---------------------------------------------------------------------------
# Dependency graph built from parsed jobs
# ---------------------------------------------------------------------------


class Edge(BaseModel):
    """A directed dependency: source_job_id must complete before target_job_id."""

    source_job_id: str
    target_job_id: str


class PipelineGraph(BaseModel):
    """The job-dependency graph used for analysis and rendering."""

    nodes: dict[str, JobDefinition]
    edges: list[Edge]


# ---------------------------------------------------------------------------
# Findings emitted by checkers and the analyzer
# ---------------------------------------------------------------------------


class FindingSeverity(str, Enum):
    """Severity assigned to a deterministic finding."""

    INFO = "info"
    WARNING = "warning"
    ERROR = "error"


class Finding(BaseModel):
    """One deterministic observation, always evidence-backed."""

    id: str
    severity: FindingSeverity
    title: str
    description: str
    evidence: list[SourceLocation] = Field(default_factory=list)


# ---------------------------------------------------------------------------
# Analyzer output: structural facts computed from the graph
# ---------------------------------------------------------------------------


class AnalysisResult(BaseModel):
    """Deterministic structural facts calculated from a pipeline graph."""

    is_acyclic: bool
    execution_layers: list[list[str]] = Field(default_factory=list)
    root_job_ids: list[str] = Field(default_factory=list)
    terminal_job_ids: list[str] = Field(default_factory=list)
    findings: list[Finding] = Field(default_factory=list)


# ---------------------------------------------------------------------------
# Optional AI review: input sent to the model, output it returns
# ---------------------------------------------------------------------------


class AIReviewInput(BaseModel):
    """Deterministic facts sent to the AI reviewer — no raw YAML/script content."""

    validation_findings: list[Finding] = Field(default_factory=list)
    analysis: AnalysisResult


class AIFindingReview(BaseModel):
    """The AI's explanation for one existing finding."""

    finding_id: str
    explanation: str
    priority: int
    impact_estimate: str


class AIReviewOutput(BaseModel):
    """The AI's response: no new claims, only explanation of existing findings."""

    reviews: list[AIFindingReview] = Field(default_factory=list)


# ---------------------------------------------------------------------------
# Final response returned by the orchestrator
# ---------------------------------------------------------------------------


class PipelineReport(BaseModel):
    """Single aggregate result: everything the CLI needs to display."""

    pipeline: PipelineDefinition
    graph: PipelineGraph
    analysis: AnalysisResult
    validation_findings: list[Finding] = Field(default_factory=list)
    mermaid: str
    report_markdown: str
    ai_review: AIReviewOutput | None = None
    ai_error: str | None = None
