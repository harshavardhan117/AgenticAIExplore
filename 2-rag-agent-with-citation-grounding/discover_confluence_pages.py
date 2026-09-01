"""List all descendant Confluence pages below a selected parent page.

Before running, replace the three placeholder values below. This script reads
only page metadata; it does not save the page body or send credentials anywhere
other than your Confluence site.
"""

from __future__ import annotations

import json
import os
import time
from base64 import b64encode
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen

# Values can be supplied as PowerShell environment variables instead of being
# written in this file: CONFLUENCE_BASE_URL, CONFLUENCE_PAGE_ID, and
# CONFLUENCE_TOKEN.
# Example base URL: "https://confluence.example.com"
CONFLUENCE_BASE_URL = os.getenv(
    "CONFLUENCE_BASE_URL", "https://YOUR-CONFLUENCE-SITE"
)
PAGE_ID = os.getenv("CONFLUENCE_PAGE_ID", "REPLACE_WITH_PAGE_ID")

# For a personal API token, use AUTH_MODE = "basic" and set CONFLUENCE_EMAIL.
# For an OAuth/PAT bearer token, leave AUTH_MODE = "bearer".
AUTH_MODE = os.getenv("CONFLUENCE_AUTH_MODE", "bearer")
CONFLUENCE_TOKEN = os.getenv("CONFLUENCE_TOKEN", "REPLACE_WITH_YOUR_TOKEN")
CONFLUENCE_EMAIL = os.getenv("CONFLUENCE_EMAIL", "REPLACE_WITH_YOUR_EMAIL")

# Use "data-center" for self-managed Confluence. Use "cloud"
# only for sites hosted at *.atlassian.net.
CONFLUENCE_PLATFORM = os.getenv("CONFLUENCE_PLATFORM", "data-center")

# Keep ingestion polite to the Confluence server. These values can be adjusted
# for one PowerShell session without changing this file.
REQUEST_DELAY_SECONDS = float(os.getenv("CONFLUENCE_REQUEST_DELAY_SECONDS", "0.5"))
MAX_RETRIES = int(os.getenv("CONFLUENCE_MAX_RETRIES", "3"))
INITIAL_BACKOFF_SECONDS = float(
    os.getenv("CONFLUENCE_INITIAL_BACKOFF_SECONDS", "1")
)
# A depth of 1 lists only direct children; 3 includes children, grandchildren,
# and great-grandchildren beneath PAGE_ID.
MAX_DEPTH = int(os.getenv("CONFLUENCE_MAX_DEPTH", "3"))
# Comma-separated parent page IDs to exclude, together with every descendant.
# Example: $env:CONFLUENCE_EXCLUDED_PAGE_IDS = "12345,67890"
EXCLUDED_PAGE_IDS = {
    page_id.strip()
    for page_id in os.getenv("CONFLUENCE_EXCLUDED_PAGE_IDS", "").split(",")
    if page_id.strip()
}
# File to receive discovered descendant page IDs, one per line. Keep this
# separate from data/page_ids.txt until the discovered scope is reviewed.
OUTPUT_PAGE_ID_FILE = os.getenv(
    "CONFLUENCE_OUTPUT_PAGE_ID_FILE",
    f"data/discovered_page_ids_{PAGE_ID}.txt",
).strip()
LAST_REQUEST_STARTED_AT: float | None = None

def authorization_header() -> str:
    if AUTH_MODE == "bearer":
        return f"Bearer {CONFLUENCE_TOKEN}"

    if AUTH_MODE == "basic":
        credentials = f"{CONFLUENCE_EMAIL}:{CONFLUENCE_TOKEN}".encode()
        return f"Basic {b64encode(credentials).decode()}"

    raise ValueError('AUTH_MODE must be either "bearer" or "basic".')


def get_json(url: str) -> dict:
    global LAST_REQUEST_STARTED_AT

    request = Request(
        url,
        headers={
            "Accept": "application/json",
            "Authorization": authorization_header(),
        },
    )

    for attempt in range(MAX_RETRIES + 1):
        if LAST_REQUEST_STARTED_AT is not None:
            elapsed = time.monotonic() - LAST_REQUEST_STARTED_AT
            delay = REQUEST_DELAY_SECONDS - elapsed
            if delay > 0:
                time.sleep(delay)

        LAST_REQUEST_STARTED_AT = time.monotonic()

        try:
            with urlopen(request, timeout=20) as response:
                return json.load(response)
        except HTTPError as error:
            should_retry = error.code == 429 or 500 <= error.code < 600
            if not should_retry or attempt == MAX_RETRIES:
                raise

            retry_after = error.headers.get("Retry-After")
            retry_delay = (
                float(retry_after)
                if retry_after and retry_after.isdigit()
                else INITIAL_BACKOFF_SECONDS * (2**attempt)
            )
            print(
                f"Debug: HTTP {error.code}; retrying in {retry_delay:.1f}s "
                f"({attempt + 1}/{MAX_RETRIES})."
            )
            time.sleep(retry_delay)
        except URLError as error:
            if attempt == MAX_RETRIES:
                raise

            retry_delay = INITIAL_BACKOFF_SECONDS * (2**attempt)
            print(
                f"Debug: temporary network error ({error.reason}); retrying in "
                f"{retry_delay:.1f}s ({attempt + 1}/{MAX_RETRIES})."
            )
            time.sleep(retry_delay)

    raise RuntimeError("Unreachable retry state.")


