"""Deterministic structural analysis for explicit pipeline dependency graphs."""

from collections import deque

from engine.models import (
    FindingSeverity,
    GraphAnalysisResult,
    PipelineFinding,
    PipelineGraph,
    SourceLocation,
)


class PipelineGraphAnalyzer:
    """Calculates execution layers, endpoint jobs, and dependency cycles."""

    def analyze(self, graph: PipelineGraph) -> GraphAnalysisResult:
        """Analyze a graph using Kahn's topological-sort algorithm.

        Each emitted layer contains every currently runnable job. If jobs remain
        after the algorithm finishes, they participate in or are blocked by a
        directed cycle.
        """
        incoming_counts = {job_id: 0 for job_id in graph.nodes}
        downstream_jobs = {job_id: [] for job_id in graph.nodes}

        for edge in graph.edges:
            incoming_counts[edge.target_job_id] += 1
            downstream_jobs[edge.source_job_id].append(edge.target_job_id)

        root_job_ids = [
            job_id for job_id, count in incoming_counts.items() if count == 0
        ]
        terminal_job_ids = [
            job_id for job_id, downstream in downstream_jobs.items() if not downstream
        ]

        available_jobs = deque(root_job_ids)
        execution_layers: list[list[str]] = []
        processed_job_ids: set[str] = set()

        while available_jobs:
            layer = list(available_jobs)
            available_jobs.clear()
            execution_layers.append(layer)

            for job_id in layer:
                processed_job_ids.add(job_id)
                for downstream_job_id in downstream_jobs[job_id]:
                    incoming_counts[downstream_job_id] -= 1
                    if incoming_counts[downstream_job_id] == 0:
                        available_jobs.append(downstream_job_id)

        cycle_job_ids = [
            job_id for job_id in graph.nodes if job_id not in processed_job_ids
        ]
        findings = self._build_findings(graph, execution_layers, cycle_job_ids)

        return GraphAnalysisResult(
            is_acyclic=not cycle_job_ids,
            execution_layers=execution_layers,
            root_job_ids=root_job_ids,
            terminal_job_ids=terminal_job_ids,
            cycle_job_ids=cycle_job_ids,
            findings=findings,
        )

    @staticmethod
    def _build_findings(
        graph: PipelineGraph,
        execution_layers: list[list[str]],
        cycle_job_ids: list[str],
    ) -> list[PipelineFinding]:
        findings: list[PipelineFinding] = []

        for layer_index, layer in enumerate(execution_layers, start=1):
            if len(layer) > 1:
                findings.append(
                    PipelineFinding(
                        id=f"parallel-execution-layer-{layer_index}",
                        severity=FindingSeverity.INFO,
                        title="Parallel execution opportunity",
                        description=(
                            f"{len(layer)} jobs have no remaining prerequisites "
                            f"in execution layer {layer_index}: {', '.join(layer)}."
                        ),
                        evidence=[
                            graph.nodes[job_id].source_location for job_id in layer
                        ],
                    )
                )

        if cycle_job_ids:
            cycle_job_set = set(cycle_job_ids)
            evidence = [
                edge.source_location
                for edge in graph.edges
                if (
                    edge.source_job_id in cycle_job_set
                    and edge.target_job_id in cycle_job_set
                )
            ]
            findings.append(
                PipelineFinding(
                    id="dependency-cycle-detected",
                    severity=FindingSeverity.ERROR,
                    title="Dependency cycle detected",
                    description=(
                        "A valid execution order cannot be calculated because "
                        f"these jobs remain dependent: {', '.join(cycle_job_ids)}."
                    ),
                    evidence=evidence,
                    recommended_action=(
                        "Remove or redesign one or more needs relationships so "
                        "the dependency graph has no directed cycle."
                    ),
                )
            )

        return findings
