"""Gemini implementation of the AIReviewer contract."""

import os

from google import genai

from ai.base import AIReviewer
from ai.prompt import build_prompt, parse_response
from domain.models import AIReviewInput, AIReviewOutput

_MODEL = "gemini-3.6-flash"


class GeminiReviewer(AIReviewer):
    """Lazily creates one Gemini client on first use, then reuses it."""

    def __init__(self) -> None:
        self._client: genai.Client | None = None

    def _get_client(self) -> genai.Client:
        if self._client is None:
            api_key = os.environ["GEMINI_API_KEY"]
            self._client = genai.Client(api_key=api_key)
        return self._client

    def chat(self, review_input: AIReviewInput) -> AIReviewOutput:
        client = self._get_client()
        prompt = build_prompt(review_input)
        chat = client.chats.create(model=_MODEL)
        response = chat.send_message(prompt)
        return parse_response(response.text)
