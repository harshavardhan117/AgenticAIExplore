# Persistence

This layer stores the reusable RAG artifacts after embedding.

| Package | Purpose |
| --- | --- |
| [`catalog/`](catalog/README.md) | SQLite metadata for pages, chunks, embeddings, and canonical citations. |
| [`vector_stores/`](vector_stores/README.md) | Similarity-search adapters for Oracle Database 23ai and OpenSearch. |

The catalog and vector store have separate jobs. Vector search finds candidate chunk IDs quickly; SQLite supplies canonical page title and URL for the final citation.
