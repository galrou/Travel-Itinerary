from typing import Protocol


class LLMClient(Protocol):
    """Provider-agnostic seam for a single-turn chat completion. Every
    LLM-backed Protocol implementation (RequirementsExtractor today, and any
    future ActivityResearcher/RestaurantResearcher/FeedbackInterpreter per
    ADR-0003) depends on this rather than a specific vendor SDK, so swapping
    providers or mocking in tests doesn't touch the extraction/research code."""

    def complete(self, *, system: str, user: str) -> str:
        """Return the model's raw text response to a single user turn."""
        ...
