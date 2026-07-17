from pathlib import Path

from itinerary_agent.sources import AllowedDomainsList, SourceCategory, load_allowed_domains


def test_load_allowed_domains_reads_the_activities_category_from_config():
    allowed = load_allowed_domains()

    activities_domains = allowed.domains_for("Activities")

    assert len(activities_domains) > 0
    assert all(isinstance(domain, str) for domain in activities_domains)


def test_domains_for_an_unknown_category_is_empty():
    allowed = AllowedDomainsList(categories={"Activities": SourceCategory(name="Activities", domains=("a.com",))})

    assert allowed.domains_for("Restaurants") == ()


def test_load_allowed_domains_from_a_custom_path(tmp_path: Path):
    config = tmp_path / "allowed_domains.yaml"
    config.write_text(
        "categories:\n"
        "  Activities:\n"
        "    domains:\n"
        "      - example.com\n"
        "      - other.example.com\n"
    )

    allowed = load_allowed_domains(config)

    assert allowed.domains_for("Activities") == ("example.com", "other.example.com")
