"""Claude implementation of the AIReviewer contract."""

import os

import anthropic

from ai.base import AIReviewer
from ai.prompt import build_prompt, parse_response
from domain.models import AIReviewInput, AIReviewOutput

_MODEL = "claude-opus-5"


class ClaudeReviewer(AIReviewer):
    """Lazily creates one Claude client on first use, then reuses it."""

    def __init__(self) -> None:
        self._client: anthropic.Anthropic | None = None

    def _get_client(self) -> anthropic.Anthropic:
        if self._client is None:
            api_key = os.environ["ANTHROPIC_API_KEY"]
            self._client = anthropic.Anthropic(api_key=api_key)
        return self._client

    def chat(self, review_input: AIReviewInput) -> AIReviewOutput:
        client = self._get_client()
        prompt = build_prompt(review_input)
        message = client.messages.create(
            model=_MODEL,
            max_tokens=4096,
            messages=[{"role": "user", "content": prompt}],
        )
        raw_text = message.content[0].text
        return parse_response(raw_text)
