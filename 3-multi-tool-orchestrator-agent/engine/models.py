"""Domain models for the GitLab CI Pipeline Insight Assistant.

The initial models represent a single local GitLab CI configuration and its
explicit ``needs`` dependency graph. Additional GitLab concepts are added only
when a later feature needs them.
"""

from enum import Enum
from pathlib import Path
from typing import Any

from pydantic import BaseModel, Field


class SourceLocation(BaseModel):
    """Identifies the YAML file and logical YAML path behind a parsed value."""

    file_path: Path
    yaml_path: str


class LoadedYamlDocument(BaseModel):
    """The raw, parsed content of one YAML file."""

    source_file: Path
    content: dict[str, Any]


class JobDefinition(BaseModel):
    """A visible executable job in a GitLab CI pipeline."""

    id: str
    stage: str
    needs: list[str] = Field(default_factory=list)
    source_location: SourceLocation


class PipelineDefinition(BaseModel):
    """The supported GitLab CI concepts extracted from one configuration file."""

    source_file: Path
    stages: list[str]
    jobs: dict[str, JobDefinition]


class EdgeType(str, Enum):
    """The reason a dependency edge exists in the pipeline graph."""

    NEEDS = "needs"


class PipelineEdge(BaseModel):
    """A directed relationship from a prerequisite job to a dependent job."""

    source_job_id: str
    target_job_id: str
    edge_type: EdgeType
    source_location: SourceLocation


class PipelineGraph(BaseModel):
    """The explicit job-dependency graph used for rendering and later analysis."""

    nodes: dict[str, JobDefinition]
    edges: list[PipelineEdge]


class FindingSeverity(str, Enum):
    """Severity assigned by deterministic pipeline analysis."""

    INFO = "info"
    WARNING = "warning"
    ERROR = "error"


class PipelineFinding(BaseModel):
    """A deterministic observation that a model reviewer may explain or prioritize."""

    id: str
    severity: FindingSeverity
    title: str
    description: str
    evidence: list[SourceLocation] = Field(default_factory=list)
    recommended_action: str | None = None


class GraphAnalysisResult(BaseModel):
    """Deterministic structural facts calculated from a pipeline graph."""

    is_acyclic: bool
    execution_layers: list[list[str]] = Field(default_factory=list)
    root_job_ids: list[str] = Field(default_factory=list)
    terminal_job_ids: list[str] = Field(default_factory=list)
    cycle_job_ids: list[str] = Field(default_factory=list)
    findings: list[PipelineFinding] = Field(default_factory=list)


class VisualizationResult(BaseModel):
    """The complete deterministic output of the first visualization workflow."""

    pipeline: PipelineDefinition
    graph: PipelineGraph
    analysis: GraphAnalysisResult
    mermaid: str
    report_markdown: str
