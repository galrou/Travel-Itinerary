# 05 — Multi-Day itinerary within a single Leg

**What to build:** Extend Requirements gathering and Day assembly (04) from a single Day to a full Leg's stay of consecutive regular Days. Each Day is independently sequenced and Hotel-anchored, still respecting Budget across the whole Trip (not per Day).

Length-of-stay capture extends the existing `RequirementsExtractor` seam (one more field on `Requirements`) — no new LLM component needed.

**Blocked by:** 04

**Status:** ready-for-agent

- [ ] Requirements node captures the length of stay (or derives it from other given dates) for a Leg
- [ ] Day assembly runs once per Day in the Leg, each with its own Sequencing and its own set of researched candidates
- [ ] Budget is enforced across the whole multi-Day Itinerary total, not reset per Day
- [ ] End-to-end conversation test (Test Seam 1) produces a multi-Day Itinerary for one Leg and asserts each Day is independently sequenced and Hotel-anchored
