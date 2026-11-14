# Field / Facility split for showcase sites (PLAN 2c, A18–A20)

Generated 2026-11-15 01:03 by `scripts/sites.py` from `verdicts.parquet` (A15) and `cell_profiles.parquet` (A13); contract and showcase rule in `config/sites.yaml`. Post hoc grouping: no threshold or verdict changed. Sites are single-linkage clusters of engine-kept cells at 150 km, without ice-excluded cells. Showcase: (a) a Connecting Ridge TRANSFERS cell not downgraded by B10, (b) a multi-lens partner, (c) the largest site outside exclusion buffers.

## Target scarcity (A18)

Both columns of a comparison must use the same filter (e.g. *usable* vs *usable*). The comparison also reflects how unusual each lunar target is within its own population (native rank threshold n/2), not only rarity on Earth. Counts are of the scored sample: 300 rank cells = top 300 of 196,008 bare-land cells by a coarse sigma against Connecting Ridge on coarse slope/relief, plus seeds (screened towards Connecting Ridge at 90 m, not on the fine-scale full metric that binds it). The Shackleton inner wall is a steep comparison slope, not a Moon Base site.

| Lens | Target | TRANSFERS cells | ice ok / flag / excluded | usable | usable outside known-analog buffers | sites | usable, not B10-downgraded (incl. unreviewed) | of which B10-unreviewed |
|---|---|---|---|---|---|---|---|---|
| L1 | Connecting Ridge (Site01) | 5 | 1 / 1 / 3 | 2 | 2 | 2 | 2 | 2 |
| L1 | Shackleton inner wall (Site04 centre) | 99 | 90 / 3 / 6 | 93 | 54 | 27 | 93 | 90 |
| L2 | Connecting Ridge (Site01) | 3 | 2 / 0 / 1 | 2 | 1 | 2 | 1 | 1 |
| L2 | Shackleton inner wall (Site04 centre) | 7 | 5 / 1 / 1 | 6 | 4 | 5 | 4 | 2 |

## Da Qaidam, northern Qaidam Basin margin (Qinghai)

`site:E10K_453_921` · 38.64, 96.00 · 2 member cell(s) · span 143 km · ice ok/flag 2/0 · in known-analog buffer 0 · Attention unknown · hidden: unknown: attention not known · showcase rule a

Engine-confirmed: **L1** · not yet visually reviewed (B10): E10K_453_921,E10K_465_927

> Qaidam is a well-known Mars analog region (Dalangtan playa); new here is only its match to Connecting Ridge terrain. Not presented as hidden.

**Field — test here (transfers)**

- L1 Touchdown & Traverse · Connecting Ridge (Site01) · `slope_roughness` · 1 cell(s), best E10K_453_921: A12 robust set (intersection (i)&(ii)&(iii)); native rank i/ii/iii = 43/36/41 of 49
- L1 Touchdown & Traverse · Shackleton inner wall (Site04 centre) · `slope_roughness` · 1 cell(s), best E10K_465_927: A12 robust set (intersection (i)&(ii)&(iii)); native rank i/ii/iii = 29/38/32 of 49

**Facility — cannot test here**

