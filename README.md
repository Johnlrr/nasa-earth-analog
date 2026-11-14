# SIMILITUDE — the proving-ground finder

NASA Space Apps Challenge 2026. SIMILITUDE looks for Earth field sites where a Moon or Mars
**test result would transfer**, judged by physics rather than by how a place looks. Wind-tunnel
engineers do not ask whether a model looks like the aircraft; they ask whether the dimensionless
numbers match. We apply the same idea to planets:

- **Same formula, both worlds.** Every descriptor (slope distribution, multi-scale roughness,
  Hurst exponent, terrain shadows, Sun geometry, CRISM summary parameters, ice configuration) is
  computed by one shared library on NASA data from the target body and on Earth data, at a common
  spatial baseline.
- **Fidelity is per mission task.** Four *lenses*: L1 Touchdown & Traverse (Moon south pole:
  Connecting Ridge, Shackleton), L2 Low-Sun Navigation (Moon), M1 Aqueous Minerals (Mars: Jezero,
  Nili Fossae), X1 Ice under Dry Overburden (Mars: Arcadia Planitia). No overall score.
- **The gap is a deliverable.** Every site card has three parts: **Field** (what transfers),
  **Facility** (what no Earth site can reproduce, and which facility to use instead: offload rig,
  thermal-vacuum chamber, CO₂ chamber…), **Unobserved** (what this engine cannot tell).

Main results and every rule changed after seeing data: [`docs/validation_report.md`](docs/validation_report.md).
Site cards: [`docs/field_facility.md`](docs/field_facility.md). Web map: `web/` (static, GitHub Pages).

## Quick start

Requires Python ≥ 3.11.

```bash
git clone <this repo> && cd nasa-earth-analog
python -m venv .venv && .venv/bin/pip install -e ".[dev]"      # or: make venv  (uses uv)
.venv/bin/python -m pytest -q                                   # or: make test
.venv/bin/python -m ruff check .                                # or: make lint
```

The derived tables in `data/derived/` are committed, so the tests, the report tables and the web
data rebuild without downloading anything:

```bash
.venv/bin/python scripts/l1_robust.py        # A12 robust terrain set
.venv/bin/python scripts/build_verdicts.py   # single verdict source: data/derived/verdicts.parquet
.venv/bin/python scripts/sites.py --no-attention   # sites, scarcity, multi-lens, field/facility cards
.venv/bin/python scripts/report_tables.py    # refresh every table in docs/validation_report.md
.venv/bin/python scripts/discovery/run_discovery.py   # web/data/candidates.geojson
python -m http.server -d web 8000            # open http://localhost:8000
```

Recomputing descriptors from raw data needs a Google Earth Engine account
(`earthengine authenticate`, then `export EE_PROJECT=<your project>`), the NASA PGDA Product 78
DEMs in `data/raw/moon/pgda78/`, and network access to OpenAlex and OpenStreetMap Nominatim.
Full pipeline: `scripts/gee/tier1_terrain.py` → `scripts/select_tier2.py` →
`scripts/build_earth_L1.py` → `scripts/build_L2.py` → `scripts/run_all.py` (fidelity, null,
controls, bridge bias) → the commands above. The spectral lens (M1) runs from
`scripts/emit/` (pixel matching, `pixel_m1.py`).

## Repository map

| Path | What |
|---|---|
| `src/similitude/descriptors/` | the shared descriptor library (terrain, spectral, ice) — the only place formulas live |
| `src/similitude/fidelity.py` | Mahalanobis distance, native rank, limiting factor, null percentile |
| `config/` | lenses, targets, controls and decoys, seeds, site contract (`sites.yaml`), B10 review |
| `ledger/` | Transfer Ledger: Moon/Mars vs Earth physics with a source for every number |
| `scripts/` | pipeline steps (see above) |
| `data/derived/` | committed result tables (parquet / json) |
| `docs/` | validation report, field/facility cards, G1 review, compliance notes |
| `web/` | static map and Test Cards |

## Data

NASA and partner-agency data (all open):

