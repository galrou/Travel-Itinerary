from typing import Sequence

from langchain_core.messages import AIMessage, BaseMessage, HumanMessage

from itinerary_agent.domain import ACTIVITY_SLOTS, MEAL_SLOTS, SLOT_NAMES, Activity, Day, Hotel, Leg, Slot, Trip
from itinerary_agent.extraction import RequirementsExtractor
from itinerary_agent.models import Candidate
from itinerary_agent.requirements import Requirements, is_complete, merge_requirements, missing_requirements
from itinerary_agent.research import (
    ActivityResearcher,
    RestaurantResearcher,
    filter_by_allowed_domains,
    select_top_activities,
)
from itinerary_agent.restaurants import RestaurantPreferences, assign_restaurants_to_slots
from itinerary_agent.sequencing import sequence_route
from itinerary_agent.sources import AllowedDomainsList
from itinerary_agent.state import ConversationState

ACTIVITIES_CATEGORY = "Activities"
RESTAURANTS_CATEGORY = "Restaurants/Reviews"
DAY_ACTIVITY_COUNT = len(ACTIVITY_SLOTS)


def _last_human_message(messages: Sequence[BaseMessage]) -> str | None:
    for message in reversed(messages):
        if isinstance(message, HumanMessage):
            return str(message.content)
    return None


def make_requirements_node(extractor: RequirementsExtractor):
    """Extracts whatever's newly supplied, merges it in without overwriting
    what's already known, and asks only about what's still missing."""

    def requirements_node(state: ConversationState) -> dict[str, object]:
        message = _last_human_message(state["messages"])
        extracted = extractor.extract(message) if message is not None else Requirements()
        merged = merge_requirements(state.get("requirements", Requirements()), extracted)

        missing = missing_requirements(merged)
        if missing:
            question = "I still need: " + ", ".join(missing) + "."
            return {"requirements": merged, "messages": [AIMessage(content=question)]}
        return {"requirements": merged}

    return requirements_node


def route_after_requirements(state: ConversationState) -> str:
    if is_complete(state.get("requirements", Requirements())):
        return "research"
    return "end"


def make_research_node(researcher: ActivityResearcher, allowed_domains: AllowedDomainsList):
    def research_node(state: ConversationState) -> dict[str, object]:
        requirements = state["requirements"]
        domains = allowed_domains.domains_for(ACTIVITIES_CATEGORY)

        result = researcher.research(requirements.destination or "", requirements.hotel or "", domains)
        gated = filter_by_allowed_domains(result.candidates, domains)
        top = select_top_activities(gated, DAY_ACTIVITY_COUNT)

        return {"candidates": top, "anchor": result.anchor}

    return research_node


def make_sequencing_node():
    """Orders the day's activities via Test Seam 2 (sequencing.sequence_route)
    anchored on the Hotel, then lays the route out across the non-meal Slots
    in order (first stop -> morning, ... -> evening). Meal Slots are left for
    the restaurant nodes to fill."""

    def sequencing_node(state: ConversationState) -> dict[str, object]:
        anchor = state["anchor"]
        activities = state["candidates"]
        assert anchor is not None, "sequencing_node runs only after research_node has set an anchor"

        as_candidates = [
            Candidate(id=activity.id, slot="activity", location=activity.location, price=activity.price)
            for activity in activities
        ]
        ordered = sequence_route(as_candidates, anchor)
        by_id = {activity.id: activity for activity in activities}

        day = Day()
        for slot_name, candidate in zip(ACTIVITY_SLOTS, ordered):
            day.slots[slot_name] = by_id[candidate.id]

        return {"day": day}

    return sequencing_node


def _filled_slots(day: Day, slots: Sequence[Slot]) -> list[tuple[Slot, Activity]]:
    return [(slot, activity) for slot in slots if (activity := day.slots[slot]) is not None]


def _opted_in_meal_slots(requirements: Requirements) -> list[Slot]:
    opt_in_by_slot: dict[Slot, bool | None] = {
        "breakfast": requirements.breakfast_opt_in,
        "lunch": requirements.lunch_opt_in,
        "dinner": requirements.dinner_opt_in,
    }
    return [slot for slot in MEAL_SLOTS if opt_in_by_slot[slot]]


def make_restaurant_research_node(researcher: RestaurantResearcher, allowed_domains: AllowedDomainsList):
    """Skips research entirely when every meal Slot is opted out, rather than
    firing a Source lookup nothing will use."""

    def restaurant_research_node(state: ConversationState) -> dict[str, object]:
        requirements = state["requirements"]
        if not _opted_in_meal_slots(requirements):
            return {"restaurant_candidates": []}

        domains = allowed_domains.domains_for(RESTAURANTS_CATEGORY)
        candidates = researcher.research(requirements.destination or "", requirements.hotel or "", domains)
        gated = filter_by_allowed_domains(candidates, domains)
        return {"restaurant_candidates": gated}

    return restaurant_research_node


def make_restaurant_selection_node():
    """Fills only the opted-in meal Slots (Test Seam:
    restaurants.assign_restaurants_to_slots), ranked by preference match,
    proximity to the Day's other Activities, reviews, and a feasible
    named-restaurant request."""

    def restaurant_selection_node(state: ConversationState) -> dict[str, object]:
        requirements = state["requirements"]
        day = state["day"]
        assert day is not None, "restaurant_selection_node runs only after sequencing_node has set a day"

        opted_in = _opted_in_meal_slots(requirements)
        nearby = [activity.location for _, activity in _filled_slots(day, ACTIVITY_SLOTS)]
        preferences = RestaurantPreferences(
            cuisine=requirements.restaurant_cuisine,
            dietary=requirements.restaurant_dietary,
            price_tier=requirements.restaurant_price_tier,
            named_restaurant=requirements.named_restaurant,
        )
        assignment = assign_restaurants_to_slots(state["restaurant_candidates"], preferences, opted_in, nearby)
        for slot, restaurant in assignment.items():
            day.slots[slot] = restaurant

        return {"day": day}

    return restaurant_selection_node


def make_finalize_node():
    """Assembles the completed Day into a Trip and summarizes it back to the
    traveler."""

    def finalize_node(state: ConversationState) -> dict[str, object]:
        requirements = state["requirements"]
        anchor = state["anchor"]
        day = state["day"]
        assert anchor is not None and day is not None

        trip = Trip(
            legs=[
                Leg(
                    destination=requirements.destination or "",
                    hotel=Hotel(name=requirements.hotel or "", location=anchor),
                    days=[day],
                )
            ],
            party_size=requirements.party_size or 0,
            budget=requirements.budget or 0.0,
            arrival_airport=requirements.arrival_airport or "",
            arrival_time=requirements.arrival_time or "",
            departure_airport=requirements.departure_airport or "",
            departure_time=requirements.departure_time or "",
        )

        summary = _summarize(requirements.destination or "this trip", day)
        return {"trip": trip, "messages": [AIMessage(content=summary)]}

    return finalize_node


def _summarize(destination: str, day: Day) -> str:
    parts = [f"{slot}: {activity.name}" for slot, activity in _filled_slots(day, SLOT_NAMES)]
    return f"Here's your day in {destination} — " + "; ".join(parts) + "."
