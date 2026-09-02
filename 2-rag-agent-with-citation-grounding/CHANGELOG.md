# Changelog

This project follows a lightweight, learning-focused changelog. Versions describe the capabilities of the reusable RAG pipeline, not a production release promise.

## v1 — Confluence RAG prototype

- Added Confluence Data Center ingestion with environment-based authentication, request pacing, retries, and incremental refresh.
- Added HTML-to-block parsing and two chunking strategies; the minimal section strategy is the default for cost-conscious indexing.
- Added OCI embedding and OCI chat adapters, with replaceable provider contracts.
- Added a normalized SQLite catalog for page, chunk, embedding, and citation metadata.
- Added Oracle Database 23ai and OpenSearch as supported vector-store backends.
- Added grounded answering with source labels, Confluence citations, and configurable weak-evidence abstention.
- Added evaluation for Hit@K, MRR@K, answer relevancy, citation correctness, and abstention behavior.
- Added data and secret exclusion rules so local Confluence content, vectors, databases, reports, and credentials are not committed.

## v2 — Retrieval strategies and local API/UI

- Added strategy-based dense-vector, SQLite FTS5 keyword/BM25, and hybrid Reciprocal Rank Fusion retrieval.
- Added a shared evaluation switch so every retrieval strategy can be measured with Oracle or OpenSearch.
- Added a local FastAPI server with `/health` and `/api/ask` endpoints.
- Added a small browser UI that selects backend and retrieval strategy and renders grounded citations.

## Future ideas

- Add backend health checks, reranking, and native backend-specific hybrid retrieval.
- Add authentication and deployment hardening before exposing the API beyond a trusted environment.
