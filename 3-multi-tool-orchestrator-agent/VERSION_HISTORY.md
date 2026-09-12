# Version History and Roadmap

This document separates what is implemented from planned work. Planned items
are targets, not completed functionality.

## 0.1.0 — V1 deterministic foundation (current)

### Included

- Safe local YAML loader using `yaml.safe_load`.
- Validation for missing files, YAML extensions, file size, malformed YAML,
  root mapping shape, stages, jobs, and simple `needs` syntax.
- GitLab CI parser for stages, visible jobs, job stage assignment, and simple
  `needs` job references.
- Canonical Pydantic models for parsed pipelines, graph nodes/edges, analysis
  findings, Mermaid output, and reports.
- Explicit dependency graph: prerequisite job -> dependent job.
- Deterministic graph analysis using Kahn's topological-sort algorithm.
- Parallel execution layers, root jobs, terminal jobs, and dependency-cycle
  findings.
- Mermaid flowchart source grouped by declared stage.
- Deterministic Markdown report generation.
- Vendor-neutral Pydantic input contract for a future OCI or other LLM review.
- Unit-test files and a small GitLab CI fixture.

### Deliberate boundaries

- No LLM/provider calls.
- No changes to submitted YAML or pipeline execution.
- No UI or generated-artifact persistence.
- No GitLab includes, child pipelines, cross-project dependencies, or advanced
  `needs` object syntax.

## 0.2.0 — Usable local CLI and richer deterministic analysis (planned)

- Implement a CLI accepting a YAML path and output directory.
- Persist report Markdown, Mermaid text, and canonical graph JSON under
  `artifacts/`.
- Add CLI exit codes and clear human-readable errors.
- Add downstream-impact queries and critical-path analysis.
- Add stronger test coverage, including malformed, cyclic, and larger graphs.

## 0.3.0 — Bounded model-assisted review (planned)

- Add a provider interface and OCI adapter behind it.
- Send only validated pipeline, graph, and deterministic findings—not raw YAML
  scripts or possible secrets by default.
- Request a small, structured set of evidence-linked recommendations.
- Validate model output against the canonical graph before displaying it.
- Add timeouts, retry limits, cost/token limits, and provider-independent tests.

## 0.4.0 — Broader GitLab CI support (planned)

- Resolve approved local `include` files.
- Represent child and cross-project pipeline references.
- Support additional safe GitLab concepts such as `extends` and selected
  `needs` object fields.
- Distinguish explicit `needs` dependencies from implicit stage ordering.

## 0.5.0 — Multi-platform parsing (planned)

- Add a parser registry/factory.
- Add GitHub Actions support as a separate platform parser.
- Reuse the same canonical graph, analyzer, report, and future model-review
  layers.
