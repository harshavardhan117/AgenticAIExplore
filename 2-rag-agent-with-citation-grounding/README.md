# Confluence RAG with Citation Grounding

A reusable Python RAG prototype for answering questions from **Confluence pages**. It retrieves relevant sections, asks an LLM to answer only from that evidence, and returns links to the source pages. When evidence is weak, it abstains instead of guessing.

Bring your own Confluence page IDs, credentials, OCI models, and vector-store deployment. Source snapshots, chunks, embeddings, SQLite databases, evaluation datasets, and reports stay local under `data/` and are ignored by Git.

## Capabilities

```text
Confluence page IDs
  -> ingestion -> private raw JSON snapshots
  -> chunking -> private chunk JSON
  -> OCI embeddings -> private embedded JSON
  -> SQLite catalog + vector store
  -> retrieve -> grounded OCI chat answer + Confluence citations
  -> evaluation
```

| Component | Role | Included implementation |
| --- | --- | --- |
| SQLite | Normalized metadata, citations, and keyword search | Python `sqlite3` with FTS5/BM25 |
| Oracle Database 23ai | Dense-vector search | `python-oracledb` adapter |
| OpenSearch with k-NN | Dense-vector search | `opensearch-py` adapter |
| OCI Generative AI | Embeddings and grounded chat | OCI SDK adapters |

## Repository layout

| Path | Responsibility |
| --- | --- |
| [`source_processing/`](source_processing/README.md) | Discover, collect, parse, and chunk Confluence pages. |
| [`embedding_pipeline/`](embedding_pipeline/README.md) | Convert chunks to provider-neutral embedded records. |
| [`persistence/`](persistence/README.md) | Maintain the SQLite catalog and vector-store adapters. |
| [`rag/`](rag/README.md) | Retrieve with dense, keyword, or hybrid search and generate cited answers. |
| [`evaluation/`](evaluation/README.md) | Measure retrieval, answer, citation, and abstention behavior. |
| [`api_server.py`](api_server.py), [`web/`](web/index.html) | Local FastAPI endpoint and browser interface. |
| [`deploy/`](deploy/README.md) | Optional Kubernetes learning deployment for Oracle Database 23ai. |
| [`data/`](data/.gitignore) | Local-only source and generated artifacts; never committed. |

## Configuration

### Prefer a local `.env` file

For local development, copy the committed template and fill in only the values needed for the command you plan to run. `.env` is ignored by Git. The application loads it automatically, while values explicitly exported in your shell take precedence.

```powershell
# Windows PowerShell
Copy-Item .env.example .env
notepad .env
```

```bash
# Linux / macOS Bash
cp .env.example .env
${EDITOR:-vi} .env
```

Never commit `.env`, an OCI config file, a private key, tokens, passwords, private URLs, source pages, or generated `data/` artifacts.

### Or export values for one shell session

Use this approach for a one-off command or CI system. Replace every placeholder locally; do not paste real values into source code or documentation.

```powershell
# Windows PowerShell
$env:CONFLUENCE_BASE_URL = "https://confluence.example.com"
$env:CONFLUENCE_TOKEN = "<personal-access-token>"
$env:CONFLUENCE_AUTH_MODE = "bearer"

$env:OCI_CONFIG_FILE_PATH = "C:\path\to\oci\config"
$env:OCI_PROFILE_NAME = "DEFAULT"
$env:OCI_COMPARTMENT_ID = "<compartment-ocid>"
$env:OCI_ENDPOINT = "https://inference.generativeai.<region>.oci.oraclecloud.com"
$env:OCI_EMBEDDING_MODEL_ID = "<embedding-model-id>"
$env:OCI_CHAT_MODEL_ID = "<chat-model-id>"
$env:OCI_CHAT_REQUEST_FORMAT = "openai" # or cohere

$env:ORACLE_VECTOR_HOST = "<host>"
$env:ORACLE_VECTOR_PORT = "1521"
$env:ORACLE_VECTOR_SERVICE_NAME = "FREEPDB1"
$env:ORACLE_VECTOR_USERNAME = "<username>"
$env:ORACLE_VECTOR_PASSWORD = "<password>"

$env:OPENSEARCH_URL = "http://localhost:9200"
```

