# Submission kit — Project page text, in the order of the official form

Every number carries its key in `docs/slide_numbers.json` in square brackets (key in backticks,
then "= value"); a test fails if a value drifts (`tests/test_mission_value.py`). The paste-ready
copy without keys is generated: `python scripts/slides/project_page.py` → `docs/project_page.md`.
Form fields and rules below were read on the official Project Submission Guide (15/11/2026,
https://www.spaceappschallenge.org/resources/project-submission-guide/).

**Only the team can fill or decide (marked ⟨TEAM⟩ below):**
1. Team name (cover slide: `python scripts/slides/build_deck.py --team "<name>"` then
   `node scripts/slides/render_deck.mjs`).
2. The "Use of SI" answer: the form question is for data collection only and is not seen by the
   judges; the SI indicators judges see are the statements on the web footer, slide 7, README and
   this page.
3. Category field (form drop-down); "Submit for Judging".

---

## Project name
SIMILITUDE: which Earth test results transfer to the Moon Base and Mars

## Link to Project Demo (7 slides including the title slide, PDF, public)
https://johnlrr.github.io/nasa-earth-analog/SIMILITUDE-slides.pdf

## Link to Final Project (public, no login)
https://johnlrr.github.io/nasa-earth-analog/ (web app) · test-site finder for Artemis regions
(access screen, slope and route tests): https://johnlrr.github.io/nasa-earth-analog/test-sites.html · source, data
tables and validation report: https://github.com/Johnlrr/nasa-earth-analog

## High-Level Project Summary
Before a rover or an EVA crew goes to the Moon Base, NASA rehearses on Earth, at analog sites
usually picked because they are famous. SIMILITUDE checks whether they really match, and the
famous ones do not: on the Moon Base ridge (Connecting Ridge) **76 %** of the terrain is steeper
than 8° [`cr_frac_gt8` = 0.758]; in the footprints of six classic analog field sites the median
is **9 %** [`classic_frac_gt8_median` = 0.089], and **0 of 54** footprints around them pass our
ridge test [`stability_classic_robust` = 0, `stability_classic_n` = 54].
**What a test engineer gets.** Pick an Artemis south-pole region and get the Earth sites that do
match, each with a card: which test results transfer, which need a named facility instead, and
which orbit cannot judge. For the ridge, SIMILITUDE found two new sites, in countries open to NASA
and outside known analog areas, that pass both the slope and the traverse test on two elevation
models: one in Argentina, the only one of **1,000** random cells to pass
[`prevalence_connecting_ridge_n` = 1000], and one on Baffin Island, Canada, where from 13 Nov to
22 Jan every daylight minute has the Sun below 7° (**71** days [`i1_baffin_window_days` = 71]),
the closest Earth comes to the polar low Sun.
**Checked against NASA and against a real rover.** Our slope code matches NASA's PGDA 78 slope
rasters to **0.0009°** [`nasa_slope_max_abs_diff_deg` = 0.0009]. On Mars, our 30 m slope from
orbit ranks the terrain the way Perseverance's own tilt sensor did at **708** waypoints
(Spearman **0.80** [`r1b_rho` = 0.802, `r1b_n` = 708], pre-registered).
**Built to be trusted.** Every test is registered before it runs, and failures are published.
A slope match is not automatically a traverse match: our first registered route test failed and
the second passes at nominal α only (p = 0.049 [`v2_h1_p` = 0.0492]; 0.098 over the two looks),
with classic footprints doing as well [`v2_classic_share` = 0.3148], so every card reports slope
and traverse separately. Our mineral test failed its own stop rule, so the tool publishes no
mineral analog: it refuses to claim what the data cannot carry.
**Same code, Mars too.** On Perseverance's Jezero delta front, classic Mars analog footprints
match in **42 %** of cases against **19 %** of random land [`mars_classic_share` = 0.4222,
`mars_null_share` = 0.1881] (pre-registered, p = 0.0004 [`mars_p` = 0.0004]): delta-front test
terrain is common on Earth and easy to reach. Open source (Apache-2.0), NASA data end to end.

## Detailed Project Description
**What it does.** For five mission tests — Moon terrain for touchdown and traverse, Moon low-Sun
shadows, Mars rover terrain, Mars aqueous minerals, Mars ice under dry soil — SIMILITUDE computes the same
descriptors on the target (NASA LOLA / PGDA 78, MRO CTX DTM, MRO CRISM, SWIM) and on Earth (Copernicus DEM,
NASA EMIT, MODIS, ERA5-Land), measures the distance to the target, and tests it against a random
null sample of Earth cells. Each test variable gets one of three verdicts: TRANSFERS (test it in
the field), NO-ANALOG (no Earth site reproduces it; the card names the facility) or UNOBSERVED
(we cannot say).

**How we know it is not noise.**
- Our slope code reproduces NASA's own slope rasters on six south-pole sites to within
  **0.0009°** [`nasa_slope_max_abs_diff_deg` = 0.0009].
- Of **1,000** random bare-land cells, **1** passes the terrain test for the ridge and **9** for
  the steep Shackleton inner wall [`prevalence_connecting_ridge_n` = 1000,
  `prevalence_connecting_ridge_pass` = 1, `prevalence_shackleton_rim_pass` = 9].
- Recomputed from a second, independent elevation model (NASADEM / ArcticDEM), **102 of 109**
  terrain verdicts are unchanged [`cross_dem_same_verdict` = 102, `cross_dem_n` = 109]. The ones
  that change are listed and marked marginal, including one of our two ridge matches (Peary
  Land).
- In the 12 km blocks around six classic analog sites, **0 of 54** footprints pass the ridge test
  [`stability_classic_robust` = 0, `stability_classic_n` = 54].
- Ice test: **2 of 2** polar-desert controls pass, **2 of 2** wet-permafrost decoys are rejected
  [`x1_positive_pass` = 2, `x1_decoy_rejected` = 2]; semi-quantitative.
- Mineral test: **3 of 4** pre-registered checks pass [`m1_checks_passed` = 3,
  `m1_checks_n` = 4]; the rule says FAIL, so nothing is published for it.
- Traverse test, registered before it was run (`config/prereg_route_v1.yaml`, commit 4e9ceff):
  an 8-connected planner with grade limits of 6°, 8° and 10° on 30 m cells, same seed on both
  worlds; a footprint reproduces the ridge if its route outcomes are as close as half of the
  ridge's own lunar neighbours. Slope matches **3 of 9**, random land **151 of 994**, classic
  footprints **27 of 54** [`v1_passer_reproduce` = 3, `v1_null_reproduce` = 151,
  `v1_classic_reproduce` = 27]; H1 fails (p = 0.15 [`v1_h1_p` = 0.148]). Slope distance does
  predict route distance in random land (Spearman **0.38** [`v1_h2_rho` = 0.377]). The same three
  matches reproduce the routes on the second DEM [`v1_passer_second_dem_reproduce` = 3].
- V2, registered before the rerun (`config/prereg_v2_mars.yaml`, commit 67920dd): the same test
  with scale and threshold from **124** non-overlapping lunar windows instead of 8
  [`v2_n_moon_native` = 124]. Slope matches **3 of 9**, random land **95 of 994**, classic
  footprints **17 of 54** [`v2_passer_reproduce` = 3, `v2_null_reproduce` = 95,
  `v2_classic_reproduce` = 17]; H1 passes at nominal α (p = 0.049 [`v2_h1_p` = 0.0492]; counting
  both registered looks, Bonferroni p = 0.098 [`v2_h1_p_bonferroni` = 0.0983], so not confirmed),
  H1b fails (p = 0.59 [`v2_h1b_p` = 0.5949]).
- Mars terrain, same registration: Jezero delta front on the USGS CTX DTM, slope and route
  distances with thresholds from **185** Mars windows [`mars_n_neighbours` = 185]. Classic Mars
  analog footprints **19 of 45**, random land **187 of 994** [`mars_classic_match` = 19,
  `mars_null_match` = 187]; HI-SEAS 9/9, Atacama 5/9, Haughton 3/9, MDRS 2/9, Wright Valley 0/9
  (square 20 m ground cells; the first run used cells 5 % too wide, Deviations 40). The test
  passes (p = 0.0004), but the delta front is gentle terrain, so about one random cell in five matches.
- Ground truth from Perseverance (registered before any slope was read at a waypoint): our 30 m
  slope vs the rover's measured tilt at **708** waypoints, Spearman **0.80** [`r1b_rho` = 0.802],
  **0.91** with one value per rover site [`r1b_rho_site` = 0.909, `r1b_n_site` = 91]: pass. The
  planner's detour vs the rover's real detour (Spearman −0.35 [`r1_rho` = -0.353]) and roughness vs
  drive rate both fail, so route outcomes stay labelled a planner simulation.
- Every rule changed after seeing data is listed in the validation report (Deviations table).

**Site finder for test engineers.** Pick an Artemis south-pole region (six PGDA 78 regions) and
get matching 4 km footprints outside our access screen, each with Sentinel-2 and slope-class
pictures, the share of terrain steeper than 8° and 20°, a second-DEM check and the snow/ice share.
For Connecting Ridge, the two leads that also pass the traverse test are the ones to visit first:
Argentina (-28.79, -69.63; terrain shadow inside the ridge neighbourhood's range, low Sun only at
dawn and dusk) and Baffin Island (63.85, -65.58; a 71-day winter window of all-day low Sun, but
snow season and more terrain shadow than the ridge; its slope match still holds at 5 m with
ArcticDEM 2 m [`ms_baffin_holds_all_scales` = 1]). For the steep Shackleton inner wall the slope rule
is not selective (9 of 1,000 random cells pass): **117** leads hold on two DEMs, but **0** of them
reproduce the wall's simulated routes [`atlas_shackleton_slope_two_dems` = 117,
`atlas_shackleton_routes_two_dems` = 0]. Across all six regions, only Connecting Ridge has a field
site that passes every terrain test; the others are rehearsed in facilities. Leads are exploratory: found after the published results, not visited yet. The
access screen leaves out China (Wolf Amendment), Russia and countries under comprehensive US
sanctions; it is an assumption for planning, not a legal opinion.

