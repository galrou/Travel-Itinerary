# State-Driven Travel Itinerary Agent

Status: ready-for-agent

## Problem Statement

Travelers who have already booked their flights and hotel are left to manually stitch together what to actually *do* on the trip — researching attractions, restaurants, and reviews across many different websites, then figuring out a sensible day-by-day order that doesn't waste half the day crossing town. They can't easily tell which recommendations are trustworthy versus AI-hallucinated, and once they have a plan, tweaking one part of it (e.g. swapping a meal) means re-explaining the whole trip from scratch.

## Solution

Build a state-driven travel planning agent (a LangGraph state machine) that takes a traveler's already-booked logistics — Trip Legs, Hotel per Leg, Travel Party size, Budget, arrival/departure/transit details, and per-Slot restaurant preferences — and researches Activities and Restaurants exclusively from a category-scoped Allowed Domains List. It assembles the results into a Sequencing-optimized, meal-Slotted daily Itinerary for every Leg. The agent asks for missing Requirements before researching, persists the conversation via a Checkpointer so the traveler can give iterative feedback ("swap lunch for a cafe") without repeating themselves, and — when the stated Budget can't produce a valid Itinerary — proposes a Budget Floor instead of simply failing.

## User Stories

**Requirements gathering**

1. As a traveler, I want the agent to ask me for any missing Requirements (Trip Legs, Hotel per Leg, Travel Party size, Budget, arrival/departure Airport + time, inter-Leg Transit Point + time, per-Slot restaurant preferences) before it starts researching, so that the itinerary is grounded in my actual logistics rather than assumptions.
2. As a traveler, I want the agent to recognize when I've already provided a detail earlier in the conversation, so that I'm never asked for the same information twice.
3. As a traveler planning a multi-city trip, I want to specify a destination city and Hotel for each Leg separately, so that each city gets its own itinerary anchored to where I'm actually staying there.
4. As a traveler, I want to specify my Travel Party size (solo, couple, etc.), so that Budget and recommendations are framed correctly for my group.
5. As a traveler, I want to give my flight arrival/departure Airport and time, so that the agent knows how much of my first and last day is actually available.
6. As a traveler on a multi-city trip, I want to give the time and Transit Point for each move between cities, so that the transition day's schedule reflects how much time I actually have in each city.
7. As a traveler, I want to state my Budget once, understanding it only needs to cover Activities and Restaurants — not flights or hotel, which I've already booked.
8. As a traveler, I want to say upfront whether I want restaurant recommendations at all, and for which meals, so that I'm not served suggestions for meals I plan to handle myself.
9. As a traveler, I want to state cuisine/dietary/price-tier preferences and optionally name a specific restaurant I want worked in, so that restaurant recommendations reflect my actual taste.

**Research & source trust**

10. As a traveler, I want every Activity and Restaurant recommendation to come only from a curated Allowed Domains List, so that I can trust the recommendations and avoid AI-generated hallucinations.
11. As a developer, I want the Allowed Domains List organized into Source Categories (e.g. Activities, Restaurants/Reviews), so that I can add or vet a new source for one category without touching the others.
12. As a developer, I want to add a new Source to a category via a simple configuration change, so that I can expand research scope without modifying core agent logic.
13. As a traveler, I want Activities to be selected and ranked using real reviews and content from the Allowed Domains List, so that recommendations reflect genuine quality, not just factual existence.
14. As a traveler, I want Restaurant recommendations ranked by my stated preferences, proximity to that day's other Activities, and real reviews from the Allowed Domains List, so that meal suggestions actually fit my day and my taste.

**Itinerary structure & sequencing**

15. As a traveler, I want each Day of my itinerary structured around fixed meal-anchored Slots (breakfast, morning activity, lunch, afternoon activity, dinner, evening activity), so that the schedule reads like a coherent day rather than a loose list.
16. As a traveler, I want each Day's Activities sequenced to minimize backtracking between stops, not just picked for being near my Hotel, so that I spend my time seeing things, not commuting.
17. As a traveler, I want my Hotel to anchor the start and end of each regular Day's route, so that the plan realistically starts and ends where I'm staying.
18. As a traveler on my arrival or departure day, I want the schedule trimmed to what's actually possible given my flight time, so that I'm not given a full day when I land at 6pm.
19. As a traveler on an arrival, departure, or inter-Leg transition day, I want the route to anchor at the Airport/Transit Point instead of my Hotel where appropriate, so that an activity near the airport can be scheduled before I ever reach my hotel.
20. As a traveler with a multi-city trip, I want each Leg's Days sequenced independently around that Leg's own Hotel, so that switching cities doesn't confuse the geographic plan.

**Budget**

