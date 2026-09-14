"""AI reviewer strategy interface — one implementation per model provider."""

from abc import ABC, abstractmethod

from domain.models import AIReviewInput, AIReviewOutput


class AIReviewer(ABC):
    """Contract every AI provider adapter (Claude, Gemini, ...) must implement."""

    @abstractmethod
    def chat(self, review_input: AIReviewInput) -> AIReviewOutput:
        """Send deterministic findings to the model and return its review.

        Implementations own their own auth and client setup. Must raise on
        failure (auth, network, bad response) rather than returning a partial
        or empty result — the orchestrator catches the exception and falls
        back to deterministic-only output.
        """