**What a mission team gets.** A campaign, not a site. For Connecting Ridge, the two leads together
cover **5 of 5** field rows that orbit can judge (slope, simulated routes, all-day low Sun, terrain
shadow, slope at 5 m) [`camp_two_leads` = 5, `camp_n_field` = 5]; Baffin covers 4 of them at once,
in its winter window; the best classic site alone covers **1** [`camp_best_classic_alone` = 1].
Rocks under 60 m need a site survey and **8** rows go to named facilities [`camp_n_facility` = 8].
The rows map to NASA's Civil Space Shortfalls "Autonomous Surface Mobility and Navigation"
(ESDMD #0805) and "Lunar Precision Landing and Hazard Avoidance" (ESDMD #1101).
Beside that, a test protocol per site (systems to test, what to measure, what
the site does not reproduce), read beside published NASA numbers: Artemis III "Surface slope for
landing (100m): <10 deg" and "Surface slope limit for EVA (2km): <20 deg" (NASA NTRS
20250009323); Mars Life Explorer "land within a vertical meter of Martian mid-latitude ice, drill
for samples to a 2-meter depth". On the original per-lens card a terrain site reproduces **1 of 7**
rows [`coverage_L1_transfers` = 1, `coverage_L1_total` = 7]; the campaign view adds simulated
routes, low-Sun windows and 5 m slopes, and names the facility for the rest. A card is an input to a project's own "documented definition of relevant
environment"; it assigns no TRL.

