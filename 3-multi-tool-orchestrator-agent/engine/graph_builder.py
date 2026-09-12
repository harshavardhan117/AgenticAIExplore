"""Build the explicit GitLab CI job-dependency graph."""

from engine.models import EdgeType, PipelineDefinition, PipelineEdge, PipelineGraph
from engine.models import SourceLocation


class GraphBuildError(Exception):
    """Raised when a pipeline definition cannot produce a valid graph."""


class PipelineGraphBuilder:
    """Builds explicit job dependency nodes and edges from a pipeline definition."""

    def build(self, pipeline: PipelineDefinition) -> PipelineGraph:
        """Create the pipeline's explicit execution-dependency graph."""
        nodes = pipeline.jobs.copy()
        edges: list[PipelineEdge] = []

        for job in nodes.values():
            seen_dependencies: set[str] = set()

            for prerequisite_job_id in job.needs:
                if prerequisite_job_id not in nodes:
                    raise GraphBuildError(
                        f"Job '{job.id}' needs missing job '{prerequisite_job_id}'"
                    )

                if prerequisite_job_id in seen_dependencies:
                    raise GraphBuildError(
                        f"Job '{job.id}' lists duplicate need '{prerequisite_job_id}'"
                    )

                seen_dependencies.add(prerequisite_job_id)
                edges.append(
                    PipelineEdge(
                        source_job_id=prerequisite_job_id,
                        target_job_id=job.id,
                        edge_type=EdgeType.NEEDS,
                        source_location=SourceLocation(
                            file_path=job.source_location.file_path,
                            yaml_path=f"{job.id}.needs",
                        ),
                    )
                )

        return PipelineGraph(nodes=nodes, edges=edges)
