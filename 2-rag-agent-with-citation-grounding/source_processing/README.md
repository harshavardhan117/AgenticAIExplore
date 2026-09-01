# Source processing

This layer turns selected Confluence pages into stable, local RAG artifacts. It does not call an embedding model or a vector store.

```text
page_ids.txt -> ingestion -> raw_pages/<page-id>.json -> chunking -> chunks/<strategy>/<page-id>.json
```

## Modules

- [`ingestion/`](ingestion/README.md): reads page IDs, calls the Confluence REST API, and saves raw page snapshots.
- [`chunking/`](chunking/README.md): parses Confluence storage HTML and turns it into chunks with page and section metadata.

All outputs are written under `data/` and are intentionally ignored by Git. This keeps private source content out of the repository.
