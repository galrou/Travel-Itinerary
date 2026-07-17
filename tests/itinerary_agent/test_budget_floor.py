from itinerary_agent.budget_floor import find_budget_floor
from itinerary_agent.models import Candidate, Location

ANYWHERE = Location(lat=0, lon=0)


def _candidate(id: str, slot: str, price: float) -> Candidate:
    return Candidate(id=id, slot=slot, location=ANYWHERE, price=price)


def test_picks_the_cheapest_candidate_per_slot_and_sums_them():
    candidates = [
        _candidate("b1", "breakfast", 10),
        _candidate("b2", "breakfast", 5),
        _candidate("b3", "breakfast", 8),
        _candidate("l1", "lunch", 20),
        _candidate("l2", "lunch", 15),
    ]

    result = find_budget_floor(candidates, budget=25)

    assert result.combination["breakfast"].id == "b2"
    assert result.combination["lunch"].id == "l2"
    assert result.total_cost == 20
    assert result.fits_budget is True


def test_reports_the_floor_even_when_it_still_exceeds_the_budget():
    candidates = [
        _candidate("b1", "breakfast", 10),
        _candidate("b2", "breakfast", 5),
        _candidate("l1", "lunch", 20),
        _candidate("l2", "lunch", 15),
    ]

    result = find_budget_floor(candidates, budget=10)

    assert result.combination["breakfast"].id == "b2"
    assert result.combination["lunch"].id == "l2"
    assert result.total_cost == 20
    assert result.fits_budget is False


def test_finds_the_true_minimum_even_when_it_is_buried_in_a_large_list():
    # 50 decoy candidates all priced higher than the one true minimum, which
    # sits last in the list — a first-match or early-exit implementation
    # would miss it.
    decoys = [_candidate(f"decoy{i}", "dinner", price=100 + i) for i in range(50)]
    true_cheapest = _candidate("actual-cheapest", "dinner", price=12)

    result = find_budget_floor([*decoys, true_cheapest], budget=1000)

    assert result.combination["dinner"].id == "actual-cheapest"
    assert result.total_cost == 12
