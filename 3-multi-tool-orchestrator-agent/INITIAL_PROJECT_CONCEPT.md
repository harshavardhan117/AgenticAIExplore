# Multi-Tool Orchestrator Agent

Project 3 in the Agentic AI learning series.

## Purpose

Build a backend-only assistant that chooses, authorizes, executes, and combines results from multiple tools safely.

Example request:

```text
Find the likely cause of this build failure and show related tickets,
code changes, and relevant runbook guidance.
```

The agent may use tools such as build-log search, ticket search, code-change search, and document search. It should return a single evidence-backed result, including partial results when some tools fail.

## Learning goals

This project is for learning and upskilling. We will understand and review each design decision before coding it, connect it to AI-system interviews, and build in small understandable steps.

By the end, you should be able to explain and use:

- tool contracts and capability registries
- tool adapters and provider boundaries
- deterministic intent classification and routing rules
- planning which tools to call
- sequential versus parallel tool execution
- dependency-aware execution
- permission scopes and safe tool execution
- timeouts, failures, partial results, and fallbacks
- result aggregation, conflict handling, and evidence preservation
- tool-call observability: trace ID, timing, status, and safe logs
- orchestration architecture, LLD, test strategy, and production trade-offs

## Functional requirements — V1

### 1. Request intake

- Accept one user request as plain text.
- Accept optional safe request context, such as repository name, build ID, or time range.
- Validate required fields and reject malformed input with a clear error response.

### 2. Tool contract

- Define one common tool interface for all tools.
- Every tool must declare its name, supported capability, required permission scope, input shape, and output shape.
- Every tool call must return a consistent result containing tool name, success/failure, data, and a safe error when applicable.

### 3. Initial tool set

V1 will use mock or local-safe implementations of 3–4 tools before connecting real external systems:

- build-log search
- ticket/incident search
- code-change or deployment-diff search
- runbook/document search

### 4. Capability registry

- Register available tools in one central but extensible registry.
- Resolve a requested capability to an authorized tool implementation.
- Make future tools additive: add an adapter and register it without changing core orchestration flow.

### 5. Deterministic planning and routing

- Start with explicit routing rules, not an LLM planner.
- Map request intent/keywords to the required tools.
- Produce a transparent execution plan showing selected tools and why they were selected.
- Introduce LLM-based planning only after the deterministic version is tested.

### 6. Tool execution

- Execute independent tools in parallel where safe.
- Execute dependent tools in the required order.
- Apply a timeout to every tool call.
- Continue with useful partial results when one non-critical tool fails.

### 7. Permission and safety controls

- Check a tool's permission scope before execution.
- V1 tools must be read-only.
- Reject unregistered tools and insufficient permissions.
- Do not allow a user prompt to select arbitrary Python functions, shell commands, or external URLs.

### 8. Result aggregation

- Merge successful results into one final response.
- Preserve the source tool for every important piece of evidence.
- Clearly show unavailable/failed tool results rather than silently hiding them.
- Identify conflicts between tool results and report them instead of inventing a resolution.

### 9. Observability and tests

- Add a trace ID for one orchestrated request.
- Log safe metadata for each tool call: tool name, status, duration, and trace ID.
- Do not log secrets, complete sensitive logs, raw tickets, or credentials.
- Add unit tests for registry, routing rules, permissions, timeouts, failures, parallel execution, and aggregation.
- Add integration tests using mock tools.

## Non-functional requirements

- Backend-only; no chatbot UI in V1.
- Tool implementations must remain replaceable through contracts/adapters.
- Keep external integrations mocked until a real work use case is approved.
- Make concurrency explicit and bounded; do not launch unlimited parallel tool calls.
- Return predictable structured response objects for success, partial success, denied execution, and failure.
- Keep credentials and environment-specific configuration outside Git.

## Learning workflow

We will follow this order:

1. Choose a real current-job use case.
2. Finalize requirements, tool scopes, and non-goals.
3. Draw high-level architecture and execution flows.
4. Design entities, contracts, tool registry, and low-level design.
5. Implement small components with explanation before code.
6. Test each component and then test orchestration with mock tools.
7. Validate an end-to-end example.
8. Document diagrams, decisions, interview notes, and release to GitHub.

## Decisions to make before architecture

- Which current-job workflow should this solve first: build failure investigation, test-failure investigation, incident triage, or another workflow?
- Which 3–4 tool capabilities are most useful for that workflow?
- What request context should be required or optional?
- Which tools may run in parallel, and which depend on earlier results?
- What permission scopes should V1 support?
- What should the final response look like: summary plus evidence, or a structured investigation report?

## Initial non-goals

- No write/update tools in V1: no ticket creation, code changes, or deployment actions.
- No arbitrary command execution.
- No LLM-driven autonomous planning loop in V1.
- No production Jira/Git/build/log integration until mock-tool behavior is tested.
- No multi-user authorization system in V1.

## Connection to Projects 1 and 2

- **Project 1 — Structured Output Agent:** can convert the final investigation into a Jira, email, or Confluence-ready payload.
- **Project 2 — RAG Agent with Citation Grounding:** can become the document/runbook search tool and provide grounded citations.

Together, these projects can later form a safe investigation workflow:

```text
Request
  → Multi-Tool Orchestrator
  → build/ticket/code/document evidence
  → grounded investigation summary
  → Structured Output Agent
  → Jira or Confluence payload
```
