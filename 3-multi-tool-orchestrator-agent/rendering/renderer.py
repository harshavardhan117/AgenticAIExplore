"""Renders a PipelineGraph + AnalysisResult into a Mermaid diagram and a Markdown report."""

from domain.models import AnalysisResult, Finding, PipelineDefinition, PipelineGraph


def render(
    pipeline: PipelineDefinition,
    graph: PipelineGraph,
    analysis: AnalysisResult,
    findings: list[Finding],
) -> tuple[str, str]:
    """`findings` is whatever the caller wants shown — renderer doesn't care where they came from."""
    mermaid = _render_mermaid(pipeline, graph)
    report_markdown = _render_report(pipeline, graph, analysis, findings)
    return mermaid, report_markdown


def _render_mermaid(pipeline: PipelineDefinition, graph: PipelineGraph) -> str:
    lines = ["flowchart TD"]

    for stage in pipeline.stages:
        job_ids = [job_id for job_id, job in graph.nodes.items() if job.stage == stage]
        if not job_ids:
            continue
        lines.append(f'    subgraph {stage}')
        for job_id in job_ids:
            lines.append(f"        {job_id}")
        lines.append("    end")

    for edge in graph.edges:
        lines.append(f"    {edge.source_job_id} --> {edge.target_job_id}")

    return "\n".join(lines)


def _render_report(
    pipeline: PipelineDefinition,
    graph: PipelineGraph,
    analysis: AnalysisResult,
    findings: list[Finding],
) -> str:
    lines = [
        f"# Pipeline report: {pipeline.source_file.name}",
        "",
        f"- Stages: {len(pipeline.stages)}",
        f"- Jobs: {len(pipeline.jobs)}",
        f"- Acyclic: {'yes' if analysis.is_acyclic else 'no'}",
        f"- Root jobs: {', '.join(analysis.root_job_ids) or 'none'}",
        f"- Terminal jobs: {', '.join(analysis.terminal_job_ids) or 'none'}",
        "",
        "## Execution layers",
        "",
    ]

    for index, layer in enumerate(analysis.execution_layers, start=1):
        lines.append(f"{index}. {', '.join(layer)}")

    lines += ["", "## Findings", ""]

    if not findings:
        lines.append("No findings.")
    else:
        for finding in findings:
            lines.append(f"- **[{finding.severity.value.upper()}] {finding.title}** - {finding.description}")

    return "\n".join(lines)
