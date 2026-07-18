# 02 — Thinnest full-stack Itinerary: single Leg, single regular Day, Activities only

**What to build:** The first real, demoable path through the whole agent. A traveler describes a single-city, single-day trip; the agent asks for whatever Requirements are missing (destination + Hotel, Travel Party size, Budget, arrival/departure Airport + time — captured but not yet enforced/used for trimming, restaurants opted out for this slice), remembers what's already been given across turns via the Checkpointer, and once Requirements are complete, researches Activities restricted to the Allowed Domains List and returns one sequenced, Hotel-anchored Day of Activities filling the non-meal Slots (morning/afternoon/evening activity). Meal Slots are simply left unfilled since restaurants are opted out. This ticket stands up the Trip > Leg > Day > Slot > Activity state model, the LangGraph skeleton (composition over inheritance), the Checkpointer, and a first Source Category ("Activities") in the Allowed Domains List config.

**Blocked by:** 01

**Status:** ready-for-agent

- [ ] State model represents Trip > Leg > Day > Slot > Activity per `CONTEXT.md` and ADR-0002 (single Leg only for now, but the Leg layer exists)
- [ ] Graph is a LangGraph state machine built with composition over inheritance
- [ ] Checkpointer persists state across turns for one conversation thread
- [ ] Requirements node asks only for missing fields among: destination + Hotel, Travel Party size, Budget, arrival/departure Airport + time; never re-asks for something already supplied
- [ ] Restaurants are opted out for this ticket's scope — meal Slots are left unfilled, no Restaurant research happens
- [ ] Allowed Domains List config has an "Activities" Source Category that can have Sources added via config, not code changes to research logic
- [ ] Activity research pulls candidates only from domains in the Activities Source Category, using review/content signal to select and rank, not just factual existence
- [ ] Once Requirements are complete, the graph produces a single Day with morning/afternoon/evening activity Slots filled, sequenced via the Test Seam 2 function from 01, anchored on the Hotel
- [ ] A full conversation (multiple turns: partial info, then completing info) can be driven through the compiled graph (Test Seam 1) and asserted on end-to-end
