# SIMILITUDE — slide draft (B12, English, 7 slides incl. cover)

Status: **draft**. Every number must be re-checked against `docs/validation_report.md` (A9) before
submission (PLAN B12). Numbers marked ⟨prov⟩ come from the provisional diagonal scorer
(`scripts/provisional/score_b.py`) and will change when the A5/A8 engine runs. ⟨TBD-A⟩ = waiting for
Bao's L1/L2 results. Keep each slide to one idea + one figure.

---

## Slide 1 — Cover
**SIMILITUDE — the proving-ground finder**
*Same formula, both worlds. Per mission task. And we say exactly what cannot transfer.*
Challenge: Identify Earth Locations that Analog the Permanent Moon Base Locations and Mars ·
Team: ⟨team name⟩ · NASA Space Apps 2026, Ho Chi Minh City
Visual: wind-tunnel model ↔ Moon/Mars split image.

## Slide 2 — The problem: analogs chosen by eye
- Analogs are **test fixtures**: a site is useful only if a specific test's result transfers.
- Picking sites by looks fails: an image-texture ranking (NHSJS 2026) put **Devon Island — NASA's
  Haughton-Mars Project — last**.
- Four classic sites (Antarctica, Atacama, Iceland, Hawaii) dominate the literature
  (Atacama: **223** analog papers in OpenAlex vs **0** for Harrat Khaybar).
- No open, quantitative, per-mission tool exists (Preston et al. 2013; USGS analog survey 2026).
Visual: Wadi Rum (looks like Mars) next to Mars.

## Slide 3 — Method: one formula, two worlds, four mission lenses
- **Lenses:** L1 Touchdown & Traverse (Moon), L2 Low-Sun Navigation (Moon), M1 Aqueous Minerals
  (Mars), X1 Ice under Dry Overburden (Mars).
- **Twin formulas** (one library, `src/similitude/descriptors/`): slope / roughness spectrum
  at a common baseline (LOLA/PGDA ↔ Copernicus DEM); CRISM summary parameters
  (Viviano-Beck 2014) on **MRO CRISM MICA** and on **NASA EMIT** with the same code; ice
  configuration (SWIM ↔ ERA5-Land / MODIS).
- **Fidelity = σ-dissimilarity** (climate-analog statistics, Mahony 2017), scaled by natural
  variation among the target sites; ranking on raw distance; percentile vs a random null sample.
Visual: data-flow diagram (NASA data on both sides → same functions → σ).

## Slide 4 — Validation before discovery
- Expectations for every control **written before results** (`config/controls.yaml`).
- M1 ⟨prov⟩: Wadi Rum decoy ("Hollywood's Mars") lands at the **22nd percentile** — fails the
  mineral test as expected; Rio Tinto (jarosite analog) at **98.5th** vs Meridiani.
- X1 ⟨prov⟩: Beacon Valley (Antarctic buried ice) ranks **4 / 125**.
- Reported failures, not hidden: Lake Salda (NASA pair for Jezero) only **12th percentile**
  (5 km footprint mostly lake; 142 usable pixels); Simpson red-sand decoy scores high for
  Oxia/Meridiani; Jezero carbonate has **no Earth match within 2σ** (best: Semail ophiolite,
  4.1σ).
- L1/L2 controls (Haughton, SP Crater) ⟨TBD-A⟩; ablation RGB vs twin-formula ⟨TBD-A⟩.
Visual: percentile bars for controls vs decoys.

## Slide 5 — Hidden analogs (engine-found, low attention)
| Site | Lens / target | σ ⟨prov⟩ | Percentile | Papers |
| :--- | :--- | ---: | ---: | ---: |
| Harrat Rahat, Saudi Arabia | M1 / Oxia Planum (ESA landing site) | 0.24 | 100 | 0 |
| Harrat Khaybar, Saudi Arabia | M1 / Oxia Planum | 0.63 | 100 | 0 |
| Pinacate, Mexico | M1 / Oxia Planum | 2.00 | 98.5 | 1 |
| Mackenzie King Island, Canada | X1 / Arcadia Planitia (semi-quant.) | 2.44 | 98.1 | 1 |
| ⟨L1/L2 site⟩ | ⟨TBD-A⟩ | | | |
Honest caveat on the slide: M1 matches are driven by the **basaltic host** of the Mars spectra,
not by water-altered minerals — exactly what the limiting-factor column says.
Visual: map with Test Card thumbnails.

## Slide 6 — The product: Analog Test Card + Transfer Ledger
- Web app (static, GitHub Pages): pick a lens → map of hidden analogs, controls, decoys →
  Test Card: σ, percentile, per-descriptor radar, limiting factor, what to test here.
- **Transfer Ledger (numbers, sourced):** gravity 0.165 g (Moon) / 0.38 g (Mars); pressure
  3×10⁻¹⁵ bar / 0.636 kPa; surface dose **1.37 mSv/day** (Chang'e-4) / **0.67 mSv/day** (MSL RAD)
  vs 2.4 mSv/yr on Earth; linked to NASA Moon-to-Mars technology gaps (#0301 lunar night,
  #0603 water from regolith/ice, #0805 surface mobility).
- QR → ⟨Pages URL⟩
Visual: screenshot of a Test Card.

## Slide 7 — Data, licence, SI use, limits
- NASA: EMIT L2A, MRO CRISM (MICA), CTX via Mars Trek, LRO/LOLA + PGDA 78, MODIS, ASTER GED,
  SWIM. Partners/open: Copernicus DEM, ESA WorldCover, ERA5-Land, TerraClimate, OpenAlex.
- Limits: EMIT ±52° only; 1.4/1.9 µm bands hidden by Earth's air; Mars I/F vs Earth reflectance
  compared by band shape only; X1 semi-quantitative; sub-pixel analogs (caves, small craters) out
  of reach.
- Code Apache-2.0: ⟨repo URL⟩. SI disclosure: ⟨from docs/compliance.md after G0⟩.

---
### 30-second video alternative (if 0.1 chooses video)
0–8 s Wadi Rum beside Mars, "looks identical" → mineral score bar drops (22nd pct).
8–18 s Harrat Khaybar, unremarkable photo → score jumps (σ 0.6), "0 papers".
18–30 s Test Card + Transfer Ledger: "what transfers, what never can" → URL.
