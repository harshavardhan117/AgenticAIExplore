"""Top-level deterministic visualization workflow contract."""

from pathlib import Path

from engine.models import LoadedYamlDocument, VisualizationResult
from engine.graph_analyzer import PipelineGraphAnalyzer
from engine.graph_builder import PipelineGraphBuilder
from engine.mermaid_renderer import MermaidRenderer
from engine.pipeline_parser import GitLabPipelineParser
from engine.report_renderer import PipelineReportRenderer
from engine.yaml_loader import YamlLoader


class PipelineVisualizationOrchestrator:
    """Coordinates loading, parsing, graph building, and Mermaid rendering."""

    def __init__(
        self,
        yaml_loader: YamlLoader | None = None,
        pipeline_parser: GitLabPipelineParser | None = None,
        graph_builder: PipelineGraphBuilder | None = None,
        graph_analyzer: PipelineGraphAnalyzer | None = None,
        mermaid_renderer: MermaidRenderer | None = None,
        report_renderer: PipelineReportRenderer | None = None,
    ) -> None:
        self._yaml_loader = yaml_loader or YamlLoader()
        self._pipeline_parser = pipeline_parser or GitLabPipelineParser()
        self._graph_builder = graph_builder or PipelineGraphBuilder()
        self._graph_analyzer = graph_analyzer or PipelineGraphAnalyzer()
        self._mermaid_renderer = mermaid_renderer or MermaidRenderer()
        self._report_renderer = report_renderer or PipelineReportRenderer()

    def visualize(self, yaml_path: Path) -> VisualizationResult:
        """Create one visualization result from a local GitLab CI YAML file."""
        document = self._load_document(yaml_path)
        pipeline = self._pipeline_parser.parse(document)
        graph = self._graph_builder.build(pipeline)
        analysis = self._graph_analyzer.analyze(graph)
        mermaid = self._mermaid_renderer.render(pipeline, graph)
        report_markdown = self._report_renderer.render(
            pipeline,
            graph,
            analysis,
            mermaid,
        )

        return VisualizationResult(
            pipeline=pipeline,
            graph=graph,
            analysis=analysis,
            mermaid=mermaid,
            report_markdown=report_markdown,
        )

    def _load_document(self, yaml_path: Path) -> LoadedYamlDocument:
        """Load the pipeline configuration before later workflow steps process it."""
        return self._yaml_loader.load(yaml_path)
