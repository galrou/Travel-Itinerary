# 03 — Add Restaurant recommendations to the Day

**What to build:** Extend the single-Leg, single-Day Itinerary from 02 so meal Slots (breakfast, lunch, dinner) get filled by researched Restaurants instead of being left empty. The traveler can opt in/out per meal Slot independently (never all-or-nothing), state cuisine/dietary/price-tier preferences, and optionally name a specific restaurant they want worked in if feasible. Restaurant candidates come from a new "Restaurants/Reviews" Source Category in the Allowed Domains List, ranked by the traveler's stated preferences, proximity to that Day's other Activities (not just the Hotel), and reviews from allowed Sources.

**Blocked by:** 02

**Status:** ready-for-agent

- [ ] Requirements node asks whether the traveler wants restaurant recommendations at all, and for which meals specifically, with independent per-Slot opt-out
- [ ] Requirements node captures cuisine/dietary/price-tier preferences and an optional named-restaurant request
- [ ] Allowed Domains List config has a "Restaurants/Reviews" Source Category, addable independently of the Activities category
- [ ] Restaurant research pulls candidates only from domains in the Restaurants/Reviews Source Category
- [ ] Restaurant ranking considers: stated preferences, proximity to the Day's other Activities, reviews, and honors a named-restaurant request when feasible
- [ ] A Day with restaurants opted in for some meals and out for others produces a Day where only the opted-in meal Slots are filled by Restaurants
- [ ] End-to-end conversation test (Test Seam 1) covers a Day with mixed opt-in/opt-out meal Slots