```bash
# Linux / macOS Bash
export CONFLUENCE_BASE_URL="https://confluence.example.com"
export CONFLUENCE_TOKEN="<personal-access-token>"
export CONFLUENCE_AUTH_MODE="bearer"

export OCI_CONFIG_FILE_PATH="$HOME/.oci/config"
export OCI_PROFILE_NAME="DEFAULT"
export OCI_COMPARTMENT_ID="<compartment-ocid>"
export OCI_ENDPOINT="https://inference.generativeai.<region>.oci.oraclecloud.com"
export OCI_EMBEDDING_MODEL_ID="<embedding-model-id>"
export OCI_CHAT_MODEL_ID="<chat-model-id>"
export OCI_CHAT_REQUEST_FORMAT="openai" # or cohere

export ORACLE_VECTOR_HOST="<host>"
export ORACLE_VECTOR_PORT="1521"
export ORACLE_VECTOR_SERVICE_NAME="FREEPDB1"
export ORACLE_VECTOR_USERNAME="<username>"
export ORACLE_VECTOR_PASSWORD="<password>"

export OPENSEARCH_URL="http://localhost:9200"
```

See [`.env.example`](.env.example) for the complete placeholder-only template. The required variables depend on the module and selected retrieval strategy; the module READMEs list the smallest working set.

### Environment-variable reference

| Group | Variables | Used by |
| --- | --- | --- |
| Confluence access | `CONFLUENCE_BASE_URL`, `CONFLUENCE_TOKEN`, `CONFLUENCE_AUTH_MODE`, `CONFLUENCE_EMAIL` | Page discovery and ingestion |
| Confluence pacing | `CONFLUENCE_REQUEST_DELAY_SECONDS`, `CONFLUENCE_MAX_RETRIES`, `CONFLUENCE_INITIAL_BACKOFF_SECONDS` | Discovery and ingestion |
| Discovery scope | `CONFLUENCE_PAGE_ID`, `CONFLUENCE_PLATFORM`, `CONFLUENCE_MAX_DEPTH`, `CONFLUENCE_EXCLUDED_PAGE_IDS`, `CONFLUENCE_OUTPUT_PAGE_ID_FILE` | `discover_confluence_pages.py` only |
| OCI embeddings | `OCI_CONFIG_FILE_PATH`, `OCI_PROFILE_NAME`, `OCI_COMPARTMENT_ID`, `OCI_ENDPOINT`, `OCI_EMBEDDING_MODEL_ID` | Embedding and dense retrieval |
| OCI chat | `OCI_CHAT_MODEL_ID`, `OCI_CHAT_REQUEST_FORMAT`, `OCI_CHAT_MAX_TOKENS`, `OCI_CHAT_TEMPERATURE` plus OCI connection variables | Grounded answering and LLM-as-judge evaluation |
| Oracle 23ai | `ORACLE_VECTOR_HOST`, `ORACLE_VECTOR_PORT`, `ORACLE_VECTOR_SERVICE_NAME`, `ORACLE_VECTOR_USERNAME`, `ORACLE_VECTOR_PASSWORD`, `ORACLE_VECTOR_TABLE_NAME` | Oracle upload and dense retrieval |
| OpenSearch | `OPENSEARCH_URL`, `OPENSEARCH_INDEX_NAME`, `OPENSEARCH_USERNAME`, `OPENSEARCH_PASSWORD`, `OPENSEARCH_VERIFY_CERTIFICATES`, `OPENSEARCH_VECTOR_ENGINE`, `OPENSEARCH_VECTOR_SPACE_TYPE` | OpenSearch upload and dense retrieval |
| Evidence gates | `RAG_MAX_COSINE_DISTANCE`, `RAG_MIN_KNN_SCORE` | Dense answer abstention |

`CONFLUENCE_AUTH_MODE` is `bearer` by default. Set it to `basic` and provide `CONFLUENCE_EMAIL` only when your Confluence deployment requires basic authentication. `OCI_CHAT_REQUEST_FORMAT` accepts `openai` or `cohere`; it must match the selected chat model.

## Install

```powershell
# Windows PowerShell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
```

```bash
# Linux / macOS Bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
```

## End-to-end pipeline

Create `data/page_ids.txt` with one approved Confluence page ID per line. The file is intentionally ignored.

