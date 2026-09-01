"""Fetch configured Confluence pages and save one raw JSON snapshot per page."""

from __future__ import annotations

import argparse
import hashlib
import json
from datetime import UTC, datetime
from pathlib import Path
from urllib.error import HTTPError, URLError

from source_processing.ingestion.confluence_client import ConfluenceClient, ConfluenceConfig


DEFAULT_PAGE_ID_FILE = Path("data/page_ids.txt")
DEFAULT_OUTPUT_DIRECTORY = Path("data/raw_pages")


def read_page_ids(page_id_file: Path) -> list[str]:
    """Read page IDs, ignoring blank lines and comment lines beginning with #."""
    if not page_id_file.is_file():
        raise FileNotFoundError(
            f"Page ID file not found: {page_id_file}. Add one page ID per line."
        )

    page_ids: list[str] = []
    seen_page_ids: set[str] = set()
    for line in page_id_file.read_text(encoding="utf-8").splitlines():
        page_id = line.strip()
        if not page_id or page_id.startswith("#"):
            continue
        if page_id not in seen_page_ids:
            seen_page_ids.add(page_id)
            page_ids.append(page_id)
    return page_ids


def normalize_page(page: dict, base_url: str) -> dict:
    """Keep only source data needed for later parsing, chunking, and citations."""
    storage_html = page.get("body", {}).get("storage", {}).get("value", "")
    labels = [
        label["name"]
        for label in page.get("metadata", {}).get("labels", {}).get("results", [])
        if label.get("name")
    ]
    ancestors = [
        {"page_id": ancestor["id"], "title": ancestor.get("title", "")}
        for ancestor in page.get("ancestors", [])
        if ancestor.get("id")
    ]
    webui = page.get("_links", {}).get("webui", "")
    page_url = webui if webui.startswith("http") else f"{base_url}{webui}"

    return {
        "page_id": page["id"],
        "title": page["title"],
        "page_url": page_url,
        "space_key": page.get("space", {}).get("key"),
        "status": page.get("status"),
        "version": page.get("version", {}).get("number"),
        "last_modified": page.get("version", {}).get("when"),
        "ancestors": ancestors,
        "labels": labels,
        "raw_content_html": storage_html,
        "fetched_at": datetime.now(UTC).isoformat(),
        "content_sha256": hashlib.sha256(storage_html.encode("utf-8")).hexdigest(),
    }


def load_snapshot(page_id: str, output_directory: Path) -> dict | None:
    """Load an existing page snapshot when one has already been collected."""
    output_path = output_directory / f"{page_id}.json"
    if not output_path.is_file():
        return None
    return json.loads(output_path.read_text(encoding="utf-8"))


def page_changed_since_snapshot(remote_metadata: dict, snapshot: dict) -> bool:
    """Return whether Confluence reports a newer page version than the snapshot."""
    remote_version = remote_metadata.get("version", {}).get("number")
    saved_version = snapshot.get("version")

    if isinstance(remote_version, int) and isinstance(saved_version, int):
        return remote_version > saved_version

    remote_updated_at = remote_metadata.get("version", {}).get("when")
    fetched_at = snapshot.get("fetched_at")
    if not remote_updated_at or not fetched_at:
        return True

    try:
        remote_time = datetime.fromisoformat(remote_updated_at.replace("Z", "+00:00"))
        fetched_time = datetime.fromisoformat(fetched_at.replace("Z", "+00:00"))
    except ValueError:
        return True

    return remote_time > fetched_time


def save_snapshot(snapshot: dict, output_directory: Path, overwrite: bool) -> bool:
    """Write one UTF-8 JSON snapshot; return False when an existing file is skipped."""
    output_path = output_directory / f"{snapshot['page_id']}.json"
    if output_path.exists() and not overwrite:
        print(f"Skipped existing snapshot: {output_path.name}")
        return False

    output_path.write_text(
        json.dumps(snapshot, indent=2, ensure_ascii=False), encoding="utf-8"
    )
    print(f"Saved: {output_path.name} | {snapshot['title']}")
    return True


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Fetch selected Confluence pages into local JSON snapshots."
    )
    parser.add_argument("--page-id-file", type=Path, default=DEFAULT_PAGE_ID_FILE)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIRECTORY)
    parser.add_argument(
        "--overwrite",
        action="store_true",
        help="Replace existing JSON snapshots with freshly fetched page data.",
    )
    args = parser.parse_args()

    page_ids = read_page_ids(args.page_id_file)
    if not page_ids:
        raise ValueError("No page IDs found. Add one ID per line to the page ID file.")

    args.output_dir.mkdir(parents=True, exist_ok=True)
    client = ConfluenceClient(ConfluenceConfig.from_environment())
    saved_count = 0
    skipped_count = 0
    error_count = 0

    print(f"Collecting {len(page_ids)} configured Confluence page(s).")
    for position, page_id in enumerate(page_ids, start=1):
        print(f"Fetching {position}/{len(page_ids)}: page {page_id}")
        try:
            existing_snapshot = load_snapshot(page_id, args.output_dir)
            if existing_snapshot is not None and not args.overwrite:
                remote_metadata = client.get_page_metadata(page_id)
                if not page_changed_since_snapshot(remote_metadata, existing_snapshot):
                    skipped_count += 1
                    print("Skipped unchanged page.")
                    continue
                print("Page changed since the saved snapshot; fetching full content.")

            page = client.get_page(page_id)
            snapshot = normalize_page(page, client.config.base_url)
            replace_existing = args.overwrite or existing_snapshot is not None
            if save_snapshot(snapshot, args.output_dir, replace_existing):
                saved_count += 1
            else:
                skipped_count += 1
        except (HTTPError, URLError, ValueError) as error:
            error_count += 1
            print(f"Failed page {page_id}: {error}")

    print(
        f"Finished. Saved: {saved_count}; skipped: {skipped_count}; failed: {error_count}."
    )
    return 1 if error_count else 0


if __name__ == "__main__":
    raise SystemExit(main())
