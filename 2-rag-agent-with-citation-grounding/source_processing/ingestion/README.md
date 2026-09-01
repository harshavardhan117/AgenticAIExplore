# Confluence ingestion

The ingestion module fetches specific Confluence pages using the Confluence Data Center REST API and writes one raw JSON snapshot per page. The stored JSON preserves page title, URL, version, timestamps, hierarchy, labels, and storage-format HTML.

## Inputs

- `data/page_ids.txt`: one page ID per line; this file is local-only.
- Environment variables:
  - `CONFLUENCE_BASE_URL`, for example `https://confluence.example.com`
  - `CONFLUENCE_TOKEN`
  - `CONFLUENCE_AUTH_MODE=bearer` or `basic`
  - `CONFLUENCE_EMAIL`, only when basic authentication is used

Optional pacing controls: `CONFLUENCE_REQUEST_DELAY_SECONDS`, `CONFLUENCE_MAX_RETRIES`, and `CONFLUENCE_INITIAL_BACKOFF_SECONDS`.

## Run it

```powershell
python .\collect_confluence_pages.py
```

By default, an existing snapshot is skipped when Confluence reports that the page has not changed since it was fetched. Use `--overwrite` only when you intentionally need a full refresh.

```powershell
python .\collect_confluence_pages.py --page-id-file .\data\page_ids.txt --output-dir .\data\raw_pages
```

## Discovery helper

`discover_confluence_pages.py` walks child pages from a supplied parent page and produces a local page-ID list/tree. Use it to build a reviewable scope, then copy only approved page IDs to `data/page_ids.txt` before ingestion.

## Safety

Do not commit page IDs, raw JSON, Confluence URLs, or tokens. The module deliberately reads authentication from the environment and never writes the token into snapshots.
