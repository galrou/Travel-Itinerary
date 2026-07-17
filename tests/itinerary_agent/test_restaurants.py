from itinerary_agent.domain import Restaurant
from itinerary_agent.models import Location
from itinerary_agent.restaurants import RestaurantPreferences, assign_restaurants_to_slots, rank_restaurants

ANYWHERE = Location(lat=0, lon=0)


def _restaurant(
    id: str,
    lat: float = 0,
    lon: float = 0,
    cuisine: str = "",
    dietary_tags: tuple[str, ...] = (),
    price_tier: str = "",
    signal: float = 1.0,
    name: str | None = None,
) -> Restaurant:
    return Restaurant(
        id=id,
        name=name or id,
        location=Location(lat=lat, lon=lon),
        price=20.0,
        source_domain="trusted.com",
        review_signal=signal,
        cuisine=cuisine,
        dietary_tags=dietary_tags,
        price_tier=price_tier,
    )


def test_rank_prefers_a_matching_cuisine_over_a_higher_review_signal():
    match = _restaurant("match", cuisine="Italian", signal=3.0)
    higher_signal = _restaurant("higher_signal", cuisine="Thai", signal=4.9)
    preferences = RestaurantPreferences(cuisine="Italian")

    result = rank_restaurants([higher_signal, match], preferences, nearby_activity_locations=[])

    assert result[0].id == "match"


def test_rank_prefers_the_restaurant_closer_to_the_days_other_activities():
    near = _restaurant("near", lat=0, lon=0)
    far = _restaurant("far", lat=10, lon=10)
    nearby_activities = [Location(lat=0, lon=0.1)]

    result = rank_restaurants([far, near], RestaurantPreferences(), nearby_activity_locations=nearby_activities)

    assert result[0].id == "near"


def test_rank_puts_a_feasible_named_restaurant_request_first_regardless_of_other_factors():
    named = _restaurant("named", name="Le Comptoir", cuisine="Thai", signal=1.0, lat=99, lon=99)
    better_on_paper = _restaurant("better", cuisine="French", signal=5.0, lat=0, lon=0)
    preferences = RestaurantPreferences(cuisine="French", named_restaurant="Le Comptoir")

    result = rank_restaurants(
        [better_on_paper, named], preferences, nearby_activity_locations=[Location(lat=0, lon=0)]
    )

    assert result[0].id == "named"


def test_rank_falls_back_to_normal_ranking_when_the_named_restaurant_is_not_among_candidates():
    only_option = _restaurant("only", cuisine="French", signal=2.0)
    preferences = RestaurantPreferences(named_restaurant="Restaurant That Was Never Researched")

    result = rank_restaurants([only_option], preferences, nearby_activity_locations=[])

    assert [r.id for r in result] == ["only"]


def test_rank_breaks_ties_deterministically_by_id():
    b = _restaurant("b", signal=5.0)
    a = _restaurant("a", signal=5.0)

    result = rank_restaurants([b, a], RestaurantPreferences(), nearby_activity_locations=[])

    assert [r.id for r in result] == ["a", "b"]


def test_assign_fills_only_the_opted_in_slots():
    candidates = [_restaurant("bagel"), _restaurant("bistro"), _restaurant("diner")]

    assignment = assign_restaurants_to_slots(
        candidates, RestaurantPreferences(), opted_in_slots=["lunch"], nearby_activity_locations=[]
    )

    assert set(assignment.keys()) == {"lunch"}


def test_assign_returns_an_empty_mapping_when_every_meal_is_opted_out():
    candidates = [_restaurant("bagel")]

    assignment = assign_restaurants_to_slots(
        candidates, RestaurantPreferences(), opted_in_slots=[], nearby_activity_locations=[]
    )

    assert assignment == {}


def test_assign_never_repeats_the_same_restaurant_across_two_opted_in_slots():
    best = _restaurant("best", signal=5.0)
    second_best = _restaurant("second", signal=4.0)

    assignment = assign_restaurants_to_slots(
        [best, second_best],
        RestaurantPreferences(),
        opted_in_slots=["lunch", "dinner"],
        nearby_activity_locations=[],
    )

    assert assignment["lunch"].id == "best"
    assert assignment["dinner"].id == "second"
    assert assignment["lunch"].id != assignment["dinner"].id


def test_assign_leaves_a_slot_unfilled_when_candidates_run_out():
    only_one = [_restaurant("only")]

    assignment = assign_restaurants_to_slots(
        only_one, RestaurantPreferences(), opted_in_slots=["breakfast", "lunch"], nearby_activity_locations=[]
    )

    assert set(assignment.keys()) == {"breakfast"}
