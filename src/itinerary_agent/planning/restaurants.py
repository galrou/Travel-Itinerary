from dataclasses import dataclass
from typing import NamedTuple, Sequence

from itinerary_agent.domain import Location, Restaurant, Slot


class _SortKey(NamedTuple):
    named_match: int
    preference_score: int
    distance: float
    review_signal: float
    id: str


@dataclass(frozen=True)
class RestaurantPreferences:
    cuisine: str | None = None
    dietary: str | None = None
    price_tier: str | None = None
    named_restaurant: str | None = None


def _nearest_distance(location: Location, others: Sequence[Location]) -> float:
    if not others:
        return 0.0
    return min(location.distance_to(other) for other in others)


@dataclass(frozen=True)
class RestaurantRanker:
    preferences: RestaurantPreferences
    nearby_activity_locations: Sequence[Location]

    def _preference_score(self, restaurant: Restaurant) -> int:
        score = 0
        preferences = self.preferences
        if preferences.cuisine and preferences.cuisine.lower() == restaurant.cuisine.lower():
            score += 1
        if preferences.dietary and preferences.dietary.lower() in {tag.lower() for tag in restaurant.dietary_tags}:
            score += 1
        if preferences.price_tier and preferences.price_tier.lower() == restaurant.price_tier.lower():
            score += 1
        return score

    def _is_named_match(self, restaurant: Restaurant) -> bool:
        named = (self.preferences.named_restaurant or "").strip().lower()
        return bool(named) and restaurant.name.strip().lower() == named

    def rank(self, candidates: Sequence[Restaurant]) -> list[Restaurant]:
        """Ranks by: a feasible named-restaurant request first (only "feasible"
        when it's actually among the researched candidates), then stated
        preference matches, proximity to the Day's other Activities, and review
        signal — ties broken deterministically by id."""

        def sort_key(restaurant: Restaurant) -> _SortKey:
            return _SortKey(
                named_match=0 if self._is_named_match(restaurant) else 1,
                preference_score=-self._preference_score(restaurant),
                distance=_nearest_distance(restaurant.location, self.nearby_activity_locations),
                review_signal=-restaurant.review_signal,
                id=restaurant.id,
            )

        return sorted(candidates, key=sort_key)

    def assign_to_slots(self, candidates: Sequence[Restaurant], opted_in_slots: Sequence[Slot]) -> dict[Slot, Restaurant]:
        """Fills only the opted-in meal Slots, each with a distinct Restaurant
        drawn from the ranked candidates; a slot is left unfilled if candidates
        run out before every opted-in slot has one."""
        ranked = self.rank(candidates)
        assignment: dict[Slot, Restaurant] = {}
        used_ids: set[str] = set()
        for slot in opted_in_slots:
            for restaurant in ranked:
                if restaurant.id not in used_ids:
                    assignment[slot] = restaurant
                    used_ids.add(restaurant.id)
                    break
        return assignment
