# SQLite catalog

The SQLite catalog is the local source of truth for metadata and citations. It is not a vector database.

## Schema

- `pages`: page ID, title, URL, last-modified time, and version.
- `chunks`: chunk ID, page ID, heading path, ordered content, and chunk metadata.
- `embeddings`: one embedding record per chunk, including model and dimension metadata.
- `chunk_fts`: an SQLite FTS5 index over heading paths and chunk content for keyword/BM25 retrieval.

The relationships are normalized: one page has many chunks; one chunk has one current embedding record in this prototype.

## Build or refresh

```powershell
python .\sync_sqlite_catalog.py
```

It reads local raw pages, chunks, and embedded chunks, then creates or refreshes `data/ats_rag.db`. The database is ignored by Git because it contains private page metadata and content references.

## Why keep SQLite when a vector store already has metadata?

It makes citations backend-independent. Either vector store can return a `page_id` and `chunk_id`; the RAG service uses SQLite to return one canonical page title and Confluence URL.

It also enables the backend-independent keyword strategy. Run `sync_sqlite_catalog.py` after refreshing chunks so the FTS index is rebuilt with the latest content.