def get_child_pages(parent_page_id: str) -> list[dict]:
    base_url = CONFLUENCE_BASE_URL.rstrip("/")
    if CONFLUENCE_PLATFORM != "data-center":
        raise ValueError(
            'Listing descendants is currently implemented for "data-center" only.'
        )

    children: list[dict] = []
    start = 0
    limit = 100

    while True:
        print(f"Debug: fetching children of page {parent_page_id} (start={start})")
        query = urlencode({"start": start, "limit": limit})
        url = f"{base_url}/rest/api/content/{parent_page_id}/child/page?{query}"
        response = get_json(url)
        batch = response.get("results", [])
        children.extend(batch)

        if len(batch) < limit:
            return children

        start += len(batch)


def get_page_metadata(page_id: str) -> dict:
    base_url = CONFLUENCE_BASE_URL.rstrip("/")
    return get_json(f"{base_url}/rest/api/content/{page_id}")


def build_page_tree() -> tuple[dict[str, dict], dict[str, list[str]]]:
    """Build a depth-limited tree while expanding each page ID at most once."""
    if MAX_DEPTH < 0:
        raise ValueError("CONFLUENCE_MAX_DEPTH must be zero or greater.")
    if PAGE_ID in EXCLUDED_PAGE_IDS:
        raise ValueError("PAGE_ID cannot also appear in CONFLUENCE_EXCLUDED_PAGE_IDS.")

    root_page = get_page_metadata(PAGE_ID)
    pages_by_id = {PAGE_ID: root_page}
    child_ids_by_parent: dict[str, list[str]] = {PAGE_ID: []}
    pending_parent_ids = [(PAGE_ID, 0)]

    while pending_parent_ids:
        parent_page_id, depth = pending_parent_ids.pop(0)
        if depth >= MAX_DEPTH:
            print(
                f"Debug: reached configured depth {MAX_DEPTH} at page "
                f"{parent_page_id}; not expanding it further."
            )
            continue

        for child in get_child_pages(parent_page_id):
            child_id = child["id"]
            if child_id in EXCLUDED_PAGE_IDS:
                print(
                    f"Debug: excluding page {child_id} and all of its descendants."
                )
                continue
            if child_id in pages_by_id:
                print(
                    f"Debug: skipping already discovered page {child_id} "
                    "to prevent a duplicate or loop."
                )
                continue

            pages_by_id[child_id] = child
            child_ids_by_parent.setdefault(parent_page_id, []).append(child_id)
            child_ids_by_parent.setdefault(child_id, [])
            pending_parent_ids.append((child_id, depth + 1))

            descendant_count = len(pages_by_id) - 1
            if descendant_count % 5 == 0:
                print(
                    f"Progress: found {descendant_count} pages "
                    f"({len(pending_parent_ids)} still to inspect)."
                )

    return pages_by_id, child_ids_by_parent


def print_page_tree(
    page_id: str,
    pages_by_id: dict[str, dict],
    child_ids_by_parent: dict[str, list[str]],
    prefix: str = "",
    is_last: bool = True,
    is_root: bool = True,
) -> None:
    page = pages_by_id[page_id]
    label = f"{page_id} | {page['title']}"

    if is_root:
        print(label)
    else:
        connector = "└── " if is_last else "├── "
        print(f"{prefix}{connector}{label}")

    children = child_ids_by_parent[page_id]
    child_prefix = prefix if is_root else prefix + ("    " if is_last else "│   ")
    for index, child_id in enumerate(children):
        print_page_tree(
            child_id,
            pages_by_id,
            child_ids_by_parent,
            child_prefix,
            index == len(children) - 1,
            False,
        )


def write_descendant_page_ids(pages_by_id: dict[str, dict]) -> None:
    """Write discovered descendants in discovery order when an output is configured."""

    output_path = Path(OUTPUT_PAGE_ID_FILE)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    descendant_ids = [page_id for page_id in pages_by_id if page_id != PAGE_ID]
    output_path.write_text("\n".join(descendant_ids) + "\n", encoding="utf-8")
    print(f"\nWrote {len(descendant_ids)} descendant page ID(s) to {output_path}.")


def main() -> None:
    if "REPLACE_WITH" in PAGE_ID or "REPLACE_WITH" in CONFLUENCE_TOKEN:
        raise ValueError("Replace PAGE_ID and CONFLUENCE_TOKEN before running.")

    try:
        pages_by_id, child_ids_by_parent = build_page_tree()
    except HTTPError as error:
        message = error.read().decode(errors="replace")
        raise SystemExit(
            f"Confluence returned HTTP {error.code} for {error.url}: {message}"
        ) from error
    except URLError as error:
        raise SystemExit(f"Could not reach Confluence: {error.reason}") from error

    print(
        f"\nFound {len(pages_by_id) - 1} page(s) within depth "
        f"{MAX_DEPTH} beneath parent {PAGE_ID}:\n"
    )
    print_page_tree(PAGE_ID, pages_by_id, child_ids_by_parent)
    write_descendant_page_ids(pages_by_id)


if __name__ == "__main__":
    main()
