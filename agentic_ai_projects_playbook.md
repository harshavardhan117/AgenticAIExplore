# Agentic AI Projects Playbook

A practical markdown guide for building the 12 agentic AI projects one by one with Codex while learning the concepts in a systematic, system-design-first way.

## How to use this guide

For each project:

1. Read the concept and the problem it solves.
2. Write a 1-page design note before coding.
3. Build a narrow MVP first.
4. Add failure handling, tests, and evaluation.
5. Keep a README with architecture, trade-offs, and what failed.
6. Move to the next project only after you can explain the previous one clearly.

The goal is not to build 12 giant applications. The goal is to build 12 controlled experiments that teach one important agentic pattern each.

---

# Recommended learning order

1. Structured Output Agent
2. RAG Agent with Citation Grounding
3. Multi-Tool Orchestrator Agent
4. ReAct Planning Agent
5. Human-in-the-Loop Approval Agent
6. Memory-Enabled Conversational Agent
7. Cost-Aware Agent Router
8. Event-Triggered Automation Agent
9. Multi-Agent Debate System
10. Self-Reflective Agent with Auto-Eval
11. Production Agent with Observability
12. Open Source Agent Framework Contribution

---

# Standard project template

Use this same structure for every repo:

```text
project-name/
├── README.md
├── docs/
│   ├── requirements.md
│   ├── architecture.md
│   ├── decisions.md
│   └── evaluation.md
├── src/
│   ├── api/
│   ├── agents/
│   ├── tools/
│   ├── models/
│   └── services/
├── tests/
│   ├── unit/
│   ├── integration/
│   └── evaluation/
├── datasets/
├── scripts/
├── docker-compose.yml
└── pyproject.toml
```

For each project, answer the same questions in `architecture.md`:

- What problem does it solve?
- Who uses it?
- What is in scope and out of scope?
- What are the main failure modes?
- What are the latency and reliability targets?
- What is the minimum architecture that works?
- How will you test it?
- What do you measure?
- What will the human review?

---

# 1) Structured Output Agent

## Goal

Build an incident/ticket classifier that returns validated structured output instead of free-form text.

## What it teaches

- Pydantic schema design
- JSON validation
- parse retries
- fallback behavior
- application reliability with LLMs

## Example user story

A developer pastes an incident summary:

> Checkout API started returning 500s after deployment.

The agent returns a structured response:

```json
{
  "category": "deployment_failure",
  "severity": "high",
  "service": "checkout-api",
  "confidence": 0.93,
  "recommended_team": "commerce-platform"
}
```

## MVP scope

- One input text field
- One LLM call
- One Pydantic schema
- Retry up to 2 times on invalid output
- Fallback to `unknown` when confidence is low
- Log validation failures

## Suggested architecture

```text
User Input
  -> Prompt Builder
  -> LLM
  -> JSON Parser
  -> Pydantic Validator
  -> Retry / Fallback
  -> Structured Response
```

## Sample schema

```python
class IncidentClassification(BaseModel):
    category: Literal["deployment_failure", "infra_issue", "test_failure", "bug", "unknown"]
    severity: Literal["low", "medium", "high", "critical"]
    service: str
    confidence: float = Field(ge=0.0, le=1.0)
    recommended_team: str
    notes: list[str] = []
```

## Sample test cases

- Valid JSON with all fields
- Valid JSON but wrong enum
- Missing required field
- Truncated JSON
- Low-confidence output
- Empty output

## Codex build plan

Ask Codex to implement in this order:

1. Pydantic model
2. LLM wrapper
3. Validation layer
4. Retry logic
5. Logging
6. Unit tests
7. Simple CLI demo

## System design questions to answer

- Where does schema validation happen?
- How many retries are allowed?
- What is the fallback behavior?
- How do you version the schema?
- How do you distinguish model failure from app failure?

## What to write in the README

- Why free-form LLM output is not reliable enough
- Why structured output matters
- Validation strategy
- Example failures
- Example outputs

---

# 2) RAG Agent with Citation Grounding

## Goal

Build a runbook/document Q&A assistant that answers with citations and abstains when evidence is weak.

## What it teaches

- ingestion
- chunking
- embeddings
- retrieval
- reranking
- citation grounding
- hallucination control

## Example user story

> How do I handle high database connection usage?

The agent answers:

> Check the connection pool configuration first. If the value is below the runbook threshold, increase it and verify the DB wait metrics.
> Sources: Runbook v2, Section 4.2; Incident postmortem INC-418.

## MVP scope

- 5–10 markdown documents
- basic chunking
- vector search
- top-k retrieval
- source citations in the answer
- low-confidence abstention