**Limits we state ourselves.**
- Counts come from a **307**-cell sample screened towards Connecting Ridge
  [`l1_cells_scored_rank_seed` = 307], not a census: about **201** bare-land cells (95 % CI
  10–1,093) would pass the terrain test [`prevalence_connecting_ridge_cells` = 201,
  `prevalence_connecting_ridge_cells_lo` = 10, `prevalence_connecting_ridge_cells_hi` = 1093].
- A match is one 4 km footprint, not a region; slopes are computed on a 30 m baseline and compare
  Earth with Moon, not with NASA's landing maps.
- Da Qaidam and Peary Land are known analog regions, not hidden sites; Da Qaidam and the Chile
  lead (inside the Atacama analog area) fail the traverse test.
- The traverse test is a planner simulation on 30 m cells, not a rover; rocks, small craters and
  soil strength are not in it.
- The route test beats random land only narrowly (V2, p = 0.049; 0.098 over two looks) and does not beat classic sites;
  the Mars delta-front match is common (19 % of random land), so Mars matches are terrain leads.
- Every Connecting Ridge lead has more terrain above the 20° EVA slope limit than the ridge itself
  (0.08–0.26 of the footprint vs **0.058** [`cr_frac_gt20` = 0.0578], 30 m), so EVA routes there
  are harder than on the target.
