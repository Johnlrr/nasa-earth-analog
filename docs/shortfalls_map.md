# SIMILITUDE against NASA's 2026 Civil Space Shortfalls

Source: NASA, *2026 Civil Space Shortfalls*, released 12 January 2026
(https://www.nasa.gov/wp-content/uploads/2026/03/2026-civil-space-shortfalls.pdf). Need IDs and
statements below are quoted from that list; the ESDMD numbers are the ones the list itself
references. The "what SIMILITUDE gives" column is ours and is limited to what our tables show.

SIMILITUDE does not close a shortfall. It shortens the path to closing it: the hardware and
procedures that answer these needs are tested on Earth before they fly, and SIMILITUDE tells the
test team where on Earth that test reproduces the target terrain and light, and where it does not.

| Need ID | NASA need statement (2026 list) | What SIMILITUDE gives the test team | Evidence level |
|---|---|---|---|
| 1.05 | Provide crew mobility for traverses on lunar surface. | Earth sites whose 30 m slope distribution and simulated traverse match an Artemis region (Connecting Ridge: Argentina and Baffin Island, both DEMs); the share of terrain above the 20° EVA limit at each site against the target. | Pre-registered terrain and route tests; slope checked against NASA PGDA 78 (0.0009°) and against Perseverance's measured tilt (ρ 0.80) |
| 1.06 | Provide in-situ decision support tools to address identified EVA hazards and risks on the lunar surface. | Before the mission: a card per site saying which EVA test results transfer, which need a named facility, and which orbit cannot judge (rocks under 60 m). Rehearsal input for such tools, not the tool itself. | Exploratory composition of tested rows (Deviations 35) |
| 3.02 | Land on lunar south pole exploration sites in various illumination conditions with appropriate accuracy. Reference ESDMD #1101. | A calendar of Earth low-Sun windows for testing landing and hazard-detection sensors under polar light: Baffin Island has 71 days (13 Nov–22 Jan) with every daylight minute below 7°; no Earth site has it all year (best 28 % of daylight vs 100 % on the Moon). | Geometric Sun model (Deviations 32); not yet checked against an ephemeris |
| 3.03 | Perform stable touchdown and operation of large vehicles on uneven, sloped, and undulating lunar surfaces. | Lens L1 ("touchdown and traverse"): Earth terrain with the target's slope distribution at a 30 m baseline, ranked against 1,000 random land cells, for touchdown and offloading trials. | Pre-registered L1 robust set; selectivity 1/1,000 for the ridge |
| 16.01 | Autonomously maneuver and navigate to achieve faster mobility with an order of magnitude greater range. Reference ESDMD #0805. | Field sites for rover autonomy trials on target-like slopes, and a planner check of whether a site's routes behave like the target's. Rover-scale hazards are out of scope. | Route test V2 passes at nominal α (p = 0.049; 0.098 over two looks); planner detour does not predict Perseverance's (R1, published) |
| 8.06 | Provide in-situ decision support tools to address identified EVA hazards and risks on the Martian surface. | Same card logic on Mars terrain; Mars rover-terrain lens on the Jezero delta front. | Pre-registered HM1 (p = 0.0004); delta-front terrain is common on Earth (19 % of random land) |
| 8.07 | Provide crew mobility for long traverses on Martian surface. | Earth sites matching Mars slope and simulated routes; the shallow-ice base regions are the next target (post-submission lens B). | As 8.06 |

## How to say it in one line
SIMILITUDE answers the test question behind NASA shortfalls 1.05, 3.02, 3.03 and 16.01: where on
Earth can this be rehearsed so the result still holds at the Moon Base, and where does it need a
facility instead.
