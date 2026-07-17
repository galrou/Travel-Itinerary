from typing import Protocol

from itinerary_agent.requirements import Requirements


class RequirementsExtractor(Protocol):
    def extract(self, message: str) -> Requirements:
        """Return whichever Requirements fields can be read out of `message`,
        leaving anything not mentioned as None."""
        ...
