"""Runs the itinerary agent graph end-to-end against local, in-memory fixture
data — no network calls, no API keys, nothing beyond what tickets 01-03
actually wired up. Prints the conversation and the resulting Trip so the
whole pipeline can be eyeballed outside of pytest.

    python scripts/run_mock_itinerary.py
"""

import sys
import uuid
from dataclasses import dataclass, field
from pathlib import Path
from typing import Sequence

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from langchain_core.messages import HumanMessage
from langgraph.checkpoint.memory import InMemorySaver

from itinerary_agent.config import load_allowed_domains
from itinerary_agent.domain import SLOT_NAMES, Activity, Location, Requirements, Restaurant, Trip
from itinerary_agent.graph import build_graph
from itinerary_agent.llm import ActivityResearchResult

FIRST_MESSAGE = "We're headed to Lisbon and staying at Hotel Alfama, just the two of us."
SECOND_MESSAGE = (
    "Budget is 1800, arriving LIS at 11:00, departing LIS at 19:00. Skip breakfast, but we'd love lunch and "
    "dinner recommendations — Portuguese, mid-range, and work in Cervejaria Ramiro if you can."
)

ANCHOR = Location(lat=38.71, lon=-9.14)


@dataclass
class ScriptedExtractor:
    """A RequirementsExtractor stand-in: looks up the exact message text in a
    script rather than actually parsing natural language."""

    script: dict[str, Requirements]

    def extract(self, message: str) -> Requirements:
        return self.script.get(message, Requirements())


@dataclass
class FixtureResearcher:
    """An ActivityResearcher stand-in for the Activities Source Category's
    fixture data."""

    result: ActivityResearchResult

    def research(self, destination: str, hotel: str, allowed_domains: Sequence[str]) -> ActivityResearchResult:
        return self.result


@dataclass
class FixtureRestaurantResearcher:
    """A RestaurantResearcher stand-in for the Restaurants/Reviews Source
    Category's fixture data."""

    candidates: list[Restaurant] = field(default_factory=list)

    def research(self, destination: str, hotel: str, allowed_domains: Sequence[str]) -> list[Restaurant]:
        return self.candidates


def _activity(id: str, name: str, lat: float, lon: float, domain: str, signal: float) -> Activity:
    return Activity(
        id=id, name=name, location=Location(lat=lat, lon=lon), price=20.0, source_domain=domain, review_signal=signal
    )


def _restaurant(
    id: str, name: str, lat: float, lon: float, domain: str, cuisine: str, price_tier: str, signal: float
) -> Restaurant:
    return Restaurant(
        id=id,
        name=name,
        location=Location(lat=lat, lon=lon),
        price=30.0,
        source_domain=domain,
        review_signal=signal,
        cuisine=cuisine,
        dietary_tags=(),
        price_tier=price_tier,
    )


def _build_app():
    extractor = ScriptedExtractor(
        script={
            FIRST_MESSAGE: Requirements(destination="Lisbon", hotel="Hotel Alfama", party_size=2),
            SECOND_MESSAGE: Requirements(
                budget=1800,
                arrival_airport="LIS",
                arrival_time="11:00",
                departure_airport="LIS",
                departure_time="19:00",
                breakfast_opt_in=False,
                lunch_opt_in=True,
                dinner_opt_in=True,
                restaurant_cuisine="Portuguese",
                restaurant_price_tier="mid",
                named_restaurant="Cervejaria Ramiro",
            ),
        }
    )

    activity_candidates = [
        _activity("belem_tower", "Belem Tower", 38.69, -9.22, "tripadvisor.com", 4.8),
        _activity("sao_jorge", "Sao Jorge Castle", 38.71, -9.13, "lonelyplanet.com", 4.9),
        _activity("lx_factory", "LX Factory", 38.70, -9.18, "viator.com", 4.2),
        _activity("decoy_activity", "Suspiciously Perfect Tour", 38.72, -9.10, "untrusted-blog.com", 5.0),
    ]
    activity_researcher = FixtureResearcher(
        result=ActivityResearchResult(anchor=ANCHOR, candidates=activity_candidates)
    )

    restaurant_candidates = [
        _restaurant("cervejaria_ramiro", "Cervejaria Ramiro", 38.72, -9.14, "yelp.com", "Portuguese", "mid", 3.5),
        _restaurant("taberna", "Taberna Portuguesa", 38.71, -9.14, "opentable.com", "Portuguese", "mid", 4.9),
        _restaurant("cantina", "Cantina Lisboa", 38.70, -9.15, "thefork.com", "Portuguese", "mid", 4.6),
        _restaurant("decoy_restaurant", "Too-Good Bistro", 38.71, -9.14, "untrusted-blog.com", "Portuguese", "mid", 5.0),
    ]
    restaurant_researcher = FixtureRestaurantResearcher(candidates=restaurant_candidates)

    app = build_graph(extractor, activity_researcher, restaurant_researcher, load_allowed_domains(), InMemorySaver())
    config = {"configurable": {"thread_id": str(uuid.uuid4())}}
    return app, config


def _render_trip(trip: Trip) -> str:
    leg = trip.legs[0]
    day = leg.days[0]
    lines = [
        f"Destination: {leg.destination}",
        f"Hotel: {leg.hotel.name}",
        f"Party size: {trip.party_size}",
        f"Budget: {trip.budget}",
        f"Arrival: {trip.arrival_airport} at {trip.arrival_time}",
        f"Departure: {trip.departure_airport} at {trip.departure_time}",
        "",
    ]
    for slot in SLOT_NAMES:
        activity = day.slots[slot]
        lines.append(f"  {slot:<10}: {activity.name if activity else '—'}")
    return "\n".join(lines)


def main() -> None:
    sys.stdout.reconfigure(encoding="utf-8")
    app, config = _build_app()

    print("=== Turn 1 ===")
    print(f"Human: {FIRST_MESSAGE}")
    result = app.invoke({"messages": [HumanMessage(content=FIRST_MESSAGE)]}, config=config)
    print(f"Agent: {result['messages'][-1].content}")
    assert result.get("trip") is None, "requirements should still be incomplete after turn 1"

    print("\n=== Turn 2 ===")
    print(f"Human: {SECOND_MESSAGE}")
    result = app.invoke({"messages": [HumanMessage(content=SECOND_MESSAGE)]}, config=config)
    print(f"Agent: {result['messages'][-1].content}")

    trip = result.get("trip")
    assert trip is not None, "requirements were complete — finalize_node should have produced a Trip"

    print("\n=== Final Trip ===")
    print(_render_trip(trip))


if __name__ == "__main__":
    main()
