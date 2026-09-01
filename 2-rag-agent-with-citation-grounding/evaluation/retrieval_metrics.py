"""Pure retrieval-quality metric calculations for Confluence RAG experiments."""


def hit_at_k(expected_source_urls: list[str], retrieved_source_urls: list[str]) -> bool:
    """Return true when any expected source appears among the retrieved top-K sources."""

    expected = {_normalize_url(url) for url in expected_source_urls}
    retrieved = {_normalize_url(url) for url in retrieved_source_urls}
    return bool(expected & retrieved)


def reciprocal_rank_at_k(expected_source_urls: list[str], retrieved_source_urls: list[str]) -> float:
    """Return 1/rank for the first expected source, or zero when it is absent."""

    expected = {_normalize_url(url) for url in expected_source_urls}
    for rank, url in enumerate(retrieved_source_urls, start=1):
        if _normalize_url(url) in expected:
            return 1.0 / rank
    return 0.0


def _normalize_url(url: str) -> str:
    """Avoid treating an otherwise identical trailing slash as a retrieval miss."""

    return url.strip().rstrip("/")
