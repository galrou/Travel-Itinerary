import math
from dataclasses import dataclass
from typing import Sequence

from itinerary_agent.domain import Restaurant
from itinerary_agent.models import Location


@dataclass(frozen=True)
class RestaurantPreferences:
    cuisine: str | None = None
    dietary: str | None = None
    price_tier: str | None = None
    named_restaurant: str | None = None


def _distance(a: Location, b: Location) -> float:
    return math.hypot(a.lat - b.lat, a.lon - b.lon)


def _nearest_distance(location: Location, others: Sequence[Location]) -> float:
    if not others:
        return 0.0
    return min(_distance(location, other) for other in others)


def _preference_score(restaurant: Restaurant, preferences: RestaurantPreferences) -> int:
    score = 0
    if preferences.cuisine and preferences.cuisine.lower() == restaurant.cuisine.lower():
        score += 1
    if preferences.dietary and preferences.dietary.lower() in {tag.lower() for tag in restaurant.dietary_tags}:
        score += 1
    if preferences.price_tier and preferences.price_tier.lower() == restaurant.price_tier.lower():
        score += 1
    return score


def _is_named_match(restaurant: Restaurant, preferences: RestaurantPreferences) -> bool:
    named = (preferences.named_restaurant or "").strip().lower()
    return bool(named) and restaurant.name.strip().lower() == named


def rank_restaurants(
    candidates: Sequence[Restaurant],
    preferences: RestaurantPreferences,
    nearby_activity_locations: Sequence[Location],
) -> list[Restaurant]:
    """Ranks by: a feasible named-restaurant request first (only "feasible"
    when it's actually among the researched candidates), then stated
    preference matches, proximity to the Day's other Activities, and review
    signal — ties broken deterministically by id."""

    def sort_key(restaurant: Restaurant) -> tuple[int, int, float, float, str]:
        return (
            0 if _is_named_match(restaurant, preferences) else 1,
            -_preference_score(restaurant, preferences),
            _nearest_distance(restaurant.location, nearby_activity_locations),
            -restaurant.review_signal,
            restaurant.id,
        )

    return sorted(candidates, key=sort_key)


def assign_restaurants_to_slots(
    candidates: Sequence[Restaurant],
    preferences: RestaurantPreferences,
    opted_in_slots: Sequence[str],
    nearby_activity_locations: Sequence[Location],
) -> dict[str, Restaurant]:
    """Fills only the opted-in meal Slots, each with a distinct Restaurant
    drawn from the ranked candidates; a slot is left unfilled if candidates
    run out before every opted-in slot has one."""
    ranked = rank_restaurants(candidates, preferences, nearby_activity_locations)
    assignment: dict[str, Restaurant] = {}
    used_ids: set[str] = set()
    for slot in opted_in_slots:
        for restaurant in ranked:
            if restaurant.id not in used_ids:
                assignment[slot] = restaurant
                used_ids.add(restaurant.id)
                break
    return assignment
