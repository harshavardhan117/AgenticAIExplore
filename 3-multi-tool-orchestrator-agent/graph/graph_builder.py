"""Builds a PipelineGraph (nodes + dependency edges) from a parsed PipelineDefinition."""

from domain.models import Edge, Finding, FindingSeverity, PipelineDefinition, PipelineGraph
from observability.tool_logging import log_tool_call


@log_tool_call
def build_graph(pipeline: PipelineDefinition) -> tuple[PipelineGraph, list[Finding]]:
    edges: list[Edge] = []
    findings: list[Finding] = []

    for job_id, job in pipeline.jobs.items():
        for dep in job.needs:
            if dep not in pipeline.jobs:
                findings.append(
                    Finding(
                        id=f"dangling-needs-{job_id}-{dep}",
                        severity=FindingSeverity.ERROR,
                        title="Dangling needs reference",
                        description=f"Job '{job_id}' needs unknown job '{dep}'.",
                        evidence=[job.source_location],
                    )
                )
                continue
            edges.append(Edge(source_job_id=dep, target_job_id=job_id))

    graph = PipelineGraph(nodes=pipeline.jobs, edges=edges)
    return graph, findings
