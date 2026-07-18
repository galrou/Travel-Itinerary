from dataclasses import dataclass
from pathlib import Path

import yaml

DEFAULT_CONFIG_PATH = Path(__file__).parent / "allowed_domains.yaml"


@dataclass(frozen=True)
class SourceCategory:
    name: str
    domains: tuple[str, ...]


@dataclass(frozen=True)
class AllowedDomainsList:
    categories: dict[str, SourceCategory]

    def domains_for(self, category: str) -> tuple[str, ...]:
        found = self.categories.get(category)
        return found.domains if found is not None else ()


def load_allowed_domains(path: Path = DEFAULT_CONFIG_PATH) -> AllowedDomainsList:
    """Read the Allowed Domains List from a YAML config — new Sources are
    added there, not by changing research logic."""
    raw = yaml.safe_load(path.read_text()) or {}
    categories = {
        name: SourceCategory(name=name, domains=tuple(data.get("domains", [])))
        for name, data in raw.get("categories", {}).items()
    }
    return AllowedDomainsList(categories=categories)
