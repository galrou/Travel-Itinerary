# 07 — Multi-Leg trips with inter-Leg Transit

**What to build:** Extend Requirements gathering and Itinerary assembly from a single Leg to a full multi-city Trip. The traveler specifies a destination + Hotel per Leg, and a time + Transit Point for each move between Legs. Each Leg is sequenced independently around its own Hotel; the transition Day between two Legs is a Travel Day anchored at the Transit Point (reusing the Travel Day trimming/anchoring machinery from 06, generalized from Airport-only to the more general Transit Point).

Per-Leg destination/Hotel and inter-Leg Transit Point/time capture extend the existing `RequirementsExtractor` seam (more fields, same Protocol) — no new LLM component needed.

**Blocked by:** 06

**Status:** ready-for-agent

- [ ] Requirements node asks for destination + Hotel per Leg, and time + Transit Point for each inter-Leg move
- [ ] Each Leg's Days are sequenced independently around that Leg's own Hotel — switching cities doesn't affect another Leg's geographic plan
- [ ] The Day where the traveler transitions between two Legs is treated as a Travel Day, trimmed and anchored by the Transit Point + time (not necessarily Airport/IATA-based)
- [ ] Budget remains a single ceiling across the whole Trip, spanning all Legs
- [ ] End-to-end conversation test (Test Seam 1) covers a two-Leg Trip and asserts both Legs' Itineraries and the transition Day are correct
