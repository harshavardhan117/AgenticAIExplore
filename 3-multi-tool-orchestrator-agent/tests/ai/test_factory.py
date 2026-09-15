import pytest

from ai.claude_reviewer import ClaudeReviewer
from ai.factory import build_ai_reviewer
from ai.gemini_reviewer import GeminiReviewer


def test_defaults_to_gemini_when_unset(monkeypatch):
    monkeypatch.delenv("AI_PROVIDER", raising=False)

    reviewer = build_ai_reviewer()

    assert isinstance(reviewer._inner, GeminiReviewer)


def test_reads_provider_from_env(monkeypatch):
    monkeypatch.setenv("AI_PROVIDER", "claude")

    reviewer = build_ai_reviewer()

    assert isinstance(reviewer._inner, ClaudeReviewer)


def test_explicit_argument_overrides_env(monkeypatch):
    monkeypatch.setenv("AI_PROVIDER", "gemini")

    reviewer = build_ai_reviewer("claude")

    assert isinstance(reviewer._inner, ClaudeReviewer)


def test_unknown_provider_raises():
    with pytest.raises(ValueError, match="Unknown AI provider"):
        build_ai_reviewer("not-a-real-provider")
