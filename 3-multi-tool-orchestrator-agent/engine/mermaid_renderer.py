"""Generate Mermaid flowchart text from a parsed pipeline graph."""

from html import escape

from engine.models import PipelineDefinition, PipelineGraph


class MermaidRenderer:
    """Renders a pipeline definition and dependency graph as Mermaid text."""

    def render(self, pipeline: PipelineDefinition, graph: PipelineGraph) -> str:
        """Return a Mermaid flowchart for the supplied pipeline graph."""
        job_aliases = {
            job_id: f"job_{index}"
            for index, job_id in enumerate(pipeline.jobs)
        }
        lines = ["flowchart LR"]

        for stage_index, stage in enumerate(pipeline.stages):
            stage_jobs = [job for job in pipeline.jobs.values() if job.stage == stage]
            if not stage_jobs:
                continue

            lines.append(f'    subgraph stage_{stage_index}["{self._escape_label(stage)}"]')
            for job in stage_jobs:
                lines.append(
                    f'        {job_aliases[job.id]}["{self._escape_label(job.id)}"]'
                )
            lines.append("    end")

        if graph.edges:
            lines.append("")

        for edge in graph.edges:
            lines.append(
                f"    {job_aliases[edge.source_job_id]} --> "
                f"{job_aliases[edge.target_job_id]}"
            )

        return "\n".join(lines) + "\n"

    @staticmethod
    def _escape_label(value: str) -> str:
        return escape(value, quote=True).replace("\n", " ")
