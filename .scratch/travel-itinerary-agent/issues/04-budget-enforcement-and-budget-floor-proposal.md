# 04 — Budget enforcement & Budget Floor proposal

**What to build:** Wire the stated Budget into the Day assembled by 02/03. The agent must reject Activity/Restaurant combinations that exceed the Budget (a single ceiling for the whole Travel Party, covering only Activities/Restaurants — not flights or hotel), and when no combination fits, propose the Budget Floor — the cheapest feasible Itinerary it can build — instead of failing outright. Costs are presented framed to the party size. Uses the Budget Floor function from 01 for the actual search and its exhaustiveness guarantee.

**Blocked by:** 03

**Status:** ready-for-agent

- [ ] Day assembly rejects any Activity/Restaurant combination whose total exceeds the stated Budget
- [ ] When the stated Budget cannot produce any valid Day, the agent proposes the Budget Floor (cheapest feasible combination) rather than failing
- [ ] The Budget Floor proposal is backed by the exhaustive-search guarantee from 01 — every fetched candidate for every Slot was considered
- [ ] Costs shown to the traveler are framed to the Travel Party size (e.g. "price for couple"), not always broken out per traveler
- [ ] End-to-end conversation tests (Test Seam 1) cover: a Budget that comfortably fits, and a Budget too low that triggers a Budget Floor proposal
