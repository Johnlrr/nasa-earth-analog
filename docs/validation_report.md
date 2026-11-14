# Validation report — SIMILITUDE engine (draft, 2026-11-14 16:45 UTC+7)

Reproduce: `.venv/bin/python scripts/run_all.py` (≈ 11 s once the derived tables exist).
Tables: `data/derived/fidelity.parquet`, `validation_controls.parquet`, `validation_null.parquet`,
`validation_sensitivity.parquet`. Figures: `docs/figures/validation_controls_<lens>.png`.

**Reading the numbers.** `d` is the Mahalanobis distance from an Earth cell to the planetary target,
in units of the natural site-to-site variation on the target body (floored by physical tolerances in
`config/lenses.yaml`). `sigma` converts `d` to a one-dimensional equivalent (Mahony et al. 2017);
`sigma = 0` means "indistinguishable from the target's own natural variability". `percentile` is the
share of randomly drawn bare-land cells (stratified null sample, never ranked) that are farther from
the target than the cell; 100 = closer than every random cell. Expectations (`high` / `uncertain` /
`low`) were written in `config/controls.yaml` before any score existed and were not changed afterwards.

## 1. Headline results

| Lens | Target | Does the engine find anything? | Pre-registered checks |
| :--- | :--- | :--- | :--- |
| L1 Touchdown & Traverse (Moon) | Connecting Ridge | **Yes.** Ranked cells: median d 3.98 vs 10.33 for random bare land; the best cells reach σ = 0 | Haughton (`high`) **missed** (81.5th pct); SP Crater (`uncertain`) 96.5th pct |
| L2 Low-Sun Navigation (Moon) | Connecting Ridge | **No natural analog** for the sun geometry (best σ = 13.9), as pre-registered. Terrain-shadow part alone: best σ_shadow = 0.49 | Haughton (`high`) missed; Sahara decoy (`low`) not separated — all cells are far on the astro axis |
| M1 Aqueous minerals (Mars) | Jezero margin | **No analog under σ = 2** (best: Semail ophiolite seed, σ = 4.1) | Lake Salda (`high`) **missed** (11.6th pct); Wadi Rum decoy passed; Simpson Desert decoy **failed** (73.9th pct) |
| X1 Ice under dry overburden (Mars) | Arcadia Planitia | Semi-quantitative; best σ = 2.07 | Beacon Valley (`high`) passed (98.1th pct); Axel Heiberg (`high`) missed (46.3th pct) |

The honest summary: **the terrain lens works and discriminates; the spectral lens does not yet
validate against its own positive control.** Both statements are reported as they came out.

## 2. L1 — Touchdown & Traverse (Connecting Ridge, PGDA 78 Site01)

- Population for Σ: 54 non-overlapping 4 km footprints across six Artemis candidate sites
  (PGDA Product 78, 5 m LOLA DEM aggregated to 30 m). 11 descriptors > n/5, so the engine used the
  diagonal metric with physical floors.
- Earth sample: 300 ranked cells (coarse GEE screen, NMS 30 km), 200 stratified random bare-land
  cells (null), 5 pre-registered controls, 6 hypothesis seeds; 30 m Copernicus GLO-30 chips,
  4 km footprint + 3 km buffer — the same rule as on the Moon.
- **The coarse screen works:** median d — ranked 3.98, controls 6.63, seeds 6.81, null 10.33.
- **Top cells outside the classic-analog exclusion zones** (σ = 0, i.e. inside the natural spread of
  the lunar candidate sites; region names approximate, to be checked on imagery):
  81.0°N 71.2°W (northern Ellesmere Island), 80.1°N 20.7°W (NE Greenland), 33.5°N 84.2°E (Changtang,
  Tibet), 19.8°S 68.9°W (Bolivian Altiplano), 11.7°S 77.1°W (Peruvian Andes), 32.9°N 78.6°E
  (Ladakh / Aksai Chin), 68.6°N 69.1°W and 71.3°N 75.2°W (Baffin Island).
- **Seeds:** Peary Land 95.5th pct (σ 1.5), Harrat Khaybar 93.5th (σ 2.5), Roter Kamm 89.5th,
  Tenoumer 82.5th, Wolfe Creek 51st. **Karakul (3.5th pct) is a data artifact:** the seed coordinate
  falls on the lake surface (slope 0°); it must be moved to exposed ground before it means anything.
- **Haughton (`high`) missed:** slope median 3.2° vs 12.4° at Connecting Ridge; limiting factor
  `frac_gt8`. Haughton is a geology/operations analog, not a steep-ridge terrain analog. This was the
  team's expectation error, kept as is.
- **Sensitivity:** dropping one descriptor changes the top-10 a lot (median Jaccard 0.18) because
  dozens of cells sit at d ≈ 1, i.e. they are equally good within the Moon's own variability. Report
  the *set* of cells with σ ≈ 0, not a fixed ranking.

## 3. L2 — Low-Sun Navigation

- Same chips; descriptors: sun-geometry (`lowsun_frac_daylight`, `lowsun_az_coverage`, same formula
  with obliquity 1.54° for the Moon and 23.44° for Earth) + terrain shadows at 2/5/7° sun elevation.
- **No Earth analog for the sun geometry** (best σ = 13.9 at 71°N): at the lunar south pole the Sun is
  always within 7° of the horizon; on Earth that needs latitudes ≥ ~83–86°, where there is almost no
  bare land. This was pre-registered as the likely outcome and is the result to show as a number.
- **Shadow terrain alone** has good analogs (σ_shadow 0.5–1.7): Baffin Island (71°N), Changtang,
  southern Patagonia (49°S) — places to test shadow-handling perception with real long shadows, while
  the lighting rig has to be done in a facility.
- Pre-registered checks are not informative here: everything is far on the astro axis, so neither the
  Haughton control nor the Sahara decoy separates.

## 4. M1 — Aqueous minerals (owner: Linh; scored with the shared engine)

- Best vs Jezero margin: Semail ophiolite (Oman) seed, σ = 4.1 → formally **no analog** (σ > 2).
- Lake Salda (`high`, NASA Analog Explorer's Jezero analog) ranks 103/118 (11.6th pct); its limiting
  factor is `BD2250`. Simpson Desert red quartz dunes (decoy, `low`) rank 32/118. Wadi Rum (decoy)
  correctly ranks low.
- Likely causes to investigate (Linh's lane, before Data Freeze): MICA ratioed vs numerator spectra,
  water/moisture contamination of the Lake Salda footprint, the narrow population (29 MICA spectra
  spanning many mineral classes), and EMIT channel noise near 2.25–2.5 µm.

## 5. X1 — Ice under dry overburden (semi-quantitative)

- Beacon Valley, Antarctica (`high`) 98.1th pct — passes; Axel Heiberg/Eureka (`high`) 46.3th pct —
  misses. Population is only 5 Mars footprints (diag metric); evidence status stays `engine-semiquant`.

## 6. Not done / limitations

- Ablation (a) RGB/texture baseline: not run (no LROC chips on the Moon side; see PLAN log).
- Baseline change (L = 60 m) sensitivity: not run yet.
- L1/L2 tier-1 slopes come from GEE (`ee.Terrain.slope`) and differ by ~15–20 % from the shared
  library on the same cell; they are used only for preselection, never for published numbers.
- Region names in §2–3 are from coordinates and must be confirmed on imagery before slides.