- Over a year no Earth site reproduces the polar Sun: the best has the Sun below 7° for **28 %**
  of daylight, the lunar target for **100 %** [`l2_earth_best_lowsun_frac_daylight` = 0.277,
  `l2_moon_lowsun_frac_daylight` = 1.0]. The Baffin window is seasonal, from a geometric sun
  model (no refraction, no horizon), and exploratory.
- The ice lens is semi-quantitative (reanalysis soil temperature, thresholds set after seeing
  data); metre-scale boulders are below our resolution.

**Tools.** Python (NumPy, pandas, SciPy, Matplotlib), Google Earth Engine, NASA earthaccess,
OpenAlex API, Leaflet with NASA GIBS for the web map, GitHub Actions and Pages. Code licence
Apache-2.0.

## Use of Super Intelligence (SI)
Factual statement of where and how SI tools were used (official rule: SI use is permitted and must be indicated in descriptive text and metadata).

Yes. We used SI assistants (Anthropic Claude models through Claude Code; Google Gemini models
through the Antigravity IDE) throughout: to draft and review planning documents, to write and
test code, to run and check analyses, to search and read the literature, to draft the validation
report, the slide text and this page, and to act as an adversarial reviewer before each merge.
SI assistants also proposed analysis directions that we adopted (presenting results by field
site, reading results beside published NASA requirements, the checks with a second elevation
model and a larger random sample). All data are NASA and partner open data, processed by the open
code in the repository; every threshold, control and rule change is recorded with its date and
reason. No SI-generated images, audio or video are used; the figures are plots of our own data.
Where SI was used is also stated on the web app, on the last slide and in the repository.

Core idea (judging analog sites by which test results transfer, per mission test):
⟨TEAM: state here, truthfully, who originated it and how SI was involved⟩.

## NASA Data
NASA PGDA Product 78 (LRO LOLA south-pole DEMs and slope rasters) · NASA EMIT L2A surface
reflectance · MRO CRISM MICA type spectra (PDS Geosciences) · SWIM subsurface water ice mapping
(Morgan et al. 2021) · USGS Mars 2020 TRN CTX DTM of Jezero (MRO CTX) · MODIS land surface temperature and vegetation · ASTER GED · NASADEM ·
NASA GIBS Blue Marble (web basemap) · NASA NTRS 20250009323 and 20240009596 (Artemis III
landing requirements) · Mars Life Explorer mission concept study · NASA TRL definitions · NASA
SVS 14583 (JETT5) · NASA planetary fact sheets.

## Space Agency Partner Data and Other References
Copernicus DEM GLO-30 and ERA5-Land (ESA / Copernicus) · ESA WorldCover · Sentinel-2 (ESA) ·
TerraClimate · ArcticDEM (PGC) · OpenAlex · OpenStreetMap Nominatim · Viviano-Beck et al. 2014
(CRISM browse products) · Leaflet. Full table with links: README and `ledger/*.yaml` in the
repository.

---

## Seven slides in one line each (built from `scripts/slides/build_deck.py`)
1. Cover — "Famous ≠ faithful": 76 % vs 9 %, and 3 of 9 slope matches also reproduce the
   ridge's simulated routes (pre-registered).
2. Problem — six famous analog field sites are too flat for the Moon Base ridge
   (`docs/figures/fig_mission_slopes.png`).
3. Method — one formula, two worlds, a verdict for every test variable; five lenses incl. Mars rover terrain (Jezero).
4. Evidence — six checks against known truth; traverse test FAIL with 8 lunar neighbours, PASS with 124 (both registered); mineral FAIL.
5. Finding — two open-country sites pass both terrain tests on two DEMs: Argentina (random draw)
   and Baffin Island (71-day low-Sun window); Chile and Da Qaidam dropped by the traverse test.
6. Limits — sample not census, footprint not region, slope match ≠ route match, polar Sun
   28 % over a year but a seasonal window at Baffin.
7. Value — a campaign coverage matrix (`docs/figures/fig_campaign_coverage.png`), Mars terrain and ice, links.

## Optional 30-second video (the slide deck already satisfies the demo rule)
See `docs/video_script.md` for the shot list, on-screen text and narration. If made, it must be
30 s or less, English (or English subtitles), hosted publicly with no login.
