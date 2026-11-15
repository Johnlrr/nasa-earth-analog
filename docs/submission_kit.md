# Submission kit — Project page text, in the order of the official form

Every number carries its key in `docs/slide_numbers.json` in square brackets (key in backticks,
then "= value"); a test fails if a value drifts (`tests/test_mission_value.py`). The paste-ready
copy without keys is generated: `python scripts/slides/project_page.py` → `docs/project_page.md`.
Form fields and rules below were read on the official Project Submission Guide (15/11/2026,
https://www.spaceappschallenge.org/resources/project-submission-guide/); quotes are in
`docs/compliance.md`.

**Only the team can fill or decide (marked ⟨TEAM⟩ below):**
1. Team name (cover slide: `python scripts/slides/build_deck.py --team "<name>"` then
   `node scripts/slides/render_deck.mjs`).
2. The originality statement in "Use of SI": who came up with the core idea. The official guide
   says SI "should not be used to (come up with your idea of how to solve the challenge)"; read
   `docs/compliance.md` §2 and decide before submitting.
3. Signatures in `docs/compliance.md`; Category field (form drop-down); "Submit for Judging".

---

## Project name
SIMILITUDE: which Earth test results transfer to the Moon Base and Mars

## Link to Project Demo (7 slides including the title slide, PDF, public)
https://johnlrr.github.io/nasa-earth-analog/SIMILITUDE-slides.pdf

## Link to Final Project (public, no login)
https://johnlrr.github.io/nasa-earth-analog/ (web app) · source, data tables and validation report:
https://github.com/Johnlrr/nasa-earth-analog

## High-Level Project Summary
Space agencies test Moon and Mars hardware at Earth "analog" sites, usually chosen because they
are famous or look right. SIMILITUDE asks the engineer's question instead: which test results
transfer? One formula is run on NASA data from both worlds, per mission test, and every site
gets a card that says what a field test there reproduces, what no Earth site reproduces (and
which facility replaces it) and what cannot be judged. For the Moon Base ridge (Connecting
Ridge), **76 %** of the terrain is steeper than 8° [`cr_frac_gt8` = 0.758]; in the footprints of
six classic analog field sites the median is **9 %** [`classic_frac_gt8_median` = 0.089]. From
196,008 bare-land cells we screened 300; two footprints match the ridge in that sample, and one
of them, Da Qaidam (a known Mars analog region), also survives a second, independent NASA
elevation model and matches **3 of 6** south-pole sites [`regions_matched_da_qaidam` = 3]. But
Da Qaidam is in China, where NASA cannot run a bilateral campaign. So we ran the same test on
**160** more cells in countries open to NASA [`access_new_scored` = 160]: **3** usable ridge
leads hold with a second elevation model and the published ice rule
[`access_connecting_ridge_leads_usable` = 3], in Argentina, Canada and Chile; the best needs about
**8 km** of traverse for the slope exposure of 10 km on the ridge
[`access_connecting_ridge_best_usable_traverse_km` = 8.2], against about 86 km at the median
classic site. Our mineral test did not pass its own pre-registered rule, so we publish no mineral
analog.

## Detailed Project Description
**What it does.** For four mission tests — Moon terrain for touchdown and traverse, Moon low-Sun
shadows, Mars aqueous minerals, Mars ice under dry soil — SIMILITUDE computes the same
descriptors on the target (NASA LOLA / PGDA 78, MRO CRISM, SWIM) and on Earth (Copernicus DEM,
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
- Every rule changed after seeing data is listed in the validation report (Deviations table).

**Site finder for test engineers.** Pick an Artemis south-pole region (six PGDA 78 regions) and
get matching 4 km footprints in countries open to NASA, each with Sentinel-2 and slope-class
pictures, the share of terrain steeper than 8° and 20°, a second-DEM check and the snow/ice share.
For the steep Shackleton inner wall there are **113** usable open-country leads
[`access_shackleton_rim_leads_usable` = 113], most in the Andes. Leads are exploratory: found
after the published results by the unchanged rule, not visited yet. Closed countries are an
assumption for planning (China including Aksai Chin, Russia, countries under comprehensive US
sanctions), not a legal opinion.

**What a mission team gets.** A test protocol per site (systems to test, what to measure, what
the site does not reproduce), read beside published NASA numbers: Artemis III "Surface slope for
landing (100m): <10 deg" and "Surface slope limit for EVA (2km): <20 deg" (NASA NTRS
20250009323); Mars Life Explorer "land within a vertical meter of Martian mid-latitude ice, drill
for samples to a 2-meter depth". By our measure a terrain site reproduces **1 of 7** test
variables [`coverage_L1_transfers` = 1, `coverage_L1_total` = 7]; the card names the facility for
the others. A card is an input to a project's own "documented definition of relevant
environment"; it assigns no TRL.

**Limits we state ourselves.**
- Counts come from a **307**-cell sample screened towards Connecting Ridge
  [`l1_cells_scored_rank_seed` = 307], not a census: about **201** bare-land cells (95 % CI
  10–1,093) would pass the terrain test [`prevalence_connecting_ridge_cells` = 201,
  `prevalence_connecting_ridge_cells_lo` = 10, `prevalence_connecting_ridge_cells_hi` = 1093].
- A match is one 4 km footprint, not a region; slopes are computed on a 30 m baseline and compare
  Earth with Moon, not with NASA's landing maps.
- Da Qaidam and Peary Land are known analog regions, not hidden sites; only Zanda/Gar has a low
  literature count [`site_zanda_gar_attention` = 1].
- No Earth site reproduces the polar Sun: the best has the Sun below 7° for **28 %** of daylight,
  the lunar target for **100 %** [`l2_earth_best_lowsun_frac_daylight` = 0.277,
  `l2_moon_lowsun_frac_daylight` = 1.0].
- The ice lens is semi-quantitative (reanalysis soil temperature, thresholds set after seeing
  data); metre-scale boulders are below our resolution.

**Tools.** Python (NumPy, pandas, SciPy, Matplotlib), Google Earth Engine, NASA earthaccess,
OpenAlex API, Leaflet with NASA GIBS for the web map, GitHub Actions and Pages. Code licence
Apache-2.0.

## Use of Super Intelligence (SI)
Factual draft; the team must check it against the official rule (`docs/compliance.md`) before use.

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
(Morgan et al. 2021) · MODIS land surface temperature and vegetation · ASTER GED · NASADEM ·
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
1. Cover — "Famous ≠ faithful": 76 % vs 9 %, verdicts unchanged with a second DEM.
2. Problem — six famous analog field sites are too flat for the Moon Base ridge
   (`docs/figures/fig_mission_slopes.png`).
3. Method — one formula, two worlds, a verdict for every test variable.
4. Evidence — six checks against known truth, and the mineral test that failed.
5. Finding — Da Qaidam, a known Mars analog that also fits the Moon Base ridge
   (`docs/figures/fig_region_matrix.png`); Peary Land marginal.
6. Limits — sample not census, footprint not region, polar Sun 28 % vs 100 %.
7. Value — a test protocol per site (`docs/figures/fig_transfer_matrix.png`), links, data, SI use.

## Optional 30-second video (the slide deck already satisfies the demo rule)
See `docs/video_script.md` for the shot list, on-screen text and narration. If made, it must be
30 s or less, English (or English subtitles), hosted publicly with no login.
