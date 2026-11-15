# Test protocols for the showcase sites (PLAN 2d)

Generated 2026-11-15 11:35 by `scripts/mission_value.py` from `verdicts.parquet`, `field_facility.json`, `mission_criteria.parquet` and `config/mission.yaml`. Post hoc presentation layer: no threshold or verdict changed.

## What a card is, in NASA's terms

NASA's TRL definitions ask for a *"Documented definition of relevant environment"* before TRL 5 (*"Component and/or breadboard validation in relevant environment"*) ([source](https://www.nasa.gov/wp-content/uploads/2017/12/458490main_trl_definitions.pdf)). A SIMILITUDE card is that document for one site, written per test variable: **Field** rows are variables for which the site is a relevant environment by a stated, reproducible measure; **Facility** rows are variables for which no Earth site is, with the facility that replaces it; **Unobserved** rows are variables this engine cannot judge. A field campaign can therefore be credited towards TRL 5-6 for the Field rows only; the Facility rows must be closed in the named facility before a TRL 6 claim (*"operations under critical environmental conditions"*). This is the evidence a campaign may claim, not a certification of any hardware.

## Published requirements used

- **artemis3_landing_slope** — "Surface slope for landing (100m): <10 deg". Artemis Human Landing System Overview, NASA 2025 International Space Apps Challenge (L. Ortiz, NASA, 4 Oct 2025), slides 21 and 23; same text in Artemis Human Landing System Update (A. Dwyer Cianciolo, NASA LaRC, 1 Aug 2024), slides 19 and 21 ([source](https://ntrs.nasa.gov/citations/20250009323)).
- **artemis3_eva_slope** — "Surface slope limit for EVA (2km): <20 deg". same two NASA documents, slides 21 and 24 (2025) / 19 and 22 (2024) ([source](https://ntrs.nasa.gov/citations/20250009323)).
- **mars_ice_access** — "land within a vertical meter of Martian mid-latitude ice, drill for samples to a 2-meter depth". Mars Life Explorer, Planetary Mission Concept Study for the 2023-2032 Decadal Survey (JPL, 2021), executive summary and section 1 ([source](https://science.nasa.gov/wp-content/uploads/2023/10/mars-life-explorer.pdf)).
- **trl_relevant_environment** — "Component and/or breadboard validation in relevant environment". NASA Technology Readiness Level Definitions (table reproduced from NPR 7123.1) ([source](https://www.nasa.gov/wp-content/uploads/2017/12/458490main_trl_definitions.pdf)).

## Protocol per lens

### L1 — Slope traverse and touchdown-terrain rehearsal

- **Systems under test:** crewed/uncrewed rover mobility and path planning on slopes, EVA traverse planning, hazard-map products for landing-site selection
- **Requirement it rehearses:** "Surface slope for landing (100m): <10 deg"; "Surface slope limit for EVA (2km): <20 deg"
- **NASA shortfalls addressed (ledger):** ESDMD #0805 Autonomous Surface Mobility and Navigation; ESDMD #1101 Lunar Precision Landing and Hazard Avoidance for Human Exploration
- **Credited in the field:** slope and multi-scale roughness statistics at 30-480 m baselines (verdict variable slope_roughness)
- **Measure:** traverse energy, slip and path length per km against the slope classes <8, 8-20 and >20 deg; compare with predictions made on the lunar DEM
- **Not credited (facility or unobserved):** wheel-soil traction and sinkage (gravity, regolith), dust, vacuum, thermal: facility rows of the card
- **Test-matrix coverage:** 1 variable(s) transfer, 5 need a facility, 1 unobserved (of 7)

### L2 — Low-Sun shadow navigation rehearsal

- **Systems under test:** optical navigation and hazard detection cameras, traverse timing around long terrain shadows
- **Requirement it rehearses:** "Surface slope limit for EVA (2km): <20 deg"
- **NASA shortfalls addressed (ledger):** ESDMD #0805 Autonomous Surface Mobility and Navigation; ESDMD #0301 Systems to Survive and Operate through Extended Periods of Lunar Shadow
- **Credited in the field:** terrain shadow casting at Sun elevations of 2, 5 and 7 deg (verdict variable shadow_casting)
- **Measure:** navigation solution error and hazard-detection rate inside and at the edge of terrain shadows at the three Sun elevations
- **Not credited (facility or unobserved):** the Sun geometry itself (grazing Sun for all of daylight, 360 deg azimuth): NO-ANALOG at every Earth site; black sky without diffuse light
- **Test-matrix coverage:** 1 variable(s) transfer, 7 need a facility, 1 unobserved (of 9)

### X1 — Ice-access drilling rehearsal under dry overburden

- **Systems under test:** 1-2 m class ice-access drills and sample handling, site characterisation before drilling
- **Requirement it rehearses:** "land within a vertical meter of Martian mid-latitude ice, drill for samples to a 2-meter depth"
- **NASA shortfalls addressed (ledger):** ESDMD #0603 Water Recovery from Lunar Regolith/Ice
- **Credited in the field:** ice configuration: permafrost, ice-bearing ground that never thaws from above, dry overburden (verdict variable ice_configuration; semi-quantitative)
- **Measure:** depth to ice-cemented ground, drilling energy and bit temperature through the dry layer into ice, ice-table mapping before drilling
- **Not credited (facility or unobserved):** Mars pressure and CO2 atmosphere, temperature, perchlorate chemistry, radar response of the overburden
- **Test-matrix coverage:** 2 variable(s) transfer, 6 need a facility, 1 unobserved (of 9)

### M1 — Aqueous-mineral instrument rehearsal

- **Systems under test:** none certified by this engine
- **Requirement it rehearses:** —
- **NASA shortfalls addressed (ledger):** —
- **Credited in the field:** none: M1 failed its pre-registered stop rule, no M1 site is published
- **Measure:** -
- **Not credited (facility or unobserved):** all rows
- **Test-matrix coverage:** 1 variable(s) transfer, 6 need a facility, 2 unobserved (of 9)

## Protocol per showcase site

### Da Qaidam, northern Qaidam Basin margin (Qinghai)

Evidence: engine-confirmed **L1** · 2 cell(s), span 143 km · showcase rule a

- **L1 Slope traverse and touchdown-terrain rehearsal.** Test: crewed/uncrewed rover mobility and path planning on slopes, EVA traverse planning, hazard-map products for landing-site selection. Measure: traverse energy, slip and path length per km against the slope classes <8, 8-20 and >20 deg; compare with predictions made on the lunar DEM. Not credited here: wheel-soil traction and sinkage (gravity, regolith), dust, vacuum, thermal: facility rows of the card.
- **Artemis III slope reading, cell E10K_453_921:** 79% of the footprint is steeper than 8° (Connecting Ridge reference 76%), 4.5% is steeper than the 20° EVA limit (reference 5.8%). 30 m baseline in a 4 km footprint on both worlds; NASA states the landing limit at 100 m and the EVA limit over 2 km. Same formula both sides; not a landing-site certification.
- **Facility rows to close elsewhere:** 5 (see `docs/field_facility.md`, same site).

### Mauna Loa – Mauna Kea, Hawaiʻi

Evidence: engine-confirmed **L2** · 1 cell(s), span 0 km · showcase rule a

- **L2 Low-Sun shadow navigation rehearsal.** Test: optical navigation and hazard detection cameras, traverse timing around long terrain shadows. Measure: navigation solution error and hazard-detection rate inside and at the edge of terrain shadows at the three Sun elevations. Not credited here: the Sun geometry itself (grazing Sun for all of daylight, 360 deg azimuth): NO-ANALOG at every Earth site; black sky without diffuse light.
- **Facility rows to close elsewhere:** 7 (see `docs/field_facility.md`, same site).

### Peary Land, North Greenland

Evidence: engine-confirmed **L1**, engine-semiquant **X1** · 1 cell(s), span 0 km · showcase rule a,b

- **L1 Slope traverse and touchdown-terrain rehearsal.** Test: crewed/uncrewed rover mobility and path planning on slopes, EVA traverse planning, hazard-map products for landing-site selection. Measure: traverse energy, slip and path length per km against the slope classes <8, 8-20 and >20 deg; compare with predictions made on the lunar DEM. Not credited here: wheel-soil traction and sinkage (gravity, regolith), dust, vacuum, thermal: facility rows of the card.
- **X1 Ice-access drilling rehearsal under dry overburden.** Test: 1-2 m class ice-access drills and sample handling, site characterisation before drilling. Measure: depth to ice-cemented ground, drilling energy and bit temperature through the dry layer into ice, ice-table mapping before drilling. Not credited here: Mars pressure and CO2 atmosphere, temperature, perchlorate chemistry, radar response of the overburden.
- **Artemis III slope reading, cell E10K_729_-319:** 56% of the footprint is steeper than 8° (Connecting Ridge reference 76%), 8.2% is steeper than the 20° EVA limit (reference 5.8%). 30 m baseline in a 4 km footprint on both worlds; NASA states the landing limit at 100 m and the EVA limit over 2 km. Same formula both sides; not a landing-site certification.
- **Facility rows to close elsewhere:** 11 (see `docs/field_facility.md`, same site).

### Atacama – Puna altiplano (Chile, Argentina, Bolivia)

Evidence: engine-confirmed **L1,L2** · 54 cell(s), span 1108 km · showcase rule b

- **L1 Slope traverse and touchdown-terrain rehearsal.** Test: crewed/uncrewed rover mobility and path planning on slopes, EVA traverse planning, hazard-map products for landing-site selection. Measure: traverse energy, slip and path length per km against the slope classes <8, 8-20 and >20 deg; compare with predictions made on the lunar DEM. Not credited here: wheel-soil traction and sinkage (gravity, regolith), dust, vacuum, thermal: facility rows of the card.
- **L2 Low-Sun shadow navigation rehearsal.** Test: optical navigation and hazard detection cameras, traverse timing around long terrain shadows. Measure: navigation solution error and hazard-detection rate inside and at the edge of terrain shadows at the three Sun elevations. Not credited here: the Sun geometry itself (grazing Sun for all of daylight, 360 deg azimuth): NO-ANALOG at every Earth site; black sky without diffuse light.
- **Facility rows to close elsewhere:** 12 (see `docs/field_facility.md`, same site).

### Jebel Akhdar, Hajar Mountains (Oman)

Evidence: engine-confirmed **L2** · 1 cell(s), span 0 km · showcase rule b

- **L2 Low-Sun shadow navigation rehearsal.** Test: optical navigation and hazard detection cameras, traverse timing around long terrain shadows. Measure: navigation solution error and hazard-detection rate inside and at the edge of terrain shadows at the three Sun elevations. Not credited here: the Sun geometry itself (grazing Sun for all of daylight, 360 deg azimuth): NO-ANALOG at every Earth site; black sky without diffuse light.
- **Facility rows to close elsewhere:** 7 (see `docs/field_facility.md`, same site).

### Zanda (Tsamda) and Gar, Ngari, western Tibet

Evidence: engine-confirmed **L1** · 5 cell(s), span 206 km · showcase rule c

- **L1 Slope traverse and touchdown-terrain rehearsal.** Test: crewed/uncrewed rover mobility and path planning on slopes, EVA traverse planning, hazard-map products for landing-site selection. Measure: traverse energy, slip and path length per km against the slope classes <8, 8-20 and >20 deg; compare with predictions made on the lunar DEM. Not credited here: wheel-soil traction and sinkage (gravity, regolith), dust, vacuum, thermal: facility rows of the card.
- **Facility rows to close elsewhere:** 5 (see `docs/field_facility.md`, same site).