- L1 · all targets · `gravity` → Reduced-gravity offload rig, parabolic flight ([source](https://nssdc.gsfc.nasa.gov/planetary/factsheet/moonfact.html))
- L1 · all targets · `angle_of_repose` → Parabolic-flight drum tests or gravity-offload slope tests with the actual simulant ([source](https://doi.org/10.1029/2011JE003865))
- L1 · all targets · `atmospheric_pressure` → Thermal-vacuum chamber with regolith simulant ([source](https://nssdc.gsfc.nasa.gov/planetary/factsheet/moonfact.html))
- L1 · all targets · `radiation_dose` → Accelerator or isotope-source irradiation of components ([source](https://doi.org/10.1126/sciadv.aaz1334))
- L1 · all targets · `regolith_dust` → Use lunar simulant under vacuum; do not claim wear or adhesion results from field soil ([source](https://ntrs.nasa.gov/api/citations/20205001806/downloads/CJW%20PIO%20Dust%20Manuscript_V011.docx.pdf))

**Unobserved — this engine cannot say**

- L1 · `Metre-scale boulders and craters < 60 m`: below the 30 m DEM baseline on both sides (LOLA 5 m maps cannot resolve 1-2 m boulders either)

## Mauna Loa – Mauna Kea, Hawaiʻi

`site:E10K_244_-1498` · 19.45, -155.50 · 1 member cell(s) · span 0 km · ice ok/flag 1/0 · in known-analog buffer 1 · Attention unknown · hidden: no: inside known-analog buffer · showcase rule a

Engine-confirmed: **L2** · not yet visually reviewed (B10): E10K_244_-1498

> Known analog region (inside exclusion buffer).

L2 cells, snow-free fraction of the year (MODIS; seasonal snow is the risk that downgraded Gêrzê): E10K_244_-1498 0.62

**Field — test here (transfers)**

- L2 Low-Sun Navigation · Connecting Ridge (Site01) · `shadow_casting` · 1 cell(s), best E10K_244_-1498: native rank (d_shadow) 45 of 49; sigma_shadow 0.13

**Facility — cannot test here**

- L2 · all targets · `gravity` → Reduced-gravity offload rig, parabolic flight ([source](https://nssdc.gsfc.nasa.gov/planetary/factsheet/moonfact.html))
- L2 · all targets · `atmospheric_pressure` → Thermal-vacuum chamber with regolith simulant ([source](https://nssdc.gsfc.nasa.gov/planetary/factsheet/moonfact.html))
- L2 · all targets · `day_night_cycle` → Thermal-vacuum cycling of hardware ([source](https://nssdc.gsfc.nasa.gov/planetary/factsheet/moonfact.html))
- L2 · all targets · `radiation_dose` → Accelerator or isotope-source irradiation of components ([source](https://doi.org/10.1126/sciadv.aaz1334))
- L2 · all targets · `temperature` → Cryogenic test bench for ice-regolith drilling and mobility ([source](https://ntrs.nasa.gov/citations/20110011329))
- L2 · all targets · `diffuse_skylight` → Add artificial single-source lighting with black enclosures, or night tests ([source](https://science.nasa.gov/moon/sun-and-weather-overview/weather-on-the-moon/))
- L2 · Connecting Ridge (Site01) · `sun_geometry` → High-latitude summer field site or lighting rig for the solar geometry (source: engine: data/derived/verdicts.parquet (A15) / fidelity.parquet)

**Unobserved — this engine cannot say**

- L2 · `Horizon occlusion beyond 10 km`: shadows are computed inside the 10 km chip only, on both sides

## Peary Land, North Greenland

`site:E10K_729_-319` · 82.62, -33.07 · 1 member cell(s) · span 0 km · ice ok/flag 0/1 · in known-analog buffer 0 · Attention unknown · hidden: unknown: attention not known · showcase rule a,b

Engine-confirmed: **L1** · engine-semiquant: **X1** · not yet visually reviewed (B10): E10K_729_-319

> DESIGN 2.5 #6 proposed Peary Land for L2 (low Sun); the engine does NOT confirm L2 there (sun geometry is NO-ANALOG everywhere). It confirms L1 instead, through a rank cell found by the coarse screen (not the seed), 20 km from the X1 seed, and X1, which is only engine-semiquant (condition floors set after seeing data, calibrated on Beacon Valley; the X1 seed list was committed together with the first X1 scores, so it is not provably pre-registered). The L1 cell carries an ice flag (0.15). Unique only within the scored sample (X1 has 8 cell-level TRANSFERS, M1 none).

**Field — test here (transfers)**

- L1 Touchdown & Traverse · Connecting Ridge (Site01) · `slope_roughness` · 1 cell(s), best E10K_729_-319: A12 robust set (intersection (i)&(ii)&(iii)); native rank i/ii/iii = 43/26/44 of 49
- X1 Ice under Dry Overburden · Arcadia Planitia · `ice_configuration` · 2 cell(s), best seed_peary_land: all 3 conditions met (permafrost, no thaw to ice, dry overburden) (thresholds set after seeing data)
- X1 Ice under Dry Overburden · all targets · `day_night_cycle`: Day length is nearly Earth-like and transfers well; the colder, thin-air thermal cycling does not.

**Facility — cannot test here**

- L1 · all targets · `gravity` → Reduced-gravity offload rig, parabolic flight ([source](https://nssdc.gsfc.nasa.gov/planetary/factsheet/moonfact.html))
- L1 · all targets · `angle_of_repose` → Parabolic-flight drum tests or gravity-offload slope tests with the actual simulant ([source](https://doi.org/10.1029/2011JE003865))
- L1 · all targets · `atmospheric_pressure` → Thermal-vacuum chamber with regolith simulant ([source](https://nssdc.gsfc.nasa.gov/planetary/factsheet/moonfact.html))
- L1 · all targets · `radiation_dose` → Accelerator or isotope-source irradiation of components ([source](https://doi.org/10.1126/sciadv.aaz1334))
- L1 · all targets · `regolith_dust` → Use lunar simulant under vacuum; do not claim wear or adhesion results from field soil ([source](https://ntrs.nasa.gov/api/citations/20205001806/downloads/CJW%20PIO%20Dust%20Manuscript_V011.docx.pdf))
- X1 · all targets · `gravity` → Reduced-gravity offload rig, parabolic flight ([source](https://nssdc.gsfc.nasa.gov/planetary/factsheet/marsfact.html))
- X1 · all targets · `angle_of_repose` → Parabolic-flight drum tests with the actual simulant ([source](https://doi.org/10.1029/2011JE003865))
- X1 · all targets · `atmospheric_pressure` → Mars-pressure CO2 chamber ([source](https://nssdc.gsfc.nasa.gov/planetary/factsheet/marsfact.html))
- X1 · all targets · `radiation_dose` → Accelerator or isotope-source irradiation of components ([source](https://swri.org/node/9079))
- X1 · all targets · `temperature` → Cold-chamber tests; polar or high-altitude desert sites only as partial proxies ([source](https://nssdc.gsfc.nasa.gov/planetary/factsheet/marsfact.html))
- X1 · all targets · `perchlorate` → Dope simulant with perchlorate salts ([source](https://experts.arizona.edu/en/publications/detection-of-perchlorate-and-the-soluble-chemistry-of-martian-soi/))

**Unobserved — this engine cannot say**

- L1 · `Metre-scale boulders and craters < 60 m`: below the 30 m DEM baseline on both sides (LOLA 5 m maps cannot resolve 1-2 m boulders either)
- X1 · `Overburden dielectric properties (radar / GPR response)`: no global Earth dataset matched to SWIM radar observables

## Atacama – Puna altiplano (Chile, Argentina, Bolivia)

`site:E10K_-228_-669` · -24.67, -67.94 · 54 member cell(s) · **spans 1108 km: a region, not one camp** · ice ok/flag 53/1 · in known-analog buffer 40 · Attention unknown · hidden: no: inside known-analog buffer · showcase rule b

Engine-confirmed: **L1,L2** · not yet visually reviewed (B10): E10K_-228_-669,E10K_-237_-663,E10K_-254_-662,E10K_-265_-663,E10K_-271_-653,E10K_-275_-644,E10K_-275_-651,E10K_-276_-648,E10K_-278_-653,E10K_-280_-643,E10K_-281_-655,E10K_-284_-646,E10K_-287_-645,E10K_-293_-644,E10K_-300_-679,E10K_-301_-664,E10K_-302_-653,E10K_-305_-634,E10K_-305_-641,E10K_-305_-645,E10K_-305_-656,E10K_-306_-675,E10K_-309_-641,E10K_-314_-649,E10K_-314_-654,E10K_-316_-661,E10K_-317_-650,E10K_-318_-653,E10K_-319_-643,E10K_-319_-663,E10K_-321_-646,E10K_-321_-652,E10K_-324_-648,E10K_-324_-666,E10K_-325_-642,E10K_-325_-654,E10K_-325_-663,E10K_-326_-657,E10K_-327_-645,E10K_-329_-641,E10K_-329_-660,E10K_-331_-646,E10K_-331_-664,E10K_-331_-676,E10K_-333_-657,E10K_-334_-650,E10K_-336_-664,E10K_-338_-656,E10K_-339_-667,E10K_-340_-660,E10K_-341_-657,E10K_-345_-657,E10K_-346_-664 · literature-only: M1

> Classic analog region: 40 of its cells are inside known-analog exclusion buffers. Engine rediscovering it is a sanity check, not a discovery.

L2 cells, snow-free fraction of the year (MODIS; seasonal snow is the risk that downgraded Gêrzê): E10K_-319_-663 0.97, E10K_-336_-664 0.96

**Field — test here (transfers)**

- L1 Touchdown & Traverse · Shackleton inner wall (Site04 centre) · `slope_roughness` · 53 cell(s), best E10K_-336_-664: A12 robust set (intersection (i)&(ii)&(iii)); native rank i/ii/iii = 45/49/47 of 49
- L2 Low-Sun Navigation · Shackleton inner wall (Site04 centre) · `shadow_casting` · 2 cell(s), best E10K_-336_-664: native rank (d_shadow) 49 of 49; sigma_shadow 0.01

**Facility — cannot test here**

- L1 · all targets · `gravity` → Reduced-gravity offload rig, parabolic flight ([source](https://nssdc.gsfc.nasa.gov/planetary/factsheet/moonfact.html))
- L1 · all targets · `angle_of_repose` → Parabolic-flight drum tests or gravity-offload slope tests with the actual simulant ([source](https://doi.org/10.1029/2011JE003865))
- L1 · all targets · `atmospheric_pressure` → Thermal-vacuum chamber with regolith simulant ([source](https://nssdc.gsfc.nasa.gov/planetary/factsheet/moonfact.html))
- L1 · all targets · `radiation_dose` → Accelerator or isotope-source irradiation of components ([source](https://doi.org/10.1126/sciadv.aaz1334))
- L1 · all targets · `regolith_dust` → Use lunar simulant under vacuum; do not claim wear or adhesion results from field soil ([source](https://ntrs.nasa.gov/api/citations/20205001806/downloads/CJW%20PIO%20Dust%20Manuscript_V011.docx.pdf))
- L2 · all targets · `gravity` → Reduced-gravity offload rig, parabolic flight ([source](https://nssdc.gsfc.nasa.gov/planetary/factsheet/moonfact.html))
- L2 · all targets · `atmospheric_pressure` → Thermal-vacuum chamber with regolith simulant ([source](https://nssdc.gsfc.nasa.gov/planetary/factsheet/moonfact.html))
- L2 · all targets · `day_night_cycle` → Thermal-vacuum cycling of hardware ([source](https://nssdc.gsfc.nasa.gov/planetary/factsheet/moonfact.html))
- L2 · all targets · `radiation_dose` → Accelerator or isotope-source irradiation of components ([source](https://doi.org/10.1126/sciadv.aaz1334))
- L2 · all targets · `temperature` → Cryogenic test bench for ice-regolith drilling and mobility ([source](https://ntrs.nasa.gov/citations/20110011329))
- L2 · all targets · `diffuse_skylight` → Add artificial single-source lighting with black enclosures, or night tests ([source](https://science.nasa.gov/moon/sun-and-weather-overview/weather-on-the-moon/))
- L2 · Shackleton inner wall (Site04 centre) · `sun_geometry` → High-latitude summer field site or lighting rig for the solar geometry (source: engine: data/derived/verdicts.parquet (A15) / fidelity.parquet)

**Unobserved — this engine cannot say**

- L1 · `Metre-scale boulders and craters < 60 m`: below the 30 m DEM baseline on both sides (LOLA 5 m maps cannot resolve 1-2 m boulders either)
- L2 · `Horizon occlusion beyond 10 km`: shadows are computed inside the 10 km chip only, on both sides

**Literature-only neighbours (not engine-confirmed)**

- M1 seed Salar de Uyuni margin at 149 km (edge of radius): literature-only (no cell-level TRANSFERS in verdicts.parquet)

## Jebel Akhdar, Hajar Mountains (Oman)

`site:E10K_289_551` · 23.14, 57.27 · 1 member cell(s) · span 0 km · ice ok/flag 1/0 · in known-analog buffer 0 · Attention unknown · hidden: unknown: attention not known · showcase rule b

Engine-confirmed: **L2** · literature-only: M1

> The finding here is L2 (terrain shadows, engine). Semail ophiolite (M1) lies about 106 km away but M1 failed its pre-registered stop rule, so the aqueous-mineral part is literature context only, not a second lens.

L2 cells, snow-free fraction of the year (MODIS; seasonal snow is the risk that downgraded Gêrzê): E10K_289_551 1.00

**Field — test here (transfers)**

- L2 Low-Sun Navigation · Shackleton inner wall (Site04 centre) · `shadow_casting` · 1 cell(s), best E10K_289_551: native rank (d_shadow) 29 of 49; sigma_shadow 0.65

**Facility — cannot test here**

- L2 · all targets · `gravity` → Reduced-gravity offload rig, parabolic flight ([source](https://nssdc.gsfc.nasa.gov/planetary/factsheet/moonfact.html))
- L2 · all targets · `atmospheric_pressure` → Thermal-vacuum chamber with regolith simulant ([source](https://nssdc.gsfc.nasa.gov/planetary/factsheet/moonfact.html))
- L2 · all targets · `day_night_cycle` → Thermal-vacuum cycling of hardware ([source](https://nssdc.gsfc.nasa.gov/planetary/factsheet/moonfact.html))
- L2 · all targets · `radiation_dose` → Accelerator or isotope-source irradiation of components ([source](https://doi.org/10.1126/sciadv.aaz1334))
- L2 · all targets · `temperature` → Cryogenic test bench for ice-regolith drilling and mobility ([source](https://ntrs.nasa.gov/citations/20110011329))
- L2 · all targets · `diffuse_skylight` → Add artificial single-source lighting with black enclosures, or night tests ([source](https://science.nasa.gov/moon/sun-and-weather-overview/weather-on-the-moon/))
- L2 · Shackleton inner wall (Site04 centre) · `sun_geometry` → High-latitude summer field site or lighting rig for the solar geometry (source: engine: data/derived/verdicts.parquet (A15) / fidelity.parquet)

**Unobserved — this engine cannot say**

- L2 · `Horizon occlusion beyond 10 km`: shadows are computed inside the 10 km chip only, on both sides

**Literature-only neighbours (not engine-confirmed)**

- M1 seed Semail ophiolite, Wadi Tayin A at 129 km: literature-only (no cell-level TRANSFERS in verdicts.parquet)
- M1 seed Semail ophiolite, Wadi Tayin B at 106 km: literature-only (no cell-level TRANSFERS in verdicts.parquet)
- M1 seed Semail ophiolite, Ibra at 143 km (edge of radius): literature-only (no cell-level TRANSFERS in verdicts.parquet)

## Zanda (Tsamda) and Gar, Ngari, western Tibet

`site:E10K_379_778` · 31.77, 80.28 · 5 member cell(s) · span 206 km · ice ok/flag 5/0 · in known-analog buffer 0 · Attention unknown · hidden: unknown: attention not known · showcase rule c

Engine-confirmed: **L1** · not yet visually reviewed (B10): E10K_379_778,E10K_383_771,E10K_385_776,E10K_394_764,E10K_394_774

**Field — test here (transfers)**

- L1 Touchdown & Traverse · Shackleton inner wall (Site04 centre) · `slope_roughness` · 5 cell(s), best E10K_385_776: A12 robust set (intersection (i)&(ii)&(iii)); native rank i/ii/iii = 39/48/42 of 49

**Facility — cannot test here**

- L1 · all targets · `gravity` → Reduced-gravity offload rig, parabolic flight ([source](https://nssdc.gsfc.nasa.gov/planetary/factsheet/moonfact.html))
- L1 · all targets · `angle_of_repose` → Parabolic-flight drum tests or gravity-offload slope tests with the actual simulant ([source](https://doi.org/10.1029/2011JE003865))
- L1 · all targets · `atmospheric_pressure` → Thermal-vacuum chamber with regolith simulant ([source](https://nssdc.gsfc.nasa.gov/planetary/factsheet/moonfact.html))
- L1 · all targets · `radiation_dose` → Accelerator or isotope-source irradiation of components ([source](https://doi.org/10.1126/sciadv.aaz1334))
- L1 · all targets · `regolith_dust` → Use lunar simulant under vacuum; do not claim wear or adhesion results from field soil ([source](https://ntrs.nasa.gov/api/citations/20205001806/downloads/CJW%20PIO%20Dust%20Manuscript_V011.docx.pdf))

**Unobserved — this engine cannot say**

- L1 · `Metre-scale boulders and craters < 60 m`: below the 30 m DEM baseline on both sides (LOLA 5 m maps cannot resolve 1-2 m boulders either)
