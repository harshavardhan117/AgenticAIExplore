# Structured Output Agent

A small Python module that turns a natural-language request into validated JSON matching a requested output format.

Example: describe an issue in plain English, select the `jira/v1` artifact, and receive a JSON payload that a Jira API or MCP tool can use directly.

## What it does

```text
User request
  → load or accept an output JSON format
  → build a provider-neutral prompt
  → call OCI or OpenAI
  → validate the returned JSON against the required shape
  → repair and retry invalid model output up to two times
  → return one consistent ExecutionResponse object
```

The module supports two ways to provide an output format:

- **Stored artifact:** provide an artifact name and version, for example `jira` and `v1`.
- **Inline JSON:** provide the required output JSON object directly in `output_format`.

## Current architecture

```text
main.run()
  → composition.build_orchestrator()
  → StructuredOutputOrchestrator.execute()
      → artifact resolver
      → prompt builders
      → provider service
      → JSON validator and retry helper
      → ExecutionResponse
```

The current optimized design keeps object wiring in `engine/composition.py`, while the orchestrator coordinates the request flow. Providers and artifact strategies are registered in their own modules, making future additions easier.

Editable diagrams:

- [Baseline UML Lite diagram](structured-output-agent-uml-clean-v2.excalidraw)
- [Optimization V3 UML Lite diagram](structured-output-agent-uml-optimization-v3.excalidraw)

See [CHANGELOG.md](CHANGELOG.md) for the V1 baseline and V2 optimization history.

## Project layout

```text
artifacts/      Output-format loading and resolution strategies
engine/         Application wiring and orchestration
prompts/        Provider-neutral prompt models and builders
providers/      Provider contract, registry, OCI/OpenAI adapters, configs
validation/     Generated JSON validation
responses/      Final response model
errors/         Error codes and domain exceptions
tests/          Unit tests
main.py         Simple public entry point: run(request)
```

## Run locally

Run commands from this folder:

```powershell
cd "C:\Users\Harshavardhan Reddy\Downloads\Agentic AI Explore\AgenticAIExplore\1-structured-output-agent"
```

Create a virtual environment and install the current runtime/test libraries:

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install "jsonschema>=4.0" "oci>=2.0" "pydantic>=2.0" "openai>=1.0" "pytest>=8.0"
```

> The module currently runs from the repository folder. True `pip install -e .` support is a future packaging task because the multiple top-level folders are not yet configured for setuptools discovery.

## OCI configuration

The OCI provider uses the standard OCI profile/key-file authentication flow. Keep the profile and private key outside the repository, normally under your user folder:

```text
C:\Users\<your-user>\.oci\config
C:\Users\<your-user>\.oci\oci_api_key.pem
```

Set these environment variables in the PowerShell session that runs the module:

```powershell
$env:OCI_CONFIG_FILE_PATH = "$env:USERPROFILE\.oci\config"
$env:OCI_PROFILE_NAME = "DEFAULT"
$env:OCI_COMPARTMENT_ID = "<your-compartment-ocid>"
$env:OCI_ENDPOINT = "<your-OCI-inference-endpoint>"
$env:OCI_MODEL_ID = "<your-on-demand-model-ocid>"
```

Do not place their values, your OCI config, or your private key in Git.

## Example request

The Jira artifact in this repository is located at:

```text
artifacts/jira/v1/output_format.json
```

Run this sample from the project folder:

```powershell
@'
from main import run

request = {
    "user_summary": "The login API returns HTTP 500 for valid users. Create a medium-priority bug ticket.",
    "output_format": "jira",
    "output_format_version": "v1",
}

print(run(request).model_dump_json(indent=2))
'@ | .\.venv\Scripts\python.exe -
```

To use an inline output format instead, pass a JSON object directly:

```python
request = {
    "user_summary": "Create a bug ticket for a login API error.",
    "output_format": {
        "summary": "",
        "priority": {"name": ""},
    },
    "provider": "oci",
}
```

## Response shape

Every call returns `ExecutionResponse`:

```json
{
  "success": true,
  "message": "Structured output generated successfully",
  "error_code": null,
  "output": {},
  "provider_name": "oci",
  "request_id": "provider-request-id",
  "retry_count": 0,
  "confidence_score": null
}
```

## Tests

Run all unit tests:

```powershell
.\.venv\Scripts\python.exe -m pytest -q
```

The current suite has 35 tests covering artifact resolution, prompt building, provider selection, adapters, JSON validation, retry behavior, errors, and the outer entry point.

## Safety and logs

- Only the requested artifact is loaded.
- Artifact identifiers allow only letters, numbers, `_`, and `-`.
- Invalid user input returns a safe domain error and is not retried.
- Only invalid model output triggers repair retries.
- Lifecycle logs contain safe metadata such as provider, request ID, duration, and retry count.
- Logs never include credentials, full prompts, artifact JSON, or raw model responses.

The embedding application controls Python logging configuration. The module itself does not force a global logging format or level.

## Adding future extensions

### Add a provider

1. Create an adapter that satisfies `GenerationProvider`.
2. Add a builder function in `providers/registration.py`.
3. Register it inside `register_builtin_providers()`.

### Add an artifact strategy

1. Create a class that satisfies `ArtifactResolutionStrategy`.
2. Register it inside `artifacts/registration.py`.

The registration order matters for artifact strategies: the resolver uses the first strategy whose `can_resolve()` method matches.
