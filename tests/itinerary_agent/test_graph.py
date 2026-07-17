import uuid

from fakes import FixtureResearcher, ScriptedExtractor
from langchain_core.messages import HumanMessage
from langgraph.checkpoint.memory import InMemorySaver

from itinerary_agent.domain import Activity
from itinerary_agent.graph import build_graph
from itinerary_agent.models import Location
from itinerary_agent.requirements import Requirements
from itinerary_agent.research import ActivityResearchResult
from itinerary_agent.sources import AllowedDomainsList, SourceCategory

FIRST_MESSAGE = "We're headed to Paris and staying at Hotel Lutetia, just the two of us."
SECOND_MESSAGE = "Budget is 2000, arriving CDG at 10:00, departing CDG at 18:00."

ANCHOR = Location(lat=48.85, lon=2.35)


def _allowed_domains() -> AllowedDomainsList:
    return AllowedDomainsList(
        categories={"Activities": SourceCategory(name="Activities", domains=("trusted.com",))}
    )


def _activity(id: str, lat: float, lon: float, domain: str = "trusted.com", signal: float = 4.0) -> Activity:
    return Activity(
        id=id, name=id, location=Location(lat=lat, lon=lon), price=20.0, source_domain=domain, review_signal=signal
    )


def _build_app():
    extractor = ScriptedExtractor(
        script={
            FIRST_MESSAGE: Requirements(destination="Paris", hotel="Hotel Lutetia", party_size=2),
            SECOND_MESSAGE: Requirements(
                budget=2000,
                arrival_airport="CDG",
                arrival_time="10:00",
                departure_airport="CDG",
                departure_time="18:00",
            ),
        }
    )
    candidates = [
        _activity("louvre", 48.86, 2.34, signal=4.8),
        _activity("eiffel", 48.86, 2.29, signal=4.9),
        _activity("orsay", 48.86, 2.32, signal=4.2),
        _activity("decoy", 48.9, 2.9, domain="untrusted.com", signal=5.0),
    ]
    researcher = FixtureResearcher(result=ActivityResearchResult(anchor=ANCHOR, candidates=candidates))
    app = build_graph(extractor, researcher, _allowed_domains(), InMemorySaver())
    config = {"configurable": {"thread_id": str(uuid.uuid4())}}
    return app, config


def test_first_turn_asks_only_for_the_still_missing_requirements():
    app, config = _build_app()

    result = app.invoke({"messages": [HumanMessage(content=FIRST_MESSAGE)]}, config=config)

    question = result["messages"][-1].content.lower()
    assert "budget" in question
    assert "arrival airport and time" in question
    assert "departure airport and time" in question
    assert "destination and hotel" not in question
    assert "travel party size" not in question
    assert result.get("trip") is None


def test_second_turn_completes_requirements_and_produces_a_sequenced_hotel_anchored_day():
    app, config = _build_app()
    app.invoke({"messages": [HumanMessage(content=FIRST_MESSAGE)]}, config=config)

    result = app.invoke({"messages": [HumanMessage(content=SECOND_MESSAGE)]}, config=config)

    trip = result["trip"]
    assert trip is not None
    assert trip.party_size == 2
    assert trip.budget == 2000

    leg = trip.legs[0]
    assert leg.destination == "Paris"
    assert leg.hotel.name == "Hotel Lutetia"
    assert leg.hotel.location == ANCHOR

    day = leg.days[0]
    assert day.slots["breakfast"] is None
    assert day.slots["lunch"] is None
    assert day.slots["dinner"] is None

    filled_ids = {day.slots[slot].id for slot in ("morning", "afternoon", "evening")}
    assert filled_ids == {"louvre", "eiffel", "orsay"}  # untrusted decoy excluded despite higher signal


def test_requirements_are_never_re_asked_once_supplied():
    app, config = _build_app()

    first = app.invoke({"messages": [HumanMessage(content=FIRST_MESSAGE)]}, config=config)
    assert first["requirements"].destination == "Paris"
    assert first["requirements"].hotel == "Hotel Lutetia"
    assert first["requirements"].party_size == 2
