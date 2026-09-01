# Vector stores

Vector stores persist `EmbeddedChunk` records and return nearest chunks for a query vector. They are hidden behind the `VectorStore` interface and selected through `VectorStoreFactory`.

## Supported backends

| Backend | Adapter | Required configuration |
| --- | --- | --- |
| Oracle Database 23ai | `oracle_store.py` | `ORACLE_VECTOR_HOST`, port, service name, username, password, and table name. |
| OpenSearch | `opensearch_store.py` | `OPENSEARCH_URL`, index name, and optional auth/TLS settings. |

## Upload existing local embeddings

These commands only upload already-generated vectors; they do not call the embedding model.

```powershell
python .\oracle_upload_embedded_chunks.py
python .\opensearch_upload_embedded_chunks.py
```

Use `--dry-run` to validate local input and inspect the plan before connecting to either backend.

## Retrieval score caution

Oracle returns cosine **distance** (lower is better). OpenSearch returns a k-NN **similarity score** (higher is better). Do not compare their raw numbers directly. The RAG service therefore uses independently configurable abstention thresholds: `RAG_MAX_COSINE_DISTANCE` and `RAG_MIN_KNN_SCORE`.
