from fakes import FakeLLMClient

from itinerary_agent.extraction import LLMRequirementsExtractor
from itinerary_agent.requirements import Requirements


def test_extract_parses_valid_json_subset():
    llm = FakeLLMClient(response='{"destination": "Lisbon", "party_size": 2}')
    extractor = LLMRequirementsExtractor(llm=llm)

    result = extractor.extract("We're 2 people heading to Lisbon")

    assert result == Requirements(destination="Lisbon", party_size=2)


def test_extract_malformed_json_degrades_to_empty_requirements():
    llm = FakeLLMClient(response="not json")
    extractor = LLMRequirementsExtractor(llm=llm)

    assert extractor.extract("anything") == Requirements()


def test_extract_ignores_unknown_keys():
    llm = FakeLLMClient(response='{"destination": "Rome", "not_a_field": "whatever"}')
    extractor = LLMRequirementsExtractor(llm=llm)

    assert extractor.extract("Rome please") == Requirements(destination="Rome")


def test_extract_non_dict_json_degrades_to_empty_requirements():
    llm = FakeLLMClient(response="null")
    extractor = LLMRequirementsExtractor(llm=llm)

    assert extractor.extract("anything") == Requirements()
