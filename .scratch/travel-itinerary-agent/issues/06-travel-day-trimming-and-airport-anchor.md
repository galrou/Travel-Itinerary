# 06 — Travel Day trimming & Airport anchor

**What to build:** Make the Trip's arrival and departure Days behave as Travel Days rather than regular Days. The already-captured arrival/departure Airport + time is now actually used: available Slots on the first/last Day are trimmed to what's realistically possible (e.g. a 6pm arrival leaves only the dinner/evening Slots open), and the route on those Days can anchor at the Airport instead of the Hotel where appropriate — so an Activity near the airport can be scheduled before the traveler ever reaches the Hotel.

**Blocked by:** 05

**Status:** ready-for-agent

- [ ] Arrival Day's available Slots are trimmed based on the actual arrival time
- [ ] Departure Day's available Slots are trimmed based on the actual departure time
- [ ] Sequencing on a Travel Day can anchor one end of the route at the Airport instead of the Hotel, using the anchor-point support already built into the Test Seam 2 function (01)
- [ ] End-to-end conversation tests (Test Seam 1) cover a late arrival (fewer Slots available) and an early departure (fewer Slots available)
