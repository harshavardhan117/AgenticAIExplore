# Multi-Tool Orchestrator Agent — GitLab CI Pipeline Reviewer

Project 3 in the Agentic AI learning series. Analyzes a local GitLab CI YAML
file: parses jobs and dependencies, builds a dependency graph, detects
cycles, computes parallel execution layers, and renders a Mermaid diagram +
Markdown report. An optional AI step explains and prioritizes the findings.

## Architecture

Straight-line pipeline, each stage independent and swappable:

```text
YAML file
  -> tools.yaml_loader        load + validate YAML shape
  -> parsers.registry         pick the right parser strategy (can_parse)
  -> parsers.gitlab           GitLab CI -> PipelineDefinition
  -> graph.graph_builder      PipelineDefinition -> PipelineGraph
                               (dangling `needs` -> Finding, not a crash)
  -> graph.graph_analyzer     Kahn's algorithm -> cycles + execution layers
  -> rendering.renderer       -> Mermaid diagram + Markdown report
  -> ai.factory (optional)    -> AI explains/ranks findings, never invents new ones
```

`orchestrator.run()` is the service layer — it only calls the above in order
and assembles the result; it owns no logic itself. `main.py` is a thin CLI
wrapper over the orchestrator.

## Project layout

```text
domain/models.py     Every entity: JobDefinition, PipelineGraph, Finding,
                      AnalysisResult, AIReviewInput/Output, PipelineReport
tools/                General-purpose tools (yaml_loader today)
parsers/              Parser strategy interface (ABC) + GitLabParser + registry
graph/                Graph builder + analyzer (plain functions, no
                      interface needed — only one implementation of each)
rendering/            Mermaid + Markdown report renderer
ai/                   AIReviewer interface (ABC) + Gemini/Claude adapters +
                      factory (env-driven provider choice) + shared prompt
orchestrator.py       Service layer wiring everything together
main.py               CLI entry point
samples/              Hand-written example pipelines, good and bad, for
                      manually exercising the CLI end to end
tests/                Mirrors the folder structure above 1:1
```

## Design decisions worth remembering

- **`Parser` and `AIReviewer` are ABCs** (multiple interchangeable
  implementations exist or are planned: GitLab/GitHub, Gemini/Claude).
  `graph_builder`/`graph_analyzer` are plain functions — only one algorithm
  each, an interface would be over-engineering (YAGNI).
- **Checkers were dropped.** Validation that would've been a separate
  "checker" tool (e.g. dangling `needs` references) is handled directly by
  `graph_builder`: it skips the bad edge and returns a `Finding` instead of
  raising. Parser failures (can't even build a `PipelineDefinition`) are
  still fatal — they raise.
- **Findings have two sources, kept separate in the data model**
  (`validation_findings` from the graph builder vs. `analysis.findings` from
  cycle detection) but **merged before rendering or sending to AI** — the
  renderer and the AI prompt don't care where a finding came from.
- **AI is additive, never authoritative.** It only explains, ranks, and
  estimates productivity impact for findings the deterministic engine
  already produced — it cannot introduce new structural claims. It never
  sees raw YAML/script content, only structured facts (`AIReviewInput`).
- **AI failure never fails the request.** `chat()` raises on any problem
  (auth, network, bad response); the orchestrator catches it and returns
  the deterministic report anyway, with `ai_error` set.
- **Provider choice is a factory + env var** (`AI_PROVIDER=gemini|claude`,
  defaults to Gemini), same registration-in-one-place pattern as the parser
  registry.

## Setup

```bash
python -m venv .venv
.venv/Scripts/python.exe -m pip install "pydantic>=2.0" "PyYAML>=6.0" "python-dotenv>=1.0" "google-genai>=1.0" "anthropic>=0.40" "pytest>=8.0"
```

Copy `.env.example` to `.env` and fill in whichever provider's API key you
have. `.env` is gitignored — never commit it.

## Run

```bash
python main.py samples/03_medium_parallel.yml
python main.py samples/03_medium_parallel.yml --ai
```

## Test

```bash
python -m pytest -q
```

18 tests across parsers, graph building/analysis, rendering, the AI
prompt/parsing round trip, the provider factory, and the full orchestrator
flow (including a dangling-`needs` end-to-end case).

## Samples

`samples/` has 8 hand-written pipelines for manually exercising the CLI:
`01`-`04` go from a single job to an 18-job/6-stage pipeline (all should
produce a clean report); `05`-`08` are deliberately broken (a cycle, a
dangling `needs`, a non-mapping YAML file, and an unrecognized format) to
exercise every error path — two degrade gracefully into a `Finding`, two
are hard failures with a clean CLI error message and exit code 1.

## Current limitations

- GitLab CI only (GitHub Actions parser not built — strategy pattern makes
  this additive later).
- Single local YAML file only — no `include` resolution, no folder/multi-file
  input yet.
- `needs` (explicit dependency) is the only relationship modeled — no
  artifact relationships or stage-order-only waits yet.
- No historical/duration data — execution layers are structural only, not a
  real timing estimate.
