from dataclasses import dataclass
from typing import Sequence

from itinerary_agent.requirements import Requirements
from itinerary_agent.research import ActivityResearchResult


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
