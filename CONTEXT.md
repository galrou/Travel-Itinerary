# Travel Planning Agent

A state-driven agent that turns a traveler's logistics (cities, hotels, budget) plus research from trusted sources into a geographically-sequenced, multi-city itinerary. Flights and hotels are already booked by the traveler before the agent is involved — the agent's only deliverable is the Itinerary of Activities.

## Language

**Trip**:
The top-level object the traveler is planning: an ordered sequence of Legs, undertaken by a Travel Party, constrained by a single overall Budget. Begins with an arrival Travel Day (Airport-anchored) and ends with a departure Travel Day (Airport-anchored).

**Leg**:
One destination city within a Trip, with its own Hotel/base location and its own ordered set of Days. A single-city Trip has exactly one Leg.

**Travel Party**:
The group of travelers on a Trip (e.g. solo, couple). Budget is one ceiling for the whole party, not per person, and Activity/Restaurant costs are quoted in a way natural to the party's size (e.g. "price for couple") rather than always broken down per traveler.

**Requirements**:
The logistics the traveler must supply before research can start: the Trip's Legs (destination city + Hotel/base location per Leg), Travel Party size, Budget, arrival/departure details (time and Airport) for the Trip, transit details (time and Transit Point) for each inter-Leg transition, and per-meal-Slot Restaurant preferences (see Restaurant). The agent must detect and ask about missing Requirements early rather than guessing.
lets pause
**Itinerary**:
The day-by-day activity schedule that is the agent's actual deliverable — an ordered sequence of Legs, each containing an ordered list of Days. It is a single evolving object per conversation: follow-up feedback mutates it in place rather than producing a new version.
_Avoid_: Plan (use Itinerary — there is no separate "Plan" object; it's the same thing)

**Feedback**:
A traveler's follow-up free-text request after an Itinerary already exists (e.g. "swap lunch for a cafe"), resolved to a specific Slot plus a replacement intent — never a full re-description of the trip. Distinct from Requirements: Requirements describes trip logistics before research starts; Feedback edits an already-built Itinerary in place (see ADR-0001 — no version history, the one Itinerary is mutated directly).

**Day**:
One calendar day within a Leg, structured as a fixed sequence of meal-anchored Slots (e.g. breakfast, morning activity, lunch, afternoon activity, dinner, evening activity). Every Slot is filled by exactly one Activity, which is what makes a targeted edit like "swap lunch for a cafe" meaningful.

**Travel Day**:
A Day that begins or ends with movement rather than a full day at the Hotel: the Trip's first/last Day (Airport-anchored) or a Day where the traveler transitions between two Legs (Transit-Point-anchored). Sequencing on a Travel Day may anchor one end of the route at the Airport/Transit Point instead of the Hotel — e.g. an Activity can sit between Airport and Hotel before the traveler ever checks in. Available Slots on a Travel Day are trimmed by the actual arrival/departure/transit time (e.g. a late arrival leaves only the dinner Slot open).

**Slot**:
A named, fixed position within a Day (e.g. "lunch") that an Activity fills. Slots give feedback a target to address without the user needing to describe the whole day.

**Activity**:
A single recommended thing to do — sightseeing, a meal, an event — anchored to a specific Slot and a physical location, costed against the Budget. Selection is grounded in and ranked by reviews and content pulled from allowed Sources, the same principle Restaurant follows — not just verified for factual accuracy, but chosen because the Source data ranks it well.

**Restaurant**:
A specialized Activity that fills a meal Slot (breakfast/lunch/dinner). Ranked by: the traveler's stated preferences (cuisine, dietary, price tier), an optional named-restaurant request (a specific restaurant or chain the traveler asks to be worked in if feasible), proximity to that Day's adjacent Activities (not just the Hotel), and reviews pulled from allowed Sources. Each meal Slot can be independently opted out of by the traveler — the agent must not assume all-or-nothing.

**Sequencing**:
The ordering of a Day's Activities to minimize travel between consecutive stops (a short route), not merely picking Activities that are each individually close to the Hotel. The Hotel anchors the route as its implicit start/end point — except on a Travel Day, where the Airport/Transit Point can anchor one end instead.

**Hotel / base location**:
The traveler's already-booked lodging for a Leg, supplied as part of Requirements. The agent never selects or evaluates hotels — it only uses this as the fixed anchor point for Sequencing within that Leg.

**Transit Point**:
A place and time marking movement into or out of a Leg. The Trip's overall arrival/departure is always Airport-based; movement between two Legs uses a generic Transit Point (train station, airport, etc. — not necessarily tied to an IATA code).

**Budget**:
A strict spending ceiling on Activities only (tickets, food, tours, etc.) for the Travel Party across the whole Trip. Flights and hotels are already booked by the traveler and are out of scope — Budget never needs to account for them.

**Budget Floor**:
The cheapest feasible Itinerary the agent can construct, offered back to the traveler when their stated Budget is too low to produce any valid Itinerary. The agent may only claim "no cheaper option exists" once it has exhaustively evaluated every Activity available from allowed Sources for every Slot and confirmed none combine to something cheaper — a claim scoped only to what was actually fetched this run is not sufficient to say it.

**Source / Allowed Domain**:
A domain the agent is permitted to pull external data from. The Allowed Domains List gates *all* external data the agent trusts — not just activity/content research, but any data the agent treats as factual.
_Avoid_: trusted website (use Source / Allowed Domain)

**Source Category**:
A labeled grouping within the Allowed Domains List (e.g. Activities, Restaurants/Reviews). Each category is configured and vetted as its own list rather than one flat list reused for everything — adding a new Source means adding it to the right category, not to a single global list.

**Checkpointer**:
The persistence mechanism that remembers a conversation's state across turns, so a traveler can give follow-up feedback (e.g. "swap lunch for a cafe") without re-supplying Requirements. It persists the one evolving Itinerary — it does not maintain a version history.
