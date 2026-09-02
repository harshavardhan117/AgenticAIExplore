# Vector stores

Vector stores persist `EmbeddedChunk` records and return nearest chunks for a query vector. They are hidden behind the `VectorStore` interface and selected through `VectorStoreFactory`.

The adapters are reusable: each receives the same embedded-record shape and can be selected without changing the RAG service.

The adapters are reusable: each receives the same embedded-record shape and can be selected without changing the RAG service.

## Supported backends

| Backend | Adapter | Required configuration |
| --- | --- | --- |
| Oracle Database 23ai | `oracle_store.py` | `ORACLE_VECTOR_HOST`, port, service name, username, password, and table name. |
| OpenSearch | `opensearch_store.py` | `OPENSEARCH_URL`, index name, and optional auth/TLS settings. |

For Oracle, required values are `ORACLE_VECTOR_HOST`, `ORACLE_VECTOR_USERNAME`, and `ORACLE_VECTOR_PASSWORD`; port defaults to `8123`, service to `FREEPDB1`, and table to `RAG_EMBEDDED_CHUNKS`. For OpenSearch, `OPENSEARCH_URL` is required; index, TLS, engine, space type, and optional paired basic-auth credentials use the `OPENSEARCH_*` variables in the root `.env.example`.

Both adapters automatically read the ignored root `.env` file. Exported values take precedence.

For Oracle, required values are `ORACLE_VECTOR_HOST`, `ORACLE_VECTOR_USERNAME`, and `ORACLE_VECTOR_PASSWORD`; port defaults to `8123`, service to `FREEPDB1`, and table to `RAG_EMBEDDED_CHUNKS`. For OpenSearch, `OPENSEARCH_URL` is required; index, TLS, engine, space type, and optional paired basic-auth credentials use the `OPENSEARCH_*` variables in the root `.env.example`.

Both adapters automatically read the ignored root `.env` file. Exported values take precedence.

## Upload existing local embeddings

These commands only upload already-generated vectors; they do not call the embedding model.

```powershell
python .\oracle_upload_embedded_chunks.py
python .\opensearch_upload_embedded_chunks.py
```

```bash
python oracle_upload_embedded_chunks.py
# or
python opensearch_upload_embedded_chunks.py
```

```bash
python oracle_upload_embedded_chunks.py
# or
python opensearch_upload_embedded_chunks.py
```

Use `--dry-run` to validate local input and inspect the plan before connecting to either backend.

## Retrieval score caution

Oracle returns cosine **distance** (lower is better). OpenSearch returns a k-NN **similarity score** (higher is better). Do not compare their raw numbers directly. The RAG service therefore uses independently configurable abstention thresholds: `RAG_MAX_COSINE_DISTANCE` and `RAG_MIN_KNN_SCORE`.
