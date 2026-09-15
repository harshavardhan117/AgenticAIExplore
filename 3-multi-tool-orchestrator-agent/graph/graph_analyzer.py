"""Analyzes a PipelineGraph: cycle detection + topological execution layers via Kahn's algorithm."""

from domain.models import AnalysisResult, Finding, FindingSeverity, PipelineGraph
from observability.tool_logging import log_tool_call


@log_tool_call
def analyze_graph(graph: PipelineGraph) -> AnalysisResult:
    adjacency: dict[str, list[str]] = {job_id: [] for job_id in graph.nodes}
    in_degree: dict[str, int] = {job_id: 0 for job_id in graph.nodes}
    for edge in graph.edges:
        adjacency[edge.source_job_id].append(edge.target_job_id)
        in_degree[edge.target_job_id] += 1

    root_job_ids = sorted(job_id for job_id, degree in in_degree.items() if degree == 0)
    terminal_job_ids = sorted(job_id for job_id in graph.nodes if not adjacency[job_id])

    remaining_in_degree = dict(in_degree)
    execution_layers: list[list[str]] = []
    current_layer = list(root_job_ids)
    processed = 0

    while current_layer:
        execution_layers.append(current_layer)
        next_layer: list[str] = []
        for job_id in current_layer:
            processed += 1
            for target in adjacency[job_id]:
                remaining_in_degree[target] -= 1
                if remaining_in_degree[target] == 0:
                    next_layer.append(target)
        current_layer = sorted(next_layer)

    is_acyclic = processed == len(graph.nodes)

    findings: list[Finding] = []
    if not is_acyclic:
        cyclic_job_ids = sorted(job_id for job_id, degree in remaining_in_degree.items() if degree > 0)
        findings.append(
            Finding(
                id="cycle-detected",
                severity=FindingSeverity.ERROR,
                title="Dependency cycle detected",
                description=f"These jobs form a cycle (or depend on one): {', '.join(cyclic_job_ids)}",
                evidence=[graph.nodes[job_id].source_location for job_id in cyclic_job_ids],
            )
        )

    return AnalysisResult(
        is_acyclic=is_acyclic,
        execution_layers=execution_layers,
        root_job_ids=root_job_ids,
        terminal_job_ids=terminal_job_ids,
        findings=findings,
    )