## Suggested architecture

```text
Documents -> Chunker -> Embedding Index -> Retriever -> Context Builder
                                              -> LLM Answer Generator
                                              -> Citation Formatter
```

## Sample inputs

- “What do we do when CPU spikes after deploy?”
- “Where is the rollback process documented?”
- “How do we restart the payment worker safely?”
- “What is the DB failover procedure?”

## Sample output format

```json
{
  "answer": "Increase the pool size and verify the wait queue.",
  "citations": [
    {
      "doc": "db-runbook.md",
      "chunk_id": "chunk-07",
      "quote": "If wait queue exceeds threshold, increase pool size..."
    }
  ],
  "confidence": 0.88,
  "abstained": false
}
```

## Evaluation dataset

Create 30 questions:
- 15 answerable
- 5 partially answerable
- 5 unanswerable
- 5 misleading

Track:
- retrieval accuracy
- citation correctness
- groundedness
- abstention quality

## Codex build plan

1. Document loader
2. Chunking utility
3. Embedding + vector index
4. Retriever
5. Answer generator with citations
6. Confidence / abstention logic
7. Evaluation script
8. README with examples

## System design questions to answer

- How large should chunks be?
- How do you preserve metadata?
- What happens when sources conflict?
- How do you know the answer is grounded?
- When should the agent say “I don’t know”?

---

# 3) Multi-Tool Orchestrator Agent

## Goal

Build an assistant that can use multiple tools intelligently and safely.

## What it teaches

- tool registry
- tool contracts
- permission scopes
- parallel tool calls
- conflict resolution
- orchestration

## Example user story

> Find the likely cause of this build failure and show related tickets and code changes.

Tools:
- Git search
- Jira search
- docs search
- build log search

## MVP scope

- 3–4 tools
- static capability registry
- deterministic routing rules at first
- basic parallel execution
- merged response with evidence

## Suggested architecture

```text
User Request
 -> Intent Classifier
 -> Tool Planner
 -> Tool Registry
 -> Tool Executor
 -> Result Aggregator
 -> Final Response
```

## Sample tool contract

```python
class ToolResult(BaseModel):
    tool_name: str
    success: bool
    data: dict
    error: str | None = None
```

## Sample tasks

- Search Jira for similar incidents
- Fetch the latest deployment diff
- Query logs around a timestamp
- Retrieve the release note for a build

## Codex build plan

1. Define tool interface
2. Implement mock tools
3. Add routing rules
4. Add parallel tool execution
5. Add permission checks
6. Add aggregation
7. Add integration tests

## System design questions to answer

- Which tools can run in parallel?
- Which tools depend on each other?
- How do you handle tool failure?
- How do you prevent unsafe tool execution?
- How do you log every tool call?

---

# 4) ReAct Planning Agent

## Goal

Build an agent that thinks in steps, chooses tools iteratively, and stops safely.

## What it teaches

- planning
- observation-action loops
- iteration limits
- self-critique
- graceful degradation

## Example user story

> Investigate why payment-service started failing after deployment.

The agent should:
1. inspect the deployment
2. check logs
3. search similar incidents
4. form a hypothesis
5. stop when enough evidence exists

## MVP scope

- 1 planning loop
- 2–3 tools
- max iteration count
- loop detection
- partial answer when incomplete

## Suggested architecture

```text
Observe -> Think -> Act -> Observe -> Think -> Act -> Finalize
```

## Sample state object

```json
{
  "goal": "Investigate payment-service failure",
  "steps_taken": ["checked deployment", "queried logs"],
  "hypotheses": ["config change", "DB timeout"],
  "remaining_budget": 3,
  "done": false
}
```

## Codex build plan

1. State model
2. Tool adapters
3. Loop controller
4. Step logging
5. Termination rules
6. Self-critique output
7. Demo script
8. Tests for loop prevention

## System design questions to answer

- When should the agent stop?
- What is a safe max iteration count?
- How do you detect repeated tool use?
- When should the agent ask for more context?
- What counts as “enough evidence”?

---

# 5) Human-in-the-Loop Approval Agent

## Goal

Build a workflow that pauses before risky actions and resumes after approval.

## What it teaches

- approval gates
- durable workflow state
- pause/resume
- auditability
- safe automation

## Example user story

> The agent found a likely fix. Draft the code change, but don’t apply it until I approve.

## MVP scope

- one approval gate
- one risky action
- CLI or simple web UI for approve/reject
- checkpointing
- audit log

## Suggested workflow

```text
Investigate -> Propose Fix -> Wait for Approval -> Execute Fix -> Verify
```

## Sample approval object

