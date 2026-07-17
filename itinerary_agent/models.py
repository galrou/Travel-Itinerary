from dataclasses import dataclass


@dataclass(frozen=True)
class Location:
    lat: float
    lon: float


@dataclass(frozen=True)
class Candidate:
    id: str
    slot: str
    location: Location
    price: float
