import math
from dataclasses import dataclass


@dataclass(frozen=True)
class Location:
    lat: float
    lon: float

    def distance_to(self, other: "Location") -> float:
        return math.hypot(self.lat - other.lat, self.lon - other.lon)


@dataclass(frozen=True)
class Candidate:
    id: str
    slot: str
    location: Location
    price: float