```json
{
  "action": "apply_patch",
  "risk": "medium",
  "reason": "Fixes timeout by restoring previous retry settings",
  "requires_human_approval": true
}
```

## Codex build plan

1. State machine
2. Approval schema
3. Persistence layer
4. Resume logic
5. Audit trail
6. CLI or minimal web UI
7. Tests for reject/resume paths

## System design questions to answer

- Which actions require approval?
- What if approval never comes?
- How do you resume after restart?
- What metadata should the approver see?
- How do you prevent accidental execution?

---

# 6) Memory-Enabled Conversational Agent

## Goal

Build an assistant that remembers useful long-term context across sessions.

## What it teaches

- short-term vs long-term memory
- memory relevance
- summarization
- privacy boundaries
- memory lifecycle

## Example user story

Session 1:

> I work on payment-service in Java and Spring Boot.

Session 2:

> Continue investigating the timeout issue.

The agent recalls the service, stack, and relevant prior issue context.

## MVP scope

- save project preferences
- store session summary
- recall top relevant memories
- allow memory deletion
- ignore irrelevant details

## Suggested memory classes

- session memory
- project memory
- preference memory
- sensitive memory
- expired memory

## Codex build plan

1. Memory schema
2. Memory extraction
3. Vector store or key-value store
4. Relevance scoring
5. Recall logic
6. Delete/edit flow
7. Tests for stale/irrelevant memory

## System design questions to answer

- What should be remembered?
- What should never be remembered?
- How do you expire old memory?
- How do you prevent memory pollution?
- How does memory affect prompting?

---

# 7) Cost-Aware Agent Router

## Goal

Build a service that chooses the right model for the task based on cost, latency, and complexity.

## What it teaches

- model routing
- token budgeting
- trade-offs
- cost analytics
- fallback logic

## Example user story

- classify ticket -> small model
- summarize logs -> medium model
- generate RCA -> larger model
- validate schema -> small model

## MVP scope

- 2–3 model options
- simple routing policy
- cost estimation
- latency tracking
- confidence-based fallback

## Suggested architecture

```text
Task -> Complexity Classifier -> Router -> Model A / Model B / Model C -> Result
```

## Sample routing rule

```python
if task_type == "classification":
    use = "small-model"
elif token_count > 5000:
    use = "large-model"
else:
    use = "medium-model"
```

## Codex build plan

1. Task classifier
2. Model registry
3. Cost calculator
4. Routing policy
5. Fallback strategy
6. Metrics collection
7. Evaluation script

## System design questions to answer

- What signals drive routing?
- How do you measure whether routing helps?
- When should you override the router?
- What is the fallback if a model fails?
- How do you compare cost vs quality?

---

# 8) Event-Triggered Automation Agent

## Goal

Build a webhook-driven agent that reacts to system events and processes them reliably.

## What it teaches

- event-driven architecture
- queues
- retries
- idempotency
- dead-letter queues
- asynchronous workflows

## Example user story

> Jenkins build failed.

The agent receives the event, deduplicates it, queues it, investigates the failure, and posts a summary.

## MVP scope

- webhook endpoint
- event validation
- queue
- worker
- retry policy
- dead-letter handling
- replay support

## Suggested architecture

```text
Webhook -> Validation -> Queue -> Worker -> Investigation -> Result Store
```

## Sample event schema

```json
{
  "event_id": "evt_123",
  "event_type": "build_failed",
  "source": "jenkins",
  "repository": "payments-api",
  "timestamp": "2026-08-01T10:15:00Z"
}
```

## Codex build plan

1. Webhook handler
2. Event schema
3. Queue worker
4. Retry logic
5. Idempotency store
6. Dead-letter queue
7. Replay endpoint
8. Integration tests

## System design questions to answer

- How do you deduplicate events?
- What happens if the worker crashes?
- How many retries are allowed?
- When do messages go to the dead-letter queue?
- How do you replay safely?

---

# 9) Multi-Agent Debate System

## Goal

Build a system where several specialized agents review a problem from different angles before producing a final answer.

## What it teaches

- multi-agent orchestration
- specialization
- debate and critique
- aggregation
- confidence synthesis

## Example user story

> Review this architecture for a high-volume notification service.

Agents:
- scalability reviewer
- security reviewer
- reliability reviewer
- cost reviewer
- critic
- judge

## MVP scope

- 3 specialist agents
- 1 critic agent
- 1 aggregator
- one final synthesis

## Suggested flow

```text
Proposal -> Specialist Opinions -> Critique -> Judge -> Final Response
```

## Codex build plan

1. Agent roles
2. Prompt templates per role
3. Debate rounds
4. Judge/aggregator
5. Stop conditions
6. Confidence scoring
7. Comparison tests vs single-agent baseline

