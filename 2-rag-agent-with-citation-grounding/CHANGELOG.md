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

## v2 — Planned

- Add FastAPI endpoints for retrieval and grounded question answering.
- Add a small browser UI for asking questions and viewing citations.
- Add configuration validation, backend health endpoints, and more retrieval strategies such as hybrid search and reranking.
