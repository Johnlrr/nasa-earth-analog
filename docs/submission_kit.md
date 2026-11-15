# Submission kit — text ready to paste (team must read, edit and own it)

Prepared 15/11 as a draft for the two team members. Every number carries its key in
`docs/slide_numbers.json` as [`key` = value]; a test fails if a value drifts
(`tests/test_mission_value.py`). Remove the bracketed keys when pasting. Wording rules that are
part of the result are at the top of `docs/slides_draft.md`.

**Two things only the team can do, and both can decide whether the entry is valid:**
1. Read the official Space Apps texts on AI use and sign `docs/compliance.md`. The AI statement
   below is a factual draft; section 5 has a blank the team must fill truthfully (who originated
   the core idea).
2. Open `web/index.html` and `web/evidence.html` in a browser before submitting: the evidence
   page was generated on a machine without a browser and has not been looked at.

---

## 1. High-level summary (about 150 words)

Space agencies test Moon and Mars hardware at Earth "analog" sites, usually chosen because they
are famous or look right. SIMILITUDE asks the engineer's question instead: which test results
transfer? One formula is run on NASA data from both worlds, per mission test, and every site
gets a card that says what a field test there reproduces, what no Earth site reproduces (and
which facility replaces it) and what cannot be judged. For the Moon Base ridge (Connecting
Ridge), **76 %** of the terrain is steeper than 8° [`cr_frac_gt8` = 0.758]; in the footprints of
six classic analog field sites the median is **9 %** [`classic_frac_gt8_median` = 0.089]. From
196,008 bare-land cells we screened 300; two footprints match the ridge in that sample, and one
of them — Da Qaidam, a known Mars analog region — also survives a second, independent NASA
elevation model and matches **3 of 6** south-pole sites [`regions_matched_da_qaidam` = 3]. We also report what failed: our mineral
test did not pass its own pre-registered rule, so we publish no mineral analog.

## 2. How it addresses the challenge

- **Moon Base locations:** terrain for touchdown and traverse, and low-Sun shadows, scored
  against NASA's LOLA south-pole elevation models (PGDA 78: Connecting Ridge, Shackleton and four
  more sites).
- **Mars:** ice under dry soil (Arcadia Planitia, NASA SWIM) and aqueous minerals (Jezero, Nili
  Fossae; MRO CRISM against NASA EMIT).
- **Earth locations, with reasons:** each site is tied to the test it supports, read beside
  published NASA numbers — Artemis III "Surface slope for landing (100m): <10 deg" and "Surface
  slope limit for EVA (2km): <20 deg" (NASA NTRS 20250009323); Mars Life Explorer "land within a
  vertical meter of Martian mid-latitude ice, drill for samples to a 2-meter depth".
- **What a mission team gets:** a test protocol per site (systems to test, what to measure, what
  the site does not reproduce). By our measure a terrain site reproduces **1 of 7** test
  variables [`coverage_L1_transfers` = 1, `coverage_L1_total` = 7]; the card names the facility
  for the others.

## 3. How we know it is not noise

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

## 4. Limits we state ourselves

- Counts come from a **307**-cell sample screened towards Connecting Ridge
  [`l1_cells_scored_rank_seed` = 307], not a census: about **201** bare-land cells (95 % CI
  10–1,093) would pass the terrain test [`prevalence_connecting_ridge_cells` = 201,
  `prevalence_connecting_ridge_cells_lo` = 10, `prevalence_connecting_ridge_cells_hi` = 1093].
- A match is one 4 km footprint, not a region; slopes are computed on a 30 m baseline and compare
  Earth with Moon, not with NASA's landing maps.
- The terrain test recognises a terrain class, not a named place: on the Moon it separates the
  steep wall from ridge terrain but not the ridge, rim and massif sites from one another.
- No Earth site reproduces the polar Sun: the best has the Sun below 7° for **28 %** of daylight,
  the lunar target for **100 %** [`l2_earth_best_lowsun_frac_daylight` = 0.277,
  `l2_moon_lowsun_frac_daylight` = 1.0].
- The ice lens is semi-quantitative (reanalysis soil temperature, thresholds set after seeing
  data); metre-scale boulders are below our resolution.

## 5. Use of AI — factual draft, to be checked against the official rules by the team

We used AI assistants (Anthropic Claude models through Claude Code; Google Gemini models through
the Antigravity IDE) throughout: to draft and review planning documents, to write and test code,
to run and check analyses, to search and read the literature, to draft the validation report,
the slide text and this page, and to act as an adversarial reviewer before each merge. AI
assistants also proposed analysis directions that we adopted (presenting results by field site,
reading results beside published NASA requirements, the checks with a second elevation model
and a larger random sample). All data are NASA and partner open data, processed by the open code
in the repository; every threshold, control and rule change is recorded with its date and
reason. No AI-generated images, audio or video are used.

Core idea (judging analog sites by which test results transfer, per mission test):
⟨the team states here, truthfully, who originated it and how AI was involved⟩.

## 6. Data and references (short list; full table in README)

NASA PGDA Product 78 (LOLA south-pole DEMs and slopes) · NASA EMIT L2A · MRO CRISM MICA type
spectra · NASA SWIM (Morgan et al. 2021) · MODIS · ASTER GED · NASADEM · NASA NTRS 20250009323
and 20240009596 (Artemis III landing requirements) · Mars Life Explorer mission concept study ·
NASA TRL definitions · NASA SVS 14583 (JETT5) · Copernicus DEM GLO-30 · ESA WorldCover ·
Sentinel-2 · ERA5-Land · TerraClimate · ArcticDEM · OpenAlex · OpenStreetMap Nominatim.

## 7. Seven slides in one line each (full text and keys: `docs/slides_draft.md`)

1. Cover — "Famous ≠ faithful": a test-transfer matrix for the Moon Base and Mars.
2. Problem — six famous analog field sites are too flat for the Moon Base ridge
   (`docs/figures/fig_mission_slopes.png`).
3. Method — one formula, two worlds, three verdicts.
4. Trust — five checks and the failed test we report.
5. Finding — Da Qaidam, a Mars analog that fits the Moon Base ridge
   (`docs/figures/fig_region_matrix.png`).
6. Product — a test protocol per site (`docs/figures/fig_transfer_matrix.png`).
7. Data, licence, AI use, limits.

## 8. Thirty-second video script

0–8 s: one bar chart. "Six famous analog sites: 9 % of their terrain is steeper than 8°. The
Moon Base ridge: 76 %."
8–20 s: map zooms to Qinghai. "One footprint matches — Da Qaidam, a Mars analog. It survives a
second NASA elevation model." Card appears: terrain TRANSFERS; gravity NO-ANALOG → offload rig.
20–30 s: "Earth's best site has the polar Sun for 28 % of daylight; the Moon, 100 %. We say what
cannot transfer." URL.
