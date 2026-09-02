"""Read-only SQLite queries shared by keyword and dense retrieval."""

from __future__ import annotations

import re
import sqlite3
from pathlib import Path

from rag.models import Citation, RetrievedChunk


class CatalogReader:
    """Read citation metadata and FTS5 keyword results from the SQLite catalog."""

    def __init__(self, catalog_path: Path) -> None:
        self._catalog_path = catalog_path

    def find_pages(self, page_ids: list[str]) -> dict[str, tuple[str, str]]:
        """Return canonical titles and URLs keyed by page ID."""

        unique_ids = list(dict.fromkeys(page_ids))
        if not unique_ids:
            return {}
        placeholders = ", ".join("?" for _ in unique_ids)
        with self._connect() as connection:
            rows = connection.execute(
                f"SELECT page_id, title, page_url FROM pages WHERE page_id IN ({placeholders})",
                unique_ids,
            ).fetchall()
        return {page_id: (title, page_url) for page_id, title, page_url in rows}

    def keyword_search(self, question: str, limit: int) -> list[RetrievedChunk]:
        """Use SQLite FTS5/BM25 to rank chunks matching meaningful query terms."""

        terms = re.findall(r"[A-Za-z0-9_]+", question)
        if not terms:
            return []
        fts_query = " OR ".join(f'"{term}"' for term in terms)
        with self._connect() as connection:
            rows = connection.execute(
                """
                SELECT chunks.chunk_id, chunks.page_id, chunks.heading_path, chunks.content,
                       pages.title, pages.page_url, bm25(chunk_fts) AS bm25_rank
                FROM chunk_fts
                JOIN chunks ON chunks.chunk_id = chunk_fts.chunk_id
                JOIN pages ON pages.page_id = chunks.page_id
                WHERE chunk_fts MATCH ?
                ORDER BY bm25_rank
                LIMIT ?
                """,
                (fts_query, limit),
            ).fetchall()
        return [
            RetrievedChunk(
                rank=rank,
                # SQLite BM25 ranks lower as better. Negating makes the displayed
                # value easier to read, but it is not comparable to vector scores.
                score=float(-row[6]),
                score_kind="bm25",
                chunk_id=row[0],
                page_id=row[1],
                heading_path=row[2],
                content=row[3],
                citation=Citation(page_id=row[1], page_title=row[4], page_url=row[5]),
            )
            for rank, row in enumerate(rows, start=1)
        ]

    def _connect(self) -> sqlite3.Connection:
        if not self._catalog_path.is_file():
            raise FileNotFoundError(
                f"SQLite catalog was not found: {self._catalog_path}. Run sync_sqlite_catalog.py first."
            )
        return sqlite3.connect(f"{self._catalog_path.as_uri()}?mode=ro", uri=True)
