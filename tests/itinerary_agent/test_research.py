from itinerary_agent.domain import Activity, Location
from itinerary_agent.llm import filter_by_allowed_domains, select_top_activities

ANYWHERE = Location(lat=0, lon=0)


def _activity(id: str, domain: str = "trusted.com", signal: float = 1.0) -> Activity:
    return Activity(id=id, name=id, location=ANYWHERE, price=10, source_domain=domain, review_signal=signal)


def test_filter_by_allowed_domains_drops_candidates_outside_the_list():
    candidates = [
        _activity("a", domain="trusted.com"),
        _activity("b", domain="untrusted.com"),
    ]

    result = filter_by_allowed_domains(candidates, allowed_domains=["trusted.com"])

    assert [c.id for c in result] == ["a"]


def test_select_top_activities_ranks_by_review_signal_not_arrival_order():
    candidates = [
        _activity("low", signal=2.0),
        _activity("high", signal=4.9),
        _activity("mid", signal=3.5),
    ]

    result = select_top_activities(candidates, count=2)

    assert [c.id for c in result] == ["high", "mid"]


def test_select_top_activities_never_returns_more_than_available():
    candidates = [_activity("only", signal=1.0)]

    result = select_top_activities(candidates, count=3)

    assert [c.id for c in result] == ["only"]


def test_select_top_activities_breaks_ties_deterministically_by_id():
    candidates = [_activity("b", signal=5.0), _activity("a", signal=5.0)]

    result = select_top_activities(candidates, count=2)

    assert [c.id for c in result] == ["a", "b"]
