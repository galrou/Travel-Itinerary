"""ActivityResearcher and RestaurantResearcher are the LLM-backed seam for
turning allowed-domain Source content into structured candidates: the real
implementation reads raw page/review content and extracts fields like
review_signal by judgment, not just structured-API passthrough. No real
implementation exists yet — tests mock these with fixed fakes (see
tests/itinerary_agent/fakes.py::FixtureResearcher / FixtureRestaurantResearcher).

Future consideration: retrieval over a pre-indexed allowed-domain corpus
(RAG) is a candidate implementation strategy alongside live per-request
agentic browsing — not decided yet."""

from dataclasses import dataclass
from typing import Protocol, Sequence

from itinerary_agent.domain import Activity, Restaurant
from itinerary_agent.models import Location


@dataclass(frozen=True)
class ActivityResearchResult:
    anchor: Location
    candidates: list[Activity]


class ActivityResearcher(Protocol):
    def research(
        self, destination: str, hotel: str, allowed_domains: Sequence[str]
    ) -> ActivityResearchResult: ...


class RestaurantResearcher(Protocol):
    def research(
        self, destination: str, hotel: str, allowed_domains: Sequence[str]
    ) -> list[Restaurant]:
        """No anchor to return: the Hotel location already comes from
        ActivityResearcher, and Restaurant ranking anchors on the Day's
        other Activities instead (see restaurants.rank_restaurants)."""
        ...


def filter_by_allowed_domains(
    candidates: Sequence[Activity], allowed_domains: Sequence[str]
) -> list[Activity]:
    """Enforce the Allowed Domains List gate, independent of whatever the
    researcher itself claims to have already filtered."""
    allowed = set(allowed_domains)
    return [candidate for candidate in candidates if candidate.source_domain in allowed]


def select_top_activities(candidates: Sequence[Activity], count: int) -> list[Activity]:
    """Rank by review/content signal, not just factual existence."""
    ranked = sorted(candidates, key=lambda candidate: (-candidate.review_signal, candidate.id))
    return ranked[:count]