## System design questions to answer

- When is debate useful?
- How do you keep agents from echoing each other?
- How many rounds are enough?
- Should they see each other’s outputs?
- How do you avoid cost explosion?

---

# 10) Self-Reflective Agent with Auto-Eval

## Goal

Build an agent that critiques and improves its own answer using an evaluation rubric.

## What it teaches

- LLM-as-judge
- rubric design
- revision loops
- stopping criteria
- deterministic checks

## Example user story

> Generate an RCA report, evaluate it, and revise it if needed.

## MVP scope

- answer generation
- rubric evaluation
- critique output
- one revision pass
- deterministic checks like required sections and citations

## Suggested rubric

- evidence quality
- root cause clarity
- actionability
- timeline completeness
- citation support
- confidence calibration

## Codex build plan

1. Generator
2. Evaluation rubric
3. Judge prompt
4. Revision prompt
5. Stop conditions
6. Metrics recording
7. Regression tests

## System design questions to answer

- Can the model judge itself reliably?
- What deterministic checks should be added?
- How do you prevent endless revisions?
- What makes an evaluation valid?
- How do you compare before and after scores?

---

# 11) Production Agent with Observability

## Goal

Take one earlier project and make it production-like with logs, traces, metrics, and rollout safety.

## What it teaches

- observability
- release engineering
- AI system monitoring
- alerts
- canary releases
- rollback strategy

## Best candidate

Use the RAG or incident investigation project.

## MVP scope

- structured logging
- metrics endpoint
- trace IDs
- latency dashboard
- error rate tracking
- prompt/model versioning
- canary release
- rollback plan

## Suggested metrics

- request latency
- model latency
- tool latency
- token count
- retry count
- invalid response rate
- tool failure rate
- loop count
- success rate

## Codex build plan

1. Add structured logging
2. Add trace IDs
3. Add metrics collection
4. Add dashboard export
5. Add alert thresholds
6. Add version tracking
7. Add CI evaluation
8. Add rollback demo

## System design questions to answer

- What should be observable?
- What alerts matter?
- What is an SLO for an agent?
- How do you catch regressions?
- How do you roll back safely?

---

# 12) Open Source Contribution

## Goal

Extract one reusable agent component and contribute it to an open source framework or publish it as a package.

## What it teaches

- framework internals
- contribution workflow
- documentation
- compatibility
- tests and review

## Good contribution ideas

- retry middleware for structured output
- citation validator
- memory relevance scorer
- approval checkpoint utility
- loop detector
- model routing policy

## Codex build plan

1. Pick a reusable component
2. Find a real issue or gap
3. Reproduce the behavior
4. Implement the fix or feature
5. Add tests
6. Write docs
7. Create example usage
8. Submit PR and iterate

## System design questions to answer

- What problem does the component solve?
- What are the extension points?
- What are compatibility risks?
- How do tests prove it works?
- Why is it reusable?

---

# Suggested repo checklist for every project

## Must-have files

- `README.md`
- `docs/requirements.md`
- `docs/architecture.md`
- `docs/decisions.md`
- `docs/evaluation.md`
- `tests/`
- `docker-compose.yml` or run instructions
- sample inputs and outputs

## Must-have sections in README

- Problem statement
- Why a plain LLM is not enough
- Architecture overview
- Agentic pattern used
- Failure handling
- Evaluation results
- Known limitations
- How to run
- Example interaction

## Must-have tests

- happy path
- malformed input
- missing data
- timeout
- tool failure
- low-confidence case
- repeated request
- edge case

---

# How to use Codex effectively

Use Codex for implementation, not for architecture.

Before each build, write a short design brief:

```text
Problem:
User:
Input:
Output:
Tools:
State:
Failure cases:
Tests:
Acceptance criteria:
```

Then ask Codex to implement one layer at a time:

1. schema
2. data model
3. API
4. tool wrappers
5. orchestration
6. retries
7. tests
8. demo

After each step, verify:
- does this match the design?
- what assumptions were made?
- what breaks first?
- what needs a human decision?

---

# Sample weekly routine

If you are working 10–15 hours per week:

- 2 hours: read concept docs
- 2 hours: write architecture/design
- 4 hours: build with Codex
- 2 hours: break and test it
- 1–2 hours: document findings
- 1 hour: prepare interview explanation

---

# Final rule

Every project should end with an answer to these questions:

- What did this pattern solve?
- What did I learn?
- What went wrong?
- What would I do differently?
- When should this pattern be used in real systems?

That is what turns the projects into a learning path instead of just a GitHub folder collection.
