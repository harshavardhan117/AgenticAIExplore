# RAG runtime

This package handles one question at a time. It does not ingest, chunk, or upload content; those are offline preparation steps.

## Call flow

```text
RAGRequest
  -> RAGService.retrieve()
  -> OCI query embedding
  -> selected vector-store search
  -> SQLite citation enrichment
  -> evidence threshold / abstention decision
  -> prompt construction
  -> OCI chat generation
  -> RAGResponse with citations and resolved [Source N] labels
```

## Main files

| File | Responsibility |
| --- | --- |
| `models.py` | Strict request, result, citation, and response DTOs. |
| `service.py` | Coordinates retrieval, evidence gating, prompt creation, and answer generation. |
| `prompt_builder.py` | Builds the grounded prompt and labels supplied chunks as `[Source N]`. |
| `oci_chat.py` | OCI chat client configured from environment variables. |
| `oci_chat_formats.py` | Adapters for OCI Cohere and OCI OpenAI-compatible request formats. |

## Use it from the CLI

Inspect retrieval without calling a chat model:

```powershell
python .\query_rag.py "How is this feature configured?" --backend oracle --limit 5
```

Generate a grounded answer:

```powershell
python .\ask_rag.py "How is this feature configured?" --backend opensearch --limit 5
```

## Abstention

The service abstains when no chunks are returned or the best score fails the backend-specific evidence threshold. This prevents the LLM from treating merely-nearest chunks as valid evidence. Tune thresholds from a private evaluation dataset; do not copy one backend's raw scores to another backend.
