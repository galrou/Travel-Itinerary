import json
from dataclasses import dataclass, fields
from typing import Protocol

from itinerary_agent.llm import LLMClient
from itinerary_agent.requirements import Requirements


class RequirementsExtractor(Protocol):
    """The LLM-backed seam for turning free text into structured Requirements.
    Real implementation: LLMRequirementsExtractor below. Tests mock this with
    a scripted fake instead (see tests/itinerary_agent/fakes.py::ScriptedExtractor)."""

    def extract(self, message: str) -> Requirements:
        """Return whichever Requirements fields can be read out of `message`,
        leaving anything not mentioned as None."""
        ...


_REQUIREMENTS_FIELDS = tuple(field.name for field in fields(Requirements))

_SYSTEM_PROMPT = (
    "You extract trip-planning details from a traveler's message. "
    "Respond with a single JSON object with exactly these keys: "
    + ", ".join(_REQUIREMENTS_FIELDS)
    + ". Set a key to null if the message doesn't mention it — never guess. "
    "Respond with only the JSON object, no other text."
)


@dataclass
class LLMRequirementsExtractor:
    """Real RequirementsExtractor: prompts an LLMClient to pull whichever
    Requirements fields are readable out of the message, leaving the rest
    None. A malformed or unparseable response degrades to Requirements()
    rather than raising, matching this seam's missing-value-safe contract
    (see requirements.merge_requirements/missing_requirements)."""

    llm: LLMClient

    def extract(self, message: str) -> Requirements:
        raw = self.llm.complete(system=_SYSTEM_PROMPT, user=message)
        return _parse_requirements(raw)


def _parse_requirements(raw: str) -> Requirements:
    try:
        data = json.loads(raw)
    except json.JSONDecodeError:
        return Requirements()
    if not isinstance(data, dict):
        return Requirements()
    known_fields = set(_REQUIREMENTS_FIELDS)
    filtered = {key: value for key, value in data.items() if key in known_fields}
    try:
        return Requirements(**filtered)
    except TypeError:
        return Requirements()
