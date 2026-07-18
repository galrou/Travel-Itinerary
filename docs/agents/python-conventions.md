# Python Conventions

Coding conventions for this repo, distilled from review sessions. Apply these
without being asked; only deviate with a documented reason (an ADR, or a
comment explaining the exception).

## No magic strings/values across files

If a literal (a string, a number) is used in more than one file, it gets a
name. A value repeated across files with no shared name is one rename away
from silently drifting apart — e.g. a node name returned by a router
function and the same name hardcoded in the graph wiring that consumes it.

## Constants live at the narrowest folder that needs them

When a constant is used by more than one file **within the same folder**,
extract it to a `constants.py` in that folder rather than letting one file
own it and the others reach in. Import it from there in every file that
needs it, including the file that used to define it.

Use `constants.py`, not `config.py` — `config` is reserved in this repo for
runtime-loaded configuration (e.g. `config/sources.py` +
`allowed_domains.yaml`, the Allowed Domains List). `constants.py` is for
compile-time Python values with no external source. Keeping the names
distinct keeps "what's configurable at runtime" separate from "what's fixed
in code."

If a value is only used by one file, it stays local to that file — don't
pre-emptively promote something to `constants.py` before a second file
needs it.

## `__init__.py` files are not placeholders

Every package's `__init__.py` re-exports that package's public API (plus an
explicit `__all__`), so external code imports from the package root —
`from itinerary_agent.domain import Location` — rather than reaching into
the submodule that happens to define it —
`from itinerary_agent.domain.models import Location`. The submodule split
inside a package (`entities.py` vs `models.py` vs `requirements.py`) is an
implementation detail; the package boundary is the actual public surface.

Two exceptions, both about avoiding a package importing itself:
- **Within a package**, files import each other directly by submodule path
  (`domain/entities.py` imports `from itinerary_agent.domain.models import
  Location`, not `from itinerary_agent.domain import Location`) — routing
  through `__init__.py` from inside the same package risks a circular
  import back through that `__init__.py`.
- A package's own `__init__.py` naturally imports its submodules directly
  (that's what it's re-exporting).

## Turn a family of closures into a class

When several free functions return closures over overlapping sets of the
same collaborators (`make_x_node(a, b)`, `make_y_node(b, c)`, ...), that's a
Data Clump: the collaborators are a group that wants to be constructor
state. Replace the factory functions with one class holding the
collaborators as fields, and turn each closure into a bound method. This
cuts the boilerplate at every call site and gives the collaborators one
place to be constructed instead of one per factory call.

## Folder structure: layer by architectural role, not by feature

Group modules by their place in the dependency graph — pure domain entities,
pure algorithms with no I/O, LLM/network-backed code, runtime config,
orchestration — rather than by feature/ticket. This repo's tickets already
draw an explicit line between "pure, LLM-free, I/O-free" (Test Seam 2:
`planning/`) and "LLM-backed" (`llm/`) code; a by-feature split would bury
that boundary. Feature-based ("vertical slice") packaging was considered and
rejected here specifically because the domain entities (`Activity`, `Day`,
`Trip`, ...) are genuinely shared across every feature, so slicing by
feature would just create heavy cross-imports.

Current layering in `itinerary_agent`:

```
domain/      entities + business rules, zero I/O (models, entities, requirements, constants)
planning/    pure algorithms, no LLM/network calls (sequencing, budget_floor, restaurants)
llm/         LLM-backed seam (client, extraction, research)
config/      runtime configuration (sources, allowed_domains.yaml)
graph.py, nodes.py, state.py   orchestration — the one layer allowed to depend on all the others
```

## `src/` layout: package only, not tests or scripts

The installable package lives under `src/<package_name>/`. `tests/` and
`scripts/` are **siblings** of `src/` at the repo root, not nested inside
it — `src/` means "what gets built into the package," and tests/dev scripts
aren't part of that. Run `pip install -e .` once so `import <package_name>`
resolves to the `src/` copy rather than silently picking up a stray copy
elsewhere on `sys.path`.

## Every public function gets a return type hint

Including factory functions and functions returning a closure — a function
returning `Callable[[X], Y]` still gets that annotation written out, not
left implicit.

## Verify after every change

Run the test suite (and `mypy` where configured) after each edit, not just
at the end of a batch of changes. A refactor that "should" be behavior
preserving still gets verified — the verification is what makes it safe to
call finished.
