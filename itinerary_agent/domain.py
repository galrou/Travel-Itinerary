from dataclasses import dataclass, field
from typing import Literal

from itinerary_agent.models import Location

Slot = Literal["breakfast", "morning", "lunch", "afternoon", "dinner", "evening"]

SLOT_NAMES: tuple[Slot, ...] = ("breakfast", "morning", "lunch", "afternoon", "dinner", "evening")
ACTIVITY_SLOTS: tuple[Slot, ...] = ("morning", "afternoon", "evening")
MEAL_SLOTS: tuple[Slot, ...] = ("breakfast", "lunch", "dinner")


@dataclass(frozen=True)
class Activity:
    id: str
    name: str
    location: Location
    price: float
    source_domain: str
    review_signal: float


@dataclass(frozen=True)
class Restaurant(Activity):
    """A specialized Activity that fills a meal Slot, ranked additionally by
    cuisine/dietary/price-tier preference match (see restaurants.py)."""

    cuisine: str = ""
    dietary_tags: tuple[str, ...] = ()
    price_tier: str = ""


@dataclass(frozen=True)
class Hotel:
    name: str
    location: Location


@dataclass
class Day:
    slots: dict[Slot, Activity | None] = field(default_factory=lambda: {name: None for name in SLOT_NAMES})


@dataclass
class Leg:
    destination: str
    hotel: Hotel
    days: list[Day] = field(default_factory=list)


@dataclass
class Trip:
    legs: list[Leg]
    party_size: int
    budget: float
    arrival_airport: str
    arrival_time: str
    departure_airport: str
    departure_time: str
