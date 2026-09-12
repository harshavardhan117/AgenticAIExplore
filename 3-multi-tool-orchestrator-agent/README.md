# GitLab CI Pipeline Insight Assistant

Project 3 in the Agentic AI learning series: a deterministic multi-tool
orchestrator that turns a local GitLab CI YAML file into a dependency graph,
Mermaid diagram, and structural analysis report.

The project intentionally builds trustworthy automation before adding an LLM.
An optional OCI or other model-provider review layer will later explain and
prioritize deterministic findings; it will not be the source of pipeline facts.

## What works today

Given one local `.gitlab-ci.yml` or `.yaml` file, the implemented workflow:

1. Safely loads YAML with file-type, size, root-mapping, and syntax checks.
2. Parses the supported GitLab CI concepts: stages, visible jobs, `stage`, and
   simple string/list `needs` dependencies.
3. Builds a directed graph where jobs are nodes and `needs` relationships are
   prerequisite-to-dependent edges.
4. Uses Kahn's topological-sort algorithm to calculate execution layers and
   detect dependency cycles.
5. Produces Mermaid flowchart text and a deterministic Markdown report.

```text
GitLab CI YAML path
    -> YamlLoader
    -> GitLabPipelineParser
    -> PipelineGraphBuilder
    -> PipelineGraphAnalyzer
    -> MermaidRenderer + PipelineReportRenderer
    -> VisualizationResult
```

For example, this relationship:

```yaml
test_api:
  needs: [build_api, lint]
```

becomes:

```text
build_api -> test_api
lint      -> test_api
```

## Example output

For the included sample pipeline, the analyzer reports:

```text
Execution layer 1: build_api, lint
Execution layer 2: test_api
Execution layer 3: deploy_staging

Root jobs: build_api, lint
Terminal job: deploy_staging
Graph acyclic: yes
```

The report also includes Mermaid text that can be pasted into a Mermaid-aware
Markdown viewer.

## Project structure

```text
3-multi-tool-orchestrator-agent/
├── engine/
│   ├── yaml_loader.py          # Safe local YAML loading
│   ├── pipeline_parser.py      # GitLab YAML -> PipelineDefinition
│   ├── graph_builder.py        # PipelineDefinition -> PipelineGraph
│   ├── graph_analyzer.py       # Layers, endpoints, cycle findings
│   ├── mermaid_renderer.py     # PipelineGraph -> Mermaid source
│   ├── report_renderer.py      # Deterministic Markdown report
│   ├── orchestrator.py         # Fixed multi-tool workflow
│   └── models.py               # Shared Pydantic domain models
├── providers/
│   └── models.py               # Vendor-neutral future model-review input
├── tests/
│   └── fixtures/simple_pipeline.yml
├── artifacts/                  # Reserved for future generated output files
├── PRD.md                      # Original product requirements document
├── INITIAL_PROJECT_CONCEPT.md  # Original first project concept document
├── VERSION_HISTORY.md
└── pyproject.toml
```

## Setup

Requires Python 3.11+.

```bash
python -m pip install -e ".[dev]"
```

## Run the current workflow

The CLI entry point is intentionally not implemented yet. Run the orchestrator
directly while the learning-focused V1 is being assembled:

```bash
python -c "from pathlib import Path; from engine.orchestrator import PipelineVisualizationOrchestrator; result = PipelineVisualizationOrchestrator().visualize(Path('tests/fixtures/simple_pipeline.yml')); print(result.report_markdown)"
```

## Test

```bash
python -m pytest
```

## Current limitations

- Supports one local GitLab YAML file only.
- The graph represents explicit `needs` dependencies; implicit stage-order
  dependencies are not added as edges yet.
- `needs` objects, `include`, child pipelines, cross-project pipelines,
  `extends`, and GitLab `!reference` are intentionally deferred.
- No UI, persisted artifacts, CI execution, file modification, or OCI call yet.

## Roadmap

See [VERSION_HISTORY.md](VERSION_HISTORY.md) for the implemented V1 baseline
and planned versions.

## Documents

- [Product requirements document](PRD.md)
- [Original initial project concept](INITIAL_PROJECT_CONCEPT.md)
- [Version history and roadmap](VERSION_HISTORY.md)
