from dataclasses import dataclass, field
from typing import Sequence

from itinerary_agent.domain import Requirements, Restaurant
from itinerary_agent.llm import ActivityResearchResult


@dataclass
class FakeLLMClient:
    """An LLMClient test double: returns a scripted response regardless of
    input. Used to unit-test LLMRequirementsExtractor itself, distinct from
    ScriptedExtractor which fakes the whole RequirementsExtractor seam for
    graph-level tests."""

    response: str = "{}"

    def complete(self, *, system: str, user: str) -> str:
        return self.response


@dataclass
class ScriptedExtractor:
    """A RequirementsExtractor test double: looks up the exact message text
    in a script rather than actually parsing natural language."""

    script: dict[str, Requirements]

    def extract(self, message: str) -> Requirements:
        return self.script.get(message, Requirements())


@dataclass
class FixtureResearcher:
    """An ActivityResearcher test double standing in for the Activities
    Source Category's fixture data."""

    result: ActivityResearchResult

    def research(self, destination: str, hotel: str, allowed_domains: Sequence[str]) -> ActivityResearchResult:
        return self.result


@dataclass
class FixtureRestaurantResearcher:
    """A RestaurantResearcher test double standing in for the
    Restaurants/Reviews Source Category's fixture data."""

    candidates: list[Restaurant] = field(default_factory=list)

    def research(self, destination: str, hotel: str, allowed_domains: Sequence[str]) -> list[Restaurant]:
        return self.candidates
