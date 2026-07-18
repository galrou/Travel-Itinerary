from itinerary_agent.domain import Candidate, Location
from itinerary_agent.planning import sequence_route


def _square_candidates() -> tuple[Candidate, Candidate, Candidate]:
    a = Candidate(id="a", slot="morning", location=Location(lat=1, lon=0), price=0)
    b = Candidate(id="b", slot="lunch", location=Location(lat=1, lon=1), price=0)
    c = Candidate(id="c", slot="afternoon", location=Location(lat=0, lon=1), price=0)
    return a, b, c


def test_orders_a_square_around_the_anchor_instead_of_crossing_the_diagonal():
    # Anchor plus three corners of a unit square. The only two routes that
    # avoid crossing the diagonal are the perimeter walk in either direction
    # (total round-trip length 4); any order that crosses the square
    # (through the diagonal) is longer (~4.83), so this pins down the exact
    # expected order independently of how the implementation computes it.
    anchor = Location(lat=0, lon=0)
    a, b, c = _square_candidates()

    result = sequence_route([b, c, a], anchor)

    assert [candidate.id for candidate in result] in (["a", "b", "c"], ["c", "b", "a"])


def test_the_optimal_order_follows_the_anchor_coordinate_alone():
    # Same three candidates as above, but the anchor moves to break the
    # square's symmetry (to the right of it, off the diagonal axis). Hand
    # computation of all 6 round trips shows the shortest is now a[c]b /
    # b[c]a (~4.83) rather than the a/b/c perimeter walk (~5.24) from the
    # previous test — proving the order depends only on the anchor's
    # coordinate, with no special-cased notion of "hotel" or "airport".
    anchor = Location(lat=2, lon=0)
    a, b, c = _square_candidates()

    result = sequence_route([a, b, c], anchor)

    assert [candidate.id for candidate in result] in (["a", "c", "b"], ["b", "c", "a"])


def test_empty_candidates_returns_an_empty_route():
    assert sequence_route([], Location(lat=0, lon=0)) == []


def test_a_single_candidate_is_returned_alone():
    anchor = Location(lat=0, lon=0)
    only = Candidate(id="only", slot="lunch", location=Location(lat=5, lon=5), price=0)

    assert sequence_route([only], anchor) == [only]
