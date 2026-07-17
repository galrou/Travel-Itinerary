import uuid

from fakes import FixtureRestaurantResearcher, FixtureResearcher, ScriptedExtractor
from langchain_core.messages import HumanMessage
from langgraph.checkpoint.memory import InMemorySaver

from itinerary_agent.domain import Activity, Restaurant
from itinerary_agent.graph import build_graph
from itinerary_agent.models import Location
from itinerary_agent.requirements import Requirements
from itinerary_agent.research import ActivityResearchResult
from itinerary_agent.sources import AllowedDomainsList, SourceCategory

FIRST_MESSAGE = "We're headed to Paris and staying at Hotel Lutetia, just the two of us."
SECOND_MESSAGE = "Budget is 2000, arriving CDG at 10:00, departing CDG at 18:00. No restaurant recommendations."

RESTAURANT_FIRST_MESSAGE = "We're headed to Rome and staying at Hotel Forum, just the two of us."
RESTAURANT_SECOND_MESSAGE = (
    "Budget is 1500, arriving FCO at 09:00, departing FCO at 20:00. Skip breakfast, but we'd love lunch and "
    "dinner recommendations — Italian, mid-range, and work in Trattoria Da Enzo if you can."
)

ANCHOR = Location(lat=48.85, lon=2.35)


def _allowed_domains() -> AllowedDomainsList:
    return AllowedDomainsList(
        categories={
            "Activities": SourceCategory(name="Activities", domains=("trusted.com",)),
            "Restaurants/Reviews": SourceCategory(name="Restaurants/Reviews", domains=("trusted.com",)),
        }
    )


def _activity(id: str, lat: float, lon: float, domain: str = "trusted.com", signal: float = 4.0) -> Activity:
    return Activity(
        id=id, name=id, location=Location(lat=lat, lon=lon), price=20.0, source_domain=domain, review_signal=signal
    )


def _restaurant(
    id: str,
    lat: float,
    lon: float,
    domain: str = "trusted.com",
    cuisine: str = "Italian",
    price_tier: str = "mid",
    signal: float = 4.0,
    name: str | None = None,
) -> Restaurant:
    return Restaurant(
        id=id,
        name=name or id,
        location=Location(lat=lat, lon=lon),
        price=30.0,
        source_domain=domain,
        review_signal=signal,
        cuisine=cuisine,
        dietary_tags=(),
        price_tier=price_tier,
    )


def _build_app(restaurant_candidates: list[Restaurant] | None = None):
    extractor = ScriptedExtractor(
        script={
            FIRST_MESSAGE: Requirements(destination="Paris", hotel="Hotel Lutetia", party_size=2),
            SECOND_MESSAGE: Requirements(
                budget=2000,
                arrival_airport="CDG",
                arrival_time="10:00",
                departure_airport="CDG",
                departure_time="18:00",
                breakfast_opt_in=False,
                lunch_opt_in=False,
                dinner_opt_in=False,
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
    restaurant_researcher = FixtureRestaurantResearcher(candidates=restaurant_candidates or [])
    app = build_graph(extractor, researcher, restaurant_researcher, _allowed_domains(), InMemorySaver())
    config = {"configurable": {"thread_id": str(uuid.uuid4())}}
    return app, config


def _build_restaurant_app():
    extractor = ScriptedExtractor(
        script={
            RESTAURANT_FIRST_MESSAGE: Requirements(destination="Rome", hotel="Hotel Forum", party_size=2),
            RESTAURANT_SECOND_MESSAGE: Requirements(
                budget=1500,
                arrival_airport="FCO",
                arrival_time="09:00",
                departure_airport="FCO",
                departure_time="20:00",
                breakfast_opt_in=False,
                lunch_opt_in=True,
                dinner_opt_in=True,
                restaurant_cuisine="Italian",
                restaurant_price_tier="mid",
                named_restaurant="Trattoria Da Enzo",
            ),
        }
    )
    activity_candidates = [
        _activity("colosseum", 41.89, 12.49, signal=4.8),
        _activity("forum", 41.89, 12.48, signal=4.9),
        _activity("pantheon", 41.9, 12.48, signal=4.2),
    ]
    activity_researcher = FixtureResearcher(
        result=ActivityResearchResult(anchor=Location(lat=41.9, lon=12.49), candidates=activity_candidates)
    )
    restaurant_candidates = [
        _restaurant("trattoria", 41.9, 12.49, name="Trattoria Da Enzo", signal=3.0),
        _restaurant("osteria", 41.9, 12.49, signal=4.9),
        _restaurant("bistro", 41.9, 12.49, signal=4.5),
        _restaurant("decoy", 41.9, 12.49, domain="untrusted.com", signal=5.0),
    ]
    restaurant_researcher = FixtureRestaurantResearcher(candidates=restaurant_candidates)
    app = build_graph(extractor, activity_researcher, restaurant_researcher, _allowed_domains(), InMemorySaver())
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
    assert "restaurant preferences" in question
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


def test_mixed_opt_in_and_opt_out_meal_slots_are_filled_only_where_opted_in():
    app, config = _build_restaurant_app()
    app.invoke({"messages": [HumanMessage(content=RESTAURANT_FIRST_MESSAGE)]}, config=config)

    result = app.invoke({"messages": [HumanMessage(content=RESTAURANT_SECOND_MESSAGE)]}, config=config)

    day = result["trip"].legs[0].days[0]

    assert day.slots["breakfast"] is None  # opted out

    lunch, dinner = day.slots["lunch"], day.slots["dinner"]
    assert lunch is not None
    assert dinner is not None
    assert lunch.id != dinner.id  # distinct restaurants per opted-in slot
    assert lunch.source_domain == "trusted.com"  # untrusted decoy excluded despite higher signal
    assert dinner.source_domain == "trusted.com"

    # Feasible named-restaurant request is honored ahead of the higher-reviewed alternatives.
    assert "Trattoria Da Enzo" in {lunch.name, dinner.name}
