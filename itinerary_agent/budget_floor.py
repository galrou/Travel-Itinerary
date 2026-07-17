from dataclasses import dataclass
from typing import Sequence

from itinerary_agent.models import Candidate


@dataclass(frozen=True)
class BudgetFloorResult:
    combination: dict[str, Candidate]
    total_cost: float
    fits_budget: bool


def find_budget_floor(candidates: Sequence[Candidate], budget: float) -> BudgetFloorResult:
    """The cheapest feasible combination (one candidate per slot), checked
    exhaustively against every supplied candidate for every slot."""
    cheapest_per_slot: dict[str, Candidate] = {}
    for candidate in candidates:
        current = cheapest_per_slot.get(candidate.slot)
        if current is None or candidate.price < current.price:
            cheapest_per_slot[candidate.slot] = candidate

    total_cost = sum(candidate.price for candidate in cheapest_per_slot.values())
    return BudgetFloorResult(
        combination=cheapest_per_slot,
        total_cost=total_cost,
        fits_budget=total_cost <= budget,
    )
