"""Build the LLM prompt from already retrieved Confluence evidence."""

from rag.models import RetrievedChunk


class PromptBuilder:
    """Keep grounding instructions and source formatting in one obvious place."""

    def build(self, question: str, results: list[RetrievedChunk]) -> str:
        """Create a source-only prompt with stable citation labels."""

        sources = "\n\n".join(
            (
                f"[Source {result.rank}]\n"
                f"Page title: {result.citation.page_title}\n"
                f"Page URL: {result.citation.page_url}\n"
                f"Section: {result.heading_path}\n"
                f"Content:\n{result.content}"
            )
            for result in results
        )
        return (
            "You are a Confluence documentation assistant. Answer only from the "
            "retrieved sources below. Do not use outside knowledge or invent details. "
            "If the sources do not support an answer, say: 'I cannot answer reliably "
            "from the retrieved Confluence documentation.' Cite every factual claim using the "
            "matching label, for example [Source 1].\n\n"
            f"Question:\n{question}\n\nRetrieved sources:\n{sources}"
        )