| Dataset | Used for | Reference |
|---|---|---|
| NASA PGDA Product 78 — LOLA 5 m south-pole DEMs and slopes (Artemis candidate regions) | Moon targets and population (L1, L2) | https://pgda.gsfc.nasa.gov/products/78 |
| NASA EMIT L2A surface reflectance (via Google Earth Engine `NASA/EMIT/L2A/RFL`) | Earth spectra (M1) | doi:10.5067/EMIT/EMITL2ARFL.001 |
| MRO CRISM MICA type spectra, PDS volume MROCR_8001; summary parameters of Viviano-Beck et al. 2014 | Mars targets (M1) | https://pds-geosciences.wustl.edu/missions/mro/crism.htm ; doi:10.1002/2014JE004627 |
| SWIM — Subsurface Water Ice Mapping on Mars (Morgan et al. 2021) | Mars ice configuration (X1) | doi:10.1038/s41550-020-01290-z ; https://swim.psi.edu |
| MODIS MOD11A1 v061 land surface temperature | freeze–thaw days (X1) | doi:10.5067/MODIS/MOD11A1.061 |
| MODIS MOD13A2 v061 NDVI | bare-land mask | doi:10.5067/MODIS/MOD13A2.061 |
| MODIS MOD10A1 v061 snow cover | snow-free fraction (L2) | doi:10.5067/MODIS/MOD10A1.061 |
| ASTER GED AG100 v003 | mafic index (M1 coarse tier) | doi:10.5067/Community/ASTER_GED/AG100.003 |
| NASA planetary fact sheets; Chang'e-4 LND and MSL RAD dose papers | Transfer Ledger | URLs/DOIs per row in `ledger/*.yaml` |
| Copernicus DEM GLO-30 (ESA) | Earth terrain (L1, L2) | doi:10.5270/ESA-c5d3d65 |
| ESA WorldCover v200 | bare-land mask, water, perennial ice (A13) | doi:10.5281/zenodo.7254221 |
| Copernicus Sentinel-2 L2A (`COPERNICUS/S2_SR_HARMONIZED`) | visual review contact sheets | Copernicus Sentinel data 2022–2024 |
| ERA5-Land monthly (Copernicus C3S) | soil temperature, thaw degree-days (X1) | doi:10.24381/cds.68d2bb30 |
| TerraClimate (Abatzoglou et al. 2018) | aridity P/PET (X1) | doi:10.1038/sdata.2017.191 |
| OpenAlex | Analog Attention Index (literature count) | https://openalex.org |
| OpenStreetMap Nominatim (© OpenStreetMap contributors, ODbL) | place names | https://nominatim.org |

## Known limits

- **Hydration bands at 1.4 and 1.9 µm**, where CRISM is most sensitive, are hidden by Earth's
  atmosphere in EMIT; serpentine and Mg-carbonate cannot be told apart with the 2.3 µm feature
  alone. EMIT covers only about ±52° latitude, so the spectral lens does not reach polar sites.
- **M1 failed its pre-registered stop rule** (the positive control Lake Salda reaches 0.052 km² of
  matched area < 0.1 km²): no aqueous-mineral analog is published; M1 is shown as a method
  illustration only.
- **Below-pixel analogs** are unobserved: boulders and craters < 60 m (L1), horizon occlusion
  beyond 10 km (L2), radar/GPR response of the overburden (X1), lava-tube ice caves.
- **X1 is semi-quantitative**: reanalysis soil temperature and clear-sky MODIS; condition floors
  set after seeing data and calibrated on Beacon Valley.
- **Counts are of the scored sample** (300 cells ranked from 196,008 bare-land cells by a coarse
  screen, plus seeds and controls), not a global census.
- **Attention** is an OpenAlex title/abstract count; a count of 0 for an administrative place name
  is not evidence that a site is unknown to the analog community.

## Use of AI (Super Intelligence) tools

We used AI assistants — Anthropic Claude models through Claude Code, and Google Gemini models
through the Antigravity IDE — to help draft planning documents, write and test code, review plans
and diffs, and search the literature. All data processing runs on NASA and partner data with the
open code in this repository. Every scientific threshold, control site and expectation is recorded
in `PLAN.md` / `config/` with its reason and whether it was fixed before or after seeing results
(see the Deviations table in `docs/validation_report.md`). The team directed, checked and edited
all work. No AI-generated images, voices or videos are used in the demo. Details and the
compliance checklist: [`docs/compliance.md`](docs/compliance.md).

## License

Apache-2.0 — see [LICENSE](LICENSE). Third-party data keep their own licences (see the table
above).
