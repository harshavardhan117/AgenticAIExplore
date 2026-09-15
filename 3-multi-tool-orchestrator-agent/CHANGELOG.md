# Changelog

## 0.2.0 - 2026-09-15

### Added
- Tool-call observability: one shared run/trace ID per `orchestrator.run()` call
  (via `contextvars`, no manual threading through function signatures) plus a
  structured `tool=... status=... duration_ms=...` log line for every step.
  Plain functions (`yaml_loader`, `graph_builder`, `graph_analyzer`, `renderer`)
  use a function decorator (`observability.tool_logging.log_tool_call`); the two
  swappable ABC-based tools (`Parser`, `AIReviewer`) use a Decorator-pattern
  wrapper class instead (`LoggingParser`, `LoggingAIReviewer`), applied once at
  the registry/factory construction site.
- 2-minute timeout on the AI review call, set on both the Gemini and Claude
  clients, so a stuck network call can't hang a run indefinitely.

## 0.1.0 - GitLab CI pipeline reviewer rebuild

### Added
- Full deterministic pipeline: YAML loader -> parser (strategy pattern) ->
  graph builder -> Kahn's-algorithm analyzer -> Mermaid/Markdown renderer,
  wired by a thin service-layer orchestrator and a CLI entry point.
- Optional AI review step (Gemini live, Claude adapter, both behind a provider
  factory) that only explains/ranks findings the deterministic engine already
  found, never invents new ones, and falls back to deterministic-only output
  on any failure.
- 18 automated tests covering every layer, plus 8 hand-written sample
  pipelines (good and deliberately broken) for manual CLI verification.
