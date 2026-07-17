from dataclasses import dataclass, fields


@dataclass(frozen=True)
class Requirements:
    destination: str | None = None
    hotel: str | None = None
    party_size: int | None = None
    budget: float | None = None
    arrival_airport: str | None = None
    arrival_time: str | None = None
    departure_airport: str | None = None
    departure_time: str | None = None


_REQUIREMENT_GROUPS: tuple[tuple[str, tuple[str, ...]], ...] = (
    ("destination and hotel", ("destination", "hotel")),
    ("travel party size", ("party_size",)),
    ("budget", ("budget",)),
    ("arrival airport and time", ("arrival_airport", "arrival_time")),
    ("departure airport and time", ("departure_airport", "departure_time")),
)


def missing_requirements(requirements: Requirements) -> list[str]:
    """Labels for each requirement group that has at least one unset field."""
    return [
        label
        for label, field_names in _REQUIREMENT_GROUPS
        if any(getattr(requirements, name) is None for name in field_names)
    ]


def is_complete(requirements: Requirements) -> bool:
    return not missing_requirements(requirements)


def merge_requirements(existing: Requirements, update: Requirements) -> Requirements:
    """Fill gaps in `existing` from `update`; an already-supplied field is never overwritten."""
    merged = {
        field.name: getattr(existing, field.name)
        if getattr(existing, field.name) is not None
        else getattr(update, field.name)
        for field in fields(Requirements)
    }
    return Requirements(**merged)
