from pydantic import BaseModel, ConfigDict

from itinerary_agent.domain.constants import MEAL_SLOTS, Slot

_REQUIREMENT_GROUPS: tuple[tuple[str, tuple[str, ...]], ...] = (
    ("destination and hotel", ("destination", "hotel")),
    ("travel party size", ("party_size",)),
    ("budget", ("budget",)),
    ("arrival airport and time", ("arrival_airport", "arrival_time")),
    ("departure airport and time", ("departure_airport", "departure_time")),
    (
        "restaurant preferences for breakfast/lunch/dinner",
        ("breakfast_opt_in", "lunch_opt_in", "dinner_opt_in"),
    ),
)


class Requirements(BaseModel):
    """Values are parsed from free-form traveler text (see extraction.py),
    so this is a pydantic model rather than a plain dataclass: it's the one
    seam in the codebase where field values come from outside our control."""

    model_config = ConfigDict(frozen=True)

    destination: str | None = None
    hotel: str | None = None
    party_size: int | None = None
    budget: float | None = None
    arrival_airport: str | None = None
    arrival_time: str | None = None
    departure_airport: str | None = None
    departure_time: str | None = None
    breakfast_opt_in: bool | None = None
    lunch_opt_in: bool | None = None
    dinner_opt_in: bool | None = None
    restaurant_cuisine: str | None = None
    restaurant_dietary: str | None = None
    restaurant_price_tier: str | None = None
    named_restaurant: str | None = None

    def missing(self) -> list[str]:
        """Labels for each requirement group that has at least one unset field."""
        return [
            label
            for label, field_names in _REQUIREMENT_GROUPS
            if any(getattr(self, name) is None for name in field_names)
        ]

    def is_complete(self) -> bool:
        return not self.missing()

    def merged_with(self, update: "Requirements") -> "Requirements":
        """Fill gaps in `self` from `update`; an already-supplied field is never overwritten."""
        merged = {
            name: getattr(self, name) if getattr(self, name) is not None else getattr(update, name)
            for name in type(self).model_fields
        }
        return Requirements(**merged)

    def opted_in_meal_slots(self) -> list[Slot]:
        return [slot for slot in MEAL_SLOTS if getattr(self, f"{slot}_opt_in")]
