from dataclasses import dataclass
from typing import Sequence

from langchain_core.messages import AIMessage, BaseMessage, HumanMessage

from itinerary_agent.config import AllowedDomainsList
from itinerary_agent.constants import NODE_RESEARCH, ROUTE_END
from itinerary_agent.domain import ACTIVITY_SLOTS, Candidate, Day, Hotel, Leg, Requirements, Trip
from itinerary_agent.llm import (
    ActivityResearcher,
    RequirementsExtractor,
    RestaurantResearcher,
    filter_by_allowed_domains,
    select_top_activities,
)
from itinerary_agent.planning import RestaurantPreferences, RestaurantRanker, sequence_route
from itinerary_agent.state import ConversationState

ACTIVITIES_CATEGORY = "Activities"
RESTAURANTS_CATEGORY = "Restaurants/Reviews"
DAY_ACTIVITY_COUNT = len(ACTIVITY_SLOTS)


def _last_human_message(messages: Sequence[BaseMessage]) -> str | None:
    for message in reversed(messages):
        if isinstance(message, HumanMessage):
            return str(message.content)
    return None


def _summarize(destination: str, day: Day) -> str:
    parts = [f"{slot}: {activity.name}" for slot, activity in day.filled_slots()]
    return f"Here's your day in {destination} — " + "; ".join(parts) + "."


@dataclass(frozen=True)
class IntakeNodes:
    """The Requirements graph node: extracts and merges traveler-supplied
    details, asking only about what's still missing."""

    extractor: RequirementsExtractor

    def requirements(self, state: ConversationState) -> dict[str, object]:
        """Extracts whatever's newly supplied, merges it in without overwriting
        what's already known, and asks only about what's still missing."""
        message = _last_human_message(state["messages"])
        extracted = self.extractor.extract(message) if message is not None else Requirements()
        merged = state.get("requirements", Requirements()).merged_with(extracted)

        missing = merged.missing()
        if missing:
            question = "I still need: " + ", ".join(missing) + "."
            return {"requirements": merged, "messages": [AIMessage(content=question)]}
        return {"requirements": merged}

    def route_after_requirements(self, state: ConversationState) -> str:
        if state.get("requirements", Requirements()).is_complete():
            return NODE_RESEARCH
        return ROUTE_END


@dataclass(frozen=True)
class ActivityNodes:
    """The Research / Sequencing graph nodes: finds candidate Activities and
    orders them across the Day's non-meal Slots."""

    activity_researcher: ActivityResearcher
    allowed_domains: AllowedDomainsList

    def research(self, state: ConversationState) -> dict[str, object]:
        requirements = state["requirements"]
        domains = self.allowed_domains.domains_for(ACTIVITIES_CATEGORY)

        result = self.activity_researcher.research(requirements.destination or "", requirements.hotel or "", domains)
        gated = filter_by_allowed_domains(result.candidates, domains)
        top = select_top_activities(gated, DAY_ACTIVITY_COUNT)

        return {"candidates": top, "anchor": result.anchor}

    def sequence(self, state: ConversationState) -> dict[str, object]:
        """Orders the day's activities via Test Seam 2 (sequencing.sequence_route)
        anchored on the Hotel, then lays the route out across the non-meal Slots
        in order (first stop -> morning, ... -> evening). Meal Slots are left for
        the restaurant nodes to fill."""
        anchor = state["anchor"]
        activities = state["candidates"]
        assert anchor is not None, "sequence runs only after research has set an anchor"

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


@dataclass(frozen=True)
class RestaurantNodes:
    """The Restaurant Research / Selection graph nodes: finds candidate
    Restaurants and fills the Day's opted-in meal Slots."""

    restaurant_researcher: RestaurantResearcher
    allowed_domains: AllowedDomainsList

    def restaurant_research(self, state: ConversationState) -> dict[str, object]:
        """Skips research entirely when every meal Slot is opted out, rather than
        firing a Source lookup nothing will use."""
        requirements = state["requirements"]
        if not requirements.opted_in_meal_slots():
            return {"restaurant_candidates": []}

        domains = self.allowed_domains.domains_for(RESTAURANTS_CATEGORY)
        candidates = self.restaurant_researcher.research(requirements.destination or "", requirements.hotel or "", domains)
        gated = filter_by_allowed_domains(candidates, domains)
        return {"restaurant_candidates": gated}

    def restaurant_selection(self, state: ConversationState) -> dict[str, object]:
        """Fills only the opted-in meal Slots (Test Seam:
        restaurants.RestaurantRanker.assign_to_slots), ranked by preference match,
        proximity to the Day's other Activities, reviews, and a feasible
        named-restaurant request."""
        requirements = state["requirements"]
        day = state["day"]
        assert day is not None, "restaurant_selection runs only after sequence has set a day"

        opted_in = requirements.opted_in_meal_slots()
        nearby = [activity.location for _, activity in day.filled_slots(ACTIVITY_SLOTS)]
        preferences = RestaurantPreferences(
            cuisine=requirements.restaurant_cuisine,
            dietary=requirements.restaurant_dietary,
            price_tier=requirements.restaurant_price_tier,
            named_restaurant=requirements.named_restaurant,
        )
        ranker = RestaurantRanker(preferences=preferences, nearby_activity_locations=nearby)
        assignment = ranker.assign_to_slots(state["restaurant_candidates"], opted_in)
        for slot, restaurant in assignment.items():
            day.slots[slot] = restaurant

        return {"day": day}


def finalize(state: ConversationState) -> dict[str, object]:
    """Assembles the completed Day into a Trip and summarizes it back to the
    traveler."""
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
