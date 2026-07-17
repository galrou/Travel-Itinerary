from itinerary_agent.requirements import Requirements, is_complete, merge_requirements, missing_requirements


def test_all_fields_missing_lists_every_requirement_group():
    missing = missing_requirements(Requirements())

    assert missing == [
        "destination and hotel",
        "travel party size",
        "budget",
        "arrival airport and time",
        "departure airport and time",
    ]


def test_a_group_is_missing_if_any_of_its_fields_is_unset():
    req = Requirements(destination="Paris")  # hotel still unset

    assert "destination and hotel" in missing_requirements(req)


def test_a_group_is_present_once_every_field_in_it_is_set():
    req = Requirements(destination="Paris", hotel="Hotel Lutetia")

    assert "destination and hotel" not in missing_requirements(req)


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
    )

    assert is_complete(incomplete) is False
    assert is_complete(complete) is True


def test_merge_fills_gaps_but_never_overwrites_an_already_supplied_field():
    existing = Requirements(destination="Paris", hotel="Hotel Lutetia")
    update = Requirements(destination="Rome", party_size=2)

    merged = merge_requirements(existing, update)

    assert merged.destination == "Paris"  # not overwritten by the new turn
    assert merged.hotel == "Hotel Lutetia"
    assert merged.party_size == 2  # filled in from the new turn
