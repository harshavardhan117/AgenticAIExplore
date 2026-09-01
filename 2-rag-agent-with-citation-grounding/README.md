# Confluence RAG with Citation Grounding

A reusable Python prototype for answering questions from **Confluence content**. It retrieves relevant page sections, asks an LLM to answer only from that evidence, and returns Confluence citations. When evidence is weak, it abstains instead of guessing.

The code and documentation are intentionally generic: point it at a Confluence space or page collection and use your own page IDs, credentials, models, and vector-store deployment.

## What it does

```text
Confluence page IDs
  -> ingestion -> private raw JSON snapshots
  -> chunking -> private chunk JSON
  -> OCI embeddings -> private embedded JSON
  -> SQLite catalog + vector store
  -> retrieve -> grounded OCI chat answer + Confluence citations
  -> evaluation
```

Supported storage is split by responsibility:

| Store | Role | Supported implementation |
| --- | --- | --- |
| SQLite | Normalized metadata and citation catalog | Python `sqlite3` |
| Vector store | Vector similarity search | Oracle Database 23ai |
| Vector store | Vector similarity search | OpenSearch with k-NN |

## Repository layout

| Path | Responsibility |
| --- | --- |
| [`source_processing/`](source_processing/README.md) | Collect, parse, and chunk Confluence pages. |
| [`embedding_pipeline/`](embedding_pipeline/README.md) | Turn chunks into provider-neutral embedded records. |
| [`persistence/`](persistence/README.md) | Maintain SQLite metadata and upload/search vectors. |
| [`rag/`](rag/README.md) | Retrieve evidence, build a grounded prompt, and generate cited answers. |
| [`evaluation/`](evaluation/README.md) | Measure retrieval, answer, citation, and abstention behavior. |
| [`deploy/`](deploy/README.md) | Optional Kubernetes manifest for an Oracle 23ai learning deployment. |
| [`data/`](data/.gitignore) | Local-only source and generated artifacts; never committed. |

## Quick start

1. Create and activate a virtual environment, then install dependencies:

   ```powershell
   python -m venv .venv
   .\.venv\Scripts\Activate.ps1
   pip install -r requirements.txt
   ```

2. Copy the variable names from [`.env.example`](.env.example) into your shell or a local `.env` file. Keep real values outside Git.

3. Put one Confluence page ID per line in `data/page_ids.txt`, then follow the pipeline below. The file is intentionally ignored.

## End-to-end pipeline

From this directory:

```powershell
# 1. Fetch selected Confluence pages into private JSON snapshots.
python .\collect_confluence_pages.py

# 2. Parse and chunk every downloaded page.
python .\chunk_all_pages.py

# 3. Preview embedding cost, then generate embeddings when ready.
python .\embed_all_chunks.py
python .\embed_all_chunks.py --all

# 4. Build the local SQLite citation catalog.
python .\sync_sqlite_catalog.py

# 5. Upload existing vectors to one backend. These commands do not call OCI again.
python .\oracle_upload_embedded_chunks.py
# or
python .\opensearch_upload_embedded_chunks.py

# 6. Inspect retrieval or ask a grounded question.
python .\query_rag.py "How do I configure this feature?" --backend oracle
python .\ask_rag.py "How do I configure this feature?" --backend oracle
```

Use `--backend opensearch` after uploading to OpenSearch. See the module READMEs for configuration and troubleshooting details.

## Evaluation

Create a private JSON evaluation dataset with answerable questions, expected source URLs, and unsupported questions marked `should_abstain: true`. Then run:

```powershell
python .\evaluate_rag.py --backend oracle --limit 5 `
  --output-path .\data\evaluation\runs\oracle_metrics.json

python .\evaluate_rag.py --backend opensearch --limit 5 `
  --output-path .\data\evaluation\runs\opensearch_metrics.json
```

The report contains Hit@K, MRR@K, answer relevancy, citation correctness, and abstention accuracy. The dataset and reports remain local by design.

## Security and data boundaries

- Never commit tokens, passwords, private keys, OCI configuration, internal URLs, page IDs, page snapshots, chunk JSON, embeddings, SQLite databases, or evaluation reports.
- `.env.example` contains variable names and harmless placeholders only. Use shell variables or a local ignored `.env` file for real values.
- `data/` is ignored by default. Treat content collected from Confluence as private, even when a page appears harmless.
- Review staged files before every commit with `git diff --cached`.

See [CHANGELOG.md](CHANGELOG.md) for v1 scope and planned v2 FastAPI/UI work.