21. As a traveler, I want the agent to reject combinations of Activities/Restaurants that exceed my Budget, so that the plan I get is one I can actually afford.
22. As a traveler whose Budget is too low for any valid itinerary, I want the agent to propose the cheapest itinerary it can build instead of just failing, so that I have something actionable.
23. As a traveler being told "there's no cheaper option," I want that claim backed by an exhaustive check of every available Activity/Restaurant for every Slot, so that I can trust it's actually the floor and not just whatever happened to be fetched.

**Feedback & persistence**

24. As a traveler, I want to give follow-up feedback like "swap lunch for a cafe" and have just that Slot change, so that I can refine my itinerary without re-describing the whole trip.
25. As a traveler, I want the agent to remember my Requirements and current Itinerary across turns via the Checkpointer, so that I never have to repeat my initial inputs.
26. As a traveler, I understand that feedback mutates my one Itinerary in place; I don't need to browse or restore earlier versions of the plan.

**Developer / architecture**

27. As a developer, I want the agent built as a LangGraph state machine using composition over inheritance, so that node logic stays modular and easy to extend.
28. As a developer, I want a pure, LLM-free function for Sequencing and Budget Floor search, so that the trickiest algorithmic logic (route ordering, cheapest-combination search) can be unit tested deterministically without mocking research or an LLM.

## Implementation Decisions

- State model follows `CONTEXT.md`: Trip > Leg > Day > Slot > Activity, where Restaurant is a specialized Activity that fills a meal Slot.
- Requirements extraction is a distinct phase/node from research; the graph must be able to halt and re-prompt the user when Requirements are incomplete, rather than guessing defaults.
- The Allowed Domains List is structured as Source Categories (at minimum: Activities, Restaurants/Reviews), each independently configurable — a new Source is added to a category's list, not to one flat global list.
- Sequencing and Budget Floor search are implemented as deterministic, LLM-free functions operating over candidate Activities (each with a location and price). Keep them free of I/O so they can run against fixtures — this is the boundary for Test Seam 2 below.
- Per ADR-0001: the Itinerary is a single evolving object in the Checkpointer's persisted state; no version history is modeled or exposed. Feedback (e.g. "swap lunch for a cafe") mutates the current Itinerary and is written back via the same Checkpointer thread.
- Per ADR-0002: the top-level state models Trip > Leg > Day from the outset — even a single-city trip is a Trip with one Leg. Both the Trip's overall arrival/departure and every inter-Leg transition produce a Travel Day, but only the overall arrival/departure is Airport-specific (IATA-based); inter-Leg transit uses the more general Transit Point.
- Budget is a single ceiling for the whole Travel Party across the entire Trip, covering Activities/Restaurants only — flights and hotel are out of scope. Costs are presented framed to the party size (e.g. "price for couple") rather than always broken out per traveler.
- Restaurant recommendations support independent per-meal-Slot opt-out — never an all-or-nothing toggle.
- Test Seam 1 (primary): the compiled LangGraph app invoked for one conversation turn — accumulated state + new user message in, updated state out (either a refined Itinerary or a clarifying question about missing Requirements).
- Test Seam 2 (secondary, pure logic): a standalone Sequencing/Budget-Floor function taking candidate Activities (location + price) and returning the ordered Day / the cheapest feasible combination, with no LLM or network dependency.

## Testing Decisions

- Good tests here exercise external behavior only — assert on what the seam returns, never on which internal node ran or in what order.
- **Seam 1 (graph invocation):** drive full conversational turns with mocked Source responses (fixture data standing in for each Allowed Domains List category) and assert on: which Requirements get asked for when missing, the resulting Itinerary structure, Budget Floor proposals when the stated Budget is infeasible, and in-place mutation of a single Slot after feedback.
- **Seam 2 (Sequencing / Budget Floor):** pure unit tests with fixture lists of candidate Activities (location + price), asserting on the resulting route order and the resulting cheapest feasible combination — no LLM, no mocked network calls, no graph involved.
- No prior art exists in this repo for either seam — the existing `graph.py` / `nodes.py` / `state.py` / `services/` / `tools/` belong to an unrelated project (per explicit developer direction during domain modeling) and should not be used as a pattern to imitate or extend.

## Out of Scope

- Booking or evaluating flights and hotels (the traveler has already booked these).
- Version history, undo, or diffing of past Itinerary states (ADR-0001).
- Payment processing.
- Real-time availability or booking of Activities or Restaurants (recommendations only, not transactions).

## Further Notes

- `CONTEXT.md` and `docs/adr/0001-itinerary-has-no-version-history.md` / `docs/adr/0002-itinerary-models-multi-city-trips-from-the-start.md` are the canonical vocabulary and architectural decisions for this feature; keep implementation consistent with them.
- The existing repo code (`graph.py`, `nodes.py`, `state.py`, `services/`, `tools/`, `main.py`) is an unrelated project per explicit developer direction and should be disregarded when implementing this spec — do not extend or pattern-match against it.