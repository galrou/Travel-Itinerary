# 08 — Feedback-driven Itinerary mutation

**What to build:** Let the traveler give follow-up feedback in plain language (e.g. "swap lunch for a cafe") after an Itinerary exists, and have the agent mutate just the targeted Slot in place — without re-researching or re-sequencing the rest of the Itinerary, and without the traveler re-describing their trip. Per ADR-0001, there is no version history: the one Itinerary in the Checkpointer's persisted state is mutated directly and written back through the same thread.

Feedback interpretation is its own LLM seam, distinct from `RequirementsExtractor`: a new `FeedbackInterpreter` Protocol (message + current Day → targeted Slot + replacement criteria). It mirrors `RequirementsExtractor`'s shape — real implementation is LLM-backed and out of scope for this ticket; tests mock it with a scripted fake, no real LLM/API calls. See ADR-0003 for why this is a separate Protocol rather than an extension of `RequirementsExtractor`.

**Blocked by:** 07

**Status:** ready-for-agent

- [ ] `FeedbackInterpreter` Protocol defined (message + current Day → targeted Slot + replacement criteria); real implementation is LLM-backed and out of scope here, tests use a scripted fake
- [ ] Feedback referencing a specific Slot (e.g. "swap lunch") is resolved to that Slot in the current Itinerary
- [ ] Only the targeted Slot changes; the rest of the Itinerary (other Slots, other Days, other Legs) is left untouched
- [ ] The replacement candidate still respects the Allowed Domains List, remaining Budget, and any other still-applicable Requirements (e.g. cuisine prefs for a swapped meal)
- [ ] The mutated Itinerary is persisted via the Checkpointer on the same conversation thread — no new version object is created
- [ ] End-to-end conversation test (Test Seam 1) drives: build an Itinerary, give Slot-targeted feedback, assert only that Slot changed
