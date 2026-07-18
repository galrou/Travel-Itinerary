from itinerary_agent.domain import Requirements


def test_all_fields_missing_lists_every_requirement_group():
    missing = Requirements().missing()

    assert missing == [
        "destination and hotel",
        "travel party size",
        "budget",
        "arrival airport and time",
        "departure airport and time",
        "restaurant preferences for breakfast/lunch/dinner",
    ]


def test_a_group_is_missing_if_any_of_its_fields_is_unset():
    req = Requirements(destination="Paris")  # hotel still unset

    assert "destination and hotel" in req.missing()


def test_a_group_is_present_once_every_field_in_it_is_set():
    req = Requirements(destination="Paris", hotel="Hotel Lutetia")

    assert "destination and hotel" not in req.missing()


def test_is_complete_true_only_when_nothing_is_missing():
    incomplete = Requirements(destination="Paris", hotel="Hotel Lutetia")
    complete = Requirements(
        destination="Paris",
        hotel="Hotel Lutetia",
        party_size=2,
        budget=2000,
        arrival_airport="CDG",
        arrival_time="10:00",
        departure_airport="CDG",
        departure_time="18:00",
        breakfast_opt_in=False,
        lunch_opt_in=True,
        dinner_opt_in=True,
    )

    assert incomplete.is_complete() is False
    assert complete.is_complete() is True


def test_restaurant_group_is_missing_unless_every_meal_slot_has_an_explicit_opt_in_or_out():
    only_two_answered = Requirements(breakfast_opt_in=False, lunch_opt_in=True)

    assert "restaurant preferences for breakfast/lunch/dinner" in only_two_answered.missing()


def test_restaurant_group_is_present_once_every_meal_slot_is_explicitly_opted_in_or_out():
    all_opted_out = Requirements(breakfast_opt_in=False, lunch_opt_in=False, dinner_opt_in=False)

    assert "restaurant preferences for breakfast/lunch/dinner" not in all_opted_out.missing()


def test_merge_fills_restaurant_preference_fields_without_overwriting_supplied_ones():
    existing = Requirements(named_restaurant="Le Comptoir")
    update = Requirements(restaurant_cuisine="French", named_restaurant="Some Other Place")

    merged = existing.merged_with(update)

    assert merged.named_restaurant == "Le Comptoir"  # not overwritten
    assert merged.restaurant_cuisine == "French"  # filled in


def test_merge_fills_gaps_but_never_overwrites_an_already_supplied_field():
    existing = Requirements(destination="Paris", hotel="Hotel Lutetia")
    update = Requirements(destination="Rome", party_size=2)

    merged = existing.merged_with(update)

    assert merged.destination == "Paris"  # not overwritten by the new turn
    assert merged.hotel == "Hotel Lutetia"
    assert merged.party_size == 2  # filled in from the new turn
