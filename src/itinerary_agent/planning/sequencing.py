from itertools import permutations
from typing import Sequence

from itinerary_agent.domain import Candidate, Location


def _round_trip_length(anchor: Location, route: Sequence[Candidate]) -> float:
    points = [anchor, *(candidate.location for candidate in route), anchor]
    return sum(points[i].distance_to(points[i + 1]) for i in range(len(points) - 1))


def sequence_route(candidates: Sequence[Candidate], anchor: Location) -> list[Candidate]:
    """Order candidates into the shortest round trip that starts and ends at anchor."""
    best_route: tuple[Candidate, ...] = tuple(candidates)
    best_length = _round_trip_length(anchor, best_route)
    for route in permutations(candidates):
        length = _round_trip_length(anchor, route)
        if length < best_length:
            best_route, best_length = route, length
    return list(best_route)
