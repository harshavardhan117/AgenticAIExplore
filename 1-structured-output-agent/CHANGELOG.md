# Change List

This project uses two learning versions. The current `master` branch contains both the functional baseline and the V2 refactoring work.

## V2 — Refined architecture

Status: merged into `master`.

### Design improvements

- Added `engine/composition.py` as the single application-wiring place.
- Changed `StructuredOutputOrchestrator` to receive collaborators through its constructor.
- Extracted the retry loop into `_generate_with_retries()` so `execute()` shows the high-level flow.
- Kept the retry rule simple: invalid model output receives up to two repair attempts; user-input errors are not retried.

### Extension improvements

- Refactored `ProviderFactory` into an empty provider registry with `register()` and `create()`.
- Added `providers/registration.py` to register OCI and OpenAI provider builders.
- Refactored `ArtifactResolver` into an ordered strategy registry with `register()` and `resolve()`.
- Added `artifacts/registration.py` to register inline and stored-file artifact strategies.

### Observability improvements

- Added safe `INFO` and `WARNING` lifecycle logs in `main.py`, the orchestrator, and OCI/OpenAI adapters.
- Logged only provider name, provider request ID, duration, retry count, success/failure, and safe error metadata.
- Explicitly excluded credentials, full prompts, artifact JSON, raw model output, and exception details from logs.

### Learning artifacts

- Updated the [V2 UML Lite diagram](structured-output-agent-uml-clean-v2.excalidraw) with the optimized architecture.
- Reviewed OOP relationships, SOLID principles, and creational/structural/behavioral design patterns against this codebase.

### Verification

- Unit tests: 35 passed.
- OCI happy-path integration: verified manually with the Jira V1 artifact.

### Remaining future work

- Configure package discovery so the project can be installed with `pip install -e .` and distributed as a wheel.
- Add an API/CLI adapter when needed.
- Add a retry-policy object only if retry rules grow (backoff, provider errors, environment-specific limits).
- Consider shared SDK-client lifecycle only for a long-running API server/worker.
- Add additional input-security checks only when the module accepts untrusted external traffic.

## V1 — Functional baseline on master

Status: complete baseline.

### Core capability

- Accepts a user summary, selected provider, and output format.
- Supports inline JSON formats and versioned stored artifacts.
- Resolves all artifact inputs into `ResolvedArtifact`.
- Builds provider-neutral system and user prompt messages.
- Supports OCI and OpenAI provider adapters behind one `GenerationProvider` Protocol.
- Calls the selected provider and normalizes the result into `ModelResponse`.
- Validates generated JSON and its required structure against the artifact format.
- Repairs invalid model output and retries up to two times.
- Returns a consistent Pydantic `ExecutionResponse`.

### Safety and errors

- Uses OCI profile/key-file authentication through environment-driven configuration.
- Restricts stored artifact identifiers to safe path characters.
- Uses domain error codes and safe outer error responses.
- Keeps provider credentials and user configuration outside the repository.

### Tests

- Added unit tests for baseline artifact, prompt, provider, validation, retry, and error behavior.