```powershell
# Windows PowerShell
# 1. Fetch selected pages into private raw JSON snapshots.
python .\collect_confluence_pages.py

# 2. Parse and chunk every downloaded page.
python .\chunk_all_pages.py

# 3. Preview estimated embedding cost, then generate missing embeddings.
python .\embed_all_chunks.py
python .\embed_all_chunks.py --all

# 4. Build the local SQLite citation and keyword-search catalog.
python .\sync_sqlite_catalog.py

# 5. Upload existing embeddings. These commands do not call OCI again.
python .\oracle_upload_embedded_chunks.py
# or
python .\opensearch_upload_embedded_chunks.py

# 6. Inspect retrieval or generate a grounded answer.
python .\query_rag.py "How do I configure this feature?" --backend oracle --retrieval-strategy hybrid_rrf
python .\ask_rag.py "How do I configure this feature?" --backend oracle --retrieval-strategy hybrid_rrf
```

```bash
# Linux / macOS Bash
python collect_confluence_pages.py
python chunk_all_pages.py
python embed_all_chunks.py
python embed_all_chunks.py --all
python sync_sqlite_catalog.py
python oracle_upload_embedded_chunks.py
# or
python opensearch_upload_embedded_chunks.py
python query_rag.py "How do I configure this feature?" --backend opensearch --retrieval-strategy hybrid_rrf
python ask_rag.py "How do I configure this feature?" --backend opensearch --retrieval-strategy hybrid_rrf
```

Retrieval choices are `dense`, `keyword`, and `hybrid_rrf`. Dense uses the selected vector store; keyword uses the local SQLite FTS5/BM25 index; hybrid combines their rankings with reciprocal-rank fusion. Use `--backend opensearch` after uploading to OpenSearch. See the module READMEs for configuration and troubleshooting details.

## Evaluation

Create a local ignored JSON evaluation dataset with answerable questions, expected source URLs, and unsupported questions marked `should_abstain: true`. Then compare strategies and vector backends using one representative dataset.

```powershell
# Windows PowerShell
python .\evaluate_rag.py --backend oracle --retrieval-strategy dense --limit 5 `
  --output-path .\data\evaluation\runs\oracle_dense_metrics.json

python .\evaluate_rag.py --backend opensearch --retrieval-strategy hybrid_rrf --limit 5 `
  --output-path .\data\evaluation\runs\opensearch_hybrid_metrics.json
```

```bash
# Linux / macOS Bash
python evaluate_rag.py --backend oracle --retrieval-strategy dense --limit 5 \
  --output-path data/evaluation/runs/oracle_dense_metrics.json

python evaluate_rag.py --backend opensearch --retrieval-strategy hybrid_rrf --limit 5 \
  --output-path data/evaluation/runs/opensearch_hybrid_metrics.json
```

The report contains Hit@K, MRR@K, answer relevancy, citation correctness, and abstention accuracy. See [`evaluation/README.md`](evaluation/README.md) for the dataset shape and metric definitions.

## Local API and browser UI

Set the OCI variables and ensure `data/rag_catalog.db` has been created. `dense` and `hybrid_rrf` also need the selected vector backend. Keyword retrieval searches only the SQLite catalog, although the current shared API runtime still validates OCI configuration at startup.

```powershell
# Windows PowerShell
python -m uvicorn api_server:app --reload
```

```bash
# Linux / macOS Bash
python -m uvicorn api_server:app --reload
```

Open `http://127.0.0.1:8000` for the browser interface. The API is available at `POST /api/ask`, and interactive OpenAPI documentation is at `/docs`.

This server is intentionally local and unauthenticated. Do not expose it publicly until authentication, access control, HTTPS, rate limiting, logging controls, and operational safeguards are added.

## Security and data boundaries

- Never commit tokens, passwords, private keys, OCI configuration, private URLs, page IDs, page snapshots, chunk JSON, embeddings, SQLite databases, or evaluation reports.
- `.env.example` contains variable names and harmless placeholders only; `.env` is ignored.
- `data/` is ignored by default. Treat content collected from Confluence as private, even when a page appears harmless.
- Review staged files before every commit with `git diff --cached`.

See [CHANGELOG.md](CHANGELOG.md) for the completed v1 and v2 milestones and the scoped v3 ideas.
