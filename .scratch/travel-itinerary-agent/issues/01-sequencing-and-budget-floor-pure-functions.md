# 01 — Sequencing & Budget Floor pure functions

**What to build:** A deterministic, LLM-free, I/O-free module (Test Seam 2) that two things depend on throughout the rest of this feature: (1) given a set of candidate Activities (each with a location and price) for a Day's Slots and an anchor point (Hotel, or Airport/Transit Point on a Travel Day), returns a Sequencing of those Activities that minimizes backtracking between consecutive stops — not just proximity to the anchor; (2) given candidate Activities/Restaurants per Slot and a Budget ceiling, returns the cheapest feasible combination that fits, and can only report "no cheaper option exists" after exhaustively checking every candidate for every Slot (the Budget Floor).

**Blocked by:** None — can start immediately.

**Status:** ready-for-agent

- [ ] Sequencing function takes candidate Activities (location + price) and an anchor point, returns an ordered route minimizing travel between consecutive stops
- [ ] Sequencing function supports anchoring at either a Hotel or an Airport/Transit Point (needed later for Travel Days), without knowing about either concept — just an anchor coordinate
- [ ] Budget Floor function takes candidate Activities/Restaurants per Slot and a Budget, returns the cheapest feasible full combination
- [ ] Budget Floor function's "no cheaper option" result is only reachable via an exhaustive check of every supplied candidate for every Slot
- [ ] Both functions have no LLM calls, no network calls, and no dependency on graph/state/checkpointer code
- [ ] Unit tests exercise both functions against fixture candidate lists only — no mocking required
