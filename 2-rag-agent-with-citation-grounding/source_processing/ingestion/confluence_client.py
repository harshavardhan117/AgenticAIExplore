"""Small Confluence Data Center client used by the ingestion workflow."""

from __future__ import annotations

import json
import os
import time
from dataclasses import dataclass
from base64 import b64encode
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen


@dataclass(frozen=True)
class ConfluenceConfig:
    """Connection settings loaded from environment variables."""

    base_url: str
    token: str
    auth_mode: str
    email: str
    request_delay_seconds: float
    max_retries: int
    initial_backoff_seconds: float

    @classmethod
    def from_environment(cls) -> "ConfluenceConfig":
        """Load required Confluence settings without persisting the token."""
        return cls(
            base_url=cls._required("CONFLUENCE_BASE_URL").rstrip("/"),
            token=cls._required("CONFLUENCE_TOKEN"),
            auth_mode=os.getenv("CONFLUENCE_AUTH_MODE", "bearer").strip().lower(),
            email=os.getenv("CONFLUENCE_EMAIL", "").strip(),
            request_delay_seconds=float(
                os.getenv("CONFLUENCE_REQUEST_DELAY_SECONDS", "0.5")
            ),
            max_retries=int(os.getenv("CONFLUENCE_MAX_RETRIES", "3")),
            initial_backoff_seconds=float(
                os.getenv("CONFLUENCE_INITIAL_BACKOFF_SECONDS", "1")
            ),
        )

    @staticmethod
    def _required(variable_name: str) -> str:
        value = os.getenv(variable_name)
        if not value or not value.strip():
            raise ValueError(f"Missing required environment variable: {variable_name}")
        return value.strip()


class ConfluenceClient:
    """Fetch page JSON from a Confluence Data Center REST API."""

    def __init__(self, config: ConfluenceConfig) -> None:
        self.config = config
        self._last_request_started_at: float | None = None

    def get_page(self, page_id: str) -> dict:
        """Fetch one page, including storage-format content and citation metadata."""
        expand = "body.storage,version,space,ancestors,metadata.labels"
        return self._get_json(
            f"{self.config.base_url}/rest/api/content/{page_id}?expand={expand}"
        )

    def get_page_metadata(self, page_id: str) -> dict:
        """Fetch only the lightweight version metadata used for change detection."""
        return self._get_json(
            f"{self.config.base_url}/rest/api/content/{page_id}?expand=version"
        )

    def _authorization_header(self) -> str:
        if self.config.auth_mode == "bearer":
            return f"Bearer {self.config.token}"
        if self.config.auth_mode == "basic":
            if not self.config.email:
                raise ValueError("CONFLUENCE_EMAIL is required for basic authentication.")
            credentials = f"{self.config.email}:{self.config.token}".encode()
            return f"Basic {b64encode(credentials).decode()}"
        raise ValueError('CONFLUENCE_AUTH_MODE must be "bearer" or "basic".')

    def _get_json(self, url: str) -> dict:
        request = Request(
            url,
            headers={"Accept": "application/json", "Authorization": self._authorization_header()},
        )

        for attempt in range(self.config.max_retries + 1):
            self._wait_for_request_slot()
            self._last_request_started_at = time.monotonic()
            try:
                with urlopen(request, timeout=30) as response:
                    return json.load(response)
            except HTTPError as error:
                should_retry = error.code == 429 or 500 <= error.code < 600
                if not should_retry or attempt == self.config.max_retries:
                    raise
                self._sleep_before_retry(error.code, attempt, error.headers.get("Retry-After"))
            except URLError as error:
                if attempt == self.config.max_retries:
                    raise
                self._sleep_before_retry(f"network error: {error.reason}", attempt, None)

        raise RuntimeError("Unreachable retry state.")

    def _wait_for_request_slot(self) -> None:
        if self._last_request_started_at is None:
            return
        elapsed = time.monotonic() - self._last_request_started_at
        delay = self.config.request_delay_seconds - elapsed
        if delay > 0:
            time.sleep(delay)

    def _sleep_before_retry(
        self,
        reason: object,
        attempt: int,
        retry_after: str | None,
    ) -> None:
        delay = (
            float(retry_after)
            if retry_after and retry_after.isdigit()
            else self.config.initial_backoff_seconds * (2**attempt)
        )
        print(
            f"Retrying after {reason}; waiting {delay:.1f}s "
            f"({attempt + 1}/{self.config.max_retries})."
        )
        time.sleep(delay)
