from dataclasses import dataclass, field
from typing import Sequence

from itinerary_agent.domain.constants import SLOT_NAMES, Slot
from itinerary_agent.domain.models import Location


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

    def filled_slots(self, slots: Sequence[Slot] = SLOT_NAMES) -> list[tuple[Slot, Activity]]:
        return [(slot, activity) for slot in slots if (activity := self.slots[slot]) is not None]


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
