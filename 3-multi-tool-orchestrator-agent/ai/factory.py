"""Factory: builds the configured AIReviewer implementation. Default: Gemini."""

import os

from ai.base import AIReviewer
from ai.claude_reviewer import ClaudeReviewer
from ai.gemini_reviewer import GeminiReviewer
from ai.logging_reviewer import LoggingAIReviewer

_PROVIDERS: dict[str, type[AIReviewer]] = {
    "gemini": GeminiReviewer,
    "claude": ClaudeReviewer,
}


def build_ai_reviewer(provider: str | None = None) -> AIReviewer:
    """Picks a provider explicitly, else reads AI_PROVIDER env var, else defaults to Gemini."""
    name = (provider or os.environ.get("AI_PROVIDER") or "gemini").lower()

    try:
        reviewer_cls = _PROVIDERS[name]
    except KeyError:
        raise ValueError(f"Unknown AI provider '{name}'. Choose one of: {', '.join(_PROVIDERS)}") from None

    return LoggingAIReviewer(reviewer_cls())
