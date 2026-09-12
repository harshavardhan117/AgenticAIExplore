"""Generate a deterministic Markdown report from pipeline analysis results."""

from engine.models import GraphAnalysisResult, PipelineDefinition, PipelineGraph


class PipelineReportRenderer:
    """Renders shareable Markdown without making model-based recommendations."""

    def render(
        self,
        pipeline: PipelineDefinition,
        graph: PipelineGraph,
        analysis: GraphAnalysisResult,
        mermaid: str,
    ) -> str:
        """Return a deterministic report for one analyzed pipeline."""
        lines = [
            "# GitLab CI Pipeline Report",
            "",
            "## Summary",
            "",
            f"- Source: `{pipeline.source_file.name}`",
            f"- Visible jobs: {len(pipeline.jobs)}",
            f"- Declared stages: {len(pipeline.stages)}",
            f"- Explicit `needs` relationships: {len(graph.edges)}",
            f"- Dependency graph acyclic: {'Yes' if analysis.is_acyclic else 'No'}",
            "",
            "## Execution Plan",
            "",
        ]

        if analysis.execution_layers:
            for index, layer in enumerate(analysis.execution_layers, start=1):
                lines.append(f"{index}. **Layer {index}:** {self._format_job_ids(layer)}")
        else:
            lines.append("No valid execution layers can be calculated.")

        lines.extend(
            [
                "",
                "## Pipeline Endpoints",
                "",
                f"- Root jobs: {self._format_job_ids(analysis.root_job_ids)}",
                f"- Terminal jobs: {self._format_job_ids(analysis.terminal_job_ids)}",
                "",
                "## Findings",
                "",
            ]
        )

        if not analysis.findings:
            lines.append("No deterministic findings were produced.")
        else:
            for finding in analysis.findings:
                lines.append(
                    f"- [{finding.severity.value.upper()}] "
                    f"**{finding.title}** — {finding.description}"
                )
                if finding.recommended_action:
                    lines.append(f"  - Recommended action: {finding.recommended_action}")

        lines.extend(
            [
                "",
                "## Mermaid Diagram",
                "",
                "```mermaid",
                mermaid.rstrip(),
                "```",
                "",
            ]
        )
        return "\n".join(lines)

    @staticmethod
    def _format_job_ids(job_ids: list[str]) -> str:
        if not job_ids:
            return "None"

        return ", ".join(f"`{job_id}`" for job_id in job_ids)
