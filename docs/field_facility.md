# Field / Facility split for showcase sites (PLAN 2c, A18–A20)

Generated 2026-11-14 21:53 by `scripts/sites.py` from `verdicts.parquet` (A15) and `cell_profiles.parquet` (A13). Post hoc grouping: no threshold or verdict changed. Sites are single-linkage clusters of engine-kept cells at 150 km; showcase rule: (a) Connecting Ridge cell with usable ice, (b) multi-lens partner, (c) largest site outside exclusion buffers.

## Target scarcity (A18)

| Lens | Target | TRANSFERS cells | ice ok / flag / excluded | usable | usable outside known-analog buffers | sites |
|---|---|---|---|---|---|---|
| L1 | connecting_ridge | 5 | 1 / 1 / 3 | 2 | 2 | 2 |
| L1 | shackleton_rim | 99 | 90 / 3 / 6 | 93 | 54 | 27 |
| L2 | connecting_ridge | 3 | 2 / 0 / 1 | 2 | 1 | 2 |
| L2 | shackleton_rim | 7 | 5 / 1 / 1 | 6 | 4 | 5 |

## Gêrzê, central Changtang plateau (Tibet)

`site:E10K_406_810` · 34.33, 83.83 · 4 cells · lenses L1, L2 · ice ok/flag/excluded 4/0/0 · in known-analog buffer 0 · Attention (site name) unknown · showcase rule a

**Field — test here (transfers)**

- L1 Touchdown & Traverse · shackleton_rim · `slope_roughness` · 3 cell(s), best E10K_423_793: A12 robust set (intersection (i)&(ii)&(iii)); native rank i/ii/iii = 39/48/42 of 49
- L2 Low-Sun Navigation · connecting_ridge · `shadow_casting` · 1 cell(s), best E10K_413_804: native rank (d_shadow) 35 of 49; sigma_shadow 0.54
- L2 Low-Sun Navigation · shackleton_rim · `shadow_casting` · 1 cell(s), best E10K_413_804: native rank (d_shadow) 35 of 49; sigma_shadow 0.39

**Facility — cannot test here**

- L1 · all targets · `gravity` → Reduced-gravity offload rig, parabolic flight
- L1 · all targets · `angle_of_repose` → Parabolic-flight drum tests or gravity-offload slope tests with the actual simulant
- L1 · all targets · `atmospheric_pressure` → Thermal-vacuum chamber with regolith simulant
- L1 · all targets · `radiation_dose` → Accelerator or isotope-source irradiation of components
- L1 · all targets · `regolith_dust` → Use lunar simulant under vacuum; do not claim wear or adhesion results from field soil
- L2 · all targets · `gravity` → Reduced-gravity offload rig, parabolic flight
- L2 · all targets · `atmospheric_pressure` → Thermal-vacuum chamber with regolith simulant
- L2 · all targets · `day_night_cycle` → Thermal-vacuum cycling of hardware
- L2 · all targets · `radiation_dose` → Accelerator or isotope-source irradiation of components
- L2 · all targets · `temperature` → Cryogenic test bench for ice-regolith drilling and mobility
- L2 · all targets · `diffuse_skylight` → Add artificial single-source lighting with black enclosures, or night tests
- L2 · connecting_ridge · `sun_geometry` → High-latitude summer field site or lighting rig for the solar geometry
- L2 · shackleton_rim · `sun_geometry` → High-latitude summer field site or lighting rig for the solar geometry

**Unobserved — this engine cannot say**

- L1 · `Metre-scale boulders and craters < 60 m`: below the 30 m DEM baseline on both sides (LOLA 5 m maps cannot resolve 1-2 m boulders either)
- L2 · `Horizon occlusion beyond 10 km`: shadows are computed inside the 10 km chip only, on both sides

## Da Qaidam, northern Qaidam Basin margin (Qinghai)

`site:E10K_453_921` · 38.64, 96.00 · 2 cells · lenses L1 · ice ok/flag/excluded 2/0/0 · in known-analog buffer 0 · Attention (site name) unknown · showcase rule a

**Field — test here (transfers)**

- L1 Touchdown & Traverse · connecting_ridge · `slope_roughness` · 1 cell(s), best E10K_453_921: A12 robust set (intersection (i)&(ii)&(iii)); native rank i/ii/iii = 43/36/41 of 49
- L1 Touchdown & Traverse · shackleton_rim · `slope_roughness` · 1 cell(s), best E10K_465_927: A12 robust set (intersection (i)&(ii)&(iii)); native rank i/ii/iii = 29/38/32 of 49

**Facility — cannot test here**

- L1 · all targets · `gravity` → Reduced-gravity offload rig, parabolic flight
- L1 · all targets · `angle_of_repose` → Parabolic-flight drum tests or gravity-offload slope tests with the actual simulant
- L1 · all targets · `atmospheric_pressure` → Thermal-vacuum chamber with regolith simulant
- L1 · all targets · `radiation_dose` → Accelerator or isotope-source irradiation of components
- L1 · all targets · `regolith_dust` → Use lunar simulant under vacuum; do not claim wear or adhesion results from field soil

**Unobserved — this engine cannot say**

- L1 · `Metre-scale boulders and craters < 60 m`: below the 30 m DEM baseline on both sides (LOLA 5 m maps cannot resolve 1-2 m boulders either)

## Mauna Loa – Mauna Kea, Hawaiʻi

`site:E10K_244_-1498` · 19.45, -155.50 · 1 cells · lenses L2 · ice ok/flag/excluded 1/0/0 · in known-analog buffer 1 · Attention (site name) unknown · showcase rule a

**Field — test here (transfers)**

- L2 Low-Sun Navigation · connecting_ridge · `shadow_casting` · 1 cell(s), best E10K_244_-1498: native rank (d_shadow) 45 of 49; sigma_shadow 0.13

**Facility — cannot test here**

- L2 · all targets · `gravity` → Reduced-gravity offload rig, parabolic flight
- L2 · all targets · `atmospheric_pressure` → Thermal-vacuum chamber with regolith simulant
- L2 · all targets · `day_night_cycle` → Thermal-vacuum cycling of hardware
- L2 · all targets · `radiation_dose` → Accelerator or isotope-source irradiation of components
- L2 · all targets · `temperature` → Cryogenic test bench for ice-regolith drilling and mobility
- L2 · all targets · `diffuse_skylight` → Add artificial single-source lighting with black enclosures, or night tests
- L2 · connecting_ridge · `sun_geometry` → High-latitude summer field site or lighting rig for the solar geometry

**Unobserved — this engine cannot say**

- L2 · `Horizon occlusion beyond 10 km`: shadows are computed inside the 10 km chip only, on both sides

## Peary Land, North Greenland

`site:E10K_729_-319` · 82.62, -33.07 · 1 cells · lenses L1, X1 · ice ok/flag/excluded 0/1/0 · in known-analog buffer 0 · Attention (site name) unknown · showcase rule a,b

**Field — test here (transfers)**

- L1 Touchdown & Traverse · connecting_ridge · `slope_roughness` · 1 cell(s), best E10K_729_-319: A12 robust set (intersection (i)&(ii)&(iii)); native rank i/ii/iii = 43/26/44 of 49
- X1 Ice under Dry Overburden · arcadia_planitia · `ice_configuration` · 2 cell(s), best seed_peary_land: all 3 conditions met (permafrost, no thaw to ice, dry overburden) (thresholds set after seeing data)
- X1 Ice under Dry Overburden · all targets · `day_night_cycle`: Day length is nearly Earth-like and transfers well; the colder, thin-air thermal cycling does not.

**Facility — cannot test here**

- L1 · all targets · `gravity` → Reduced-gravity offload rig, parabolic flight
- L1 · all targets · `angle_of_repose` → Parabolic-flight drum tests or gravity-offload slope tests with the actual simulant
- L1 · all targets · `atmospheric_pressure` → Thermal-vacuum chamber with regolith simulant
- L1 · all targets · `radiation_dose` → Accelerator or isotope-source irradiation of components
- L1 · all targets · `regolith_dust` → Use lunar simulant under vacuum; do not claim wear or adhesion results from field soil
- X1 · all targets · `gravity` → Reduced-gravity offload rig, parabolic flight
- X1 · all targets · `angle_of_repose` → Parabolic-flight drum tests with the actual simulant
- X1 · all targets · `atmospheric_pressure` → Mars-pressure CO2 chamber
- X1 · all targets · `radiation_dose` → Accelerator or isotope-source irradiation of components
- X1 · all targets · `temperature` → Cold-chamber tests; polar or high-altitude desert sites only as partial proxies
- X1 · all targets · `perchlorate` → Dope simulant with perchlorate salts

**Unobserved — this engine cannot say**

- L1 · `Metre-scale boulders and craters < 60 m`: below the 30 m DEM baseline on both sides (LOLA 5 m maps cannot resolve 1-2 m boulders either)
- X1 · `Overburden dielectric properties (radar / GPR response)`: no global Earth dataset matched to SWIM radar observables

## Atacama – Puna altiplano (Chile, Argentina, Bolivia)

`site:E10K_-228_-669` · -24.67, -67.94 · 54 cells · lenses L1, L2 · ice ok/flag/excluded 53/1/0 · in known-analog buffer 40 · Attention (site name) unknown · showcase rule b

**Field — test here (transfers)**

- L1 Touchdown & Traverse · shackleton_rim · `slope_roughness` · 53 cell(s), best E10K_-336_-664: A12 robust set (intersection (i)&(ii)&(iii)); native rank i/ii/iii = 45/49/47 of 49
- L2 Low-Sun Navigation · shackleton_rim · `shadow_casting` · 2 cell(s), best E10K_-336_-664: native rank (d_shadow) 49 of 49; sigma_shadow 0.01

**Facility — cannot test here**

- L1 · all targets · `gravity` → Reduced-gravity offload rig, parabolic flight
- L1 · all targets · `angle_of_repose` → Parabolic-flight drum tests or gravity-offload slope tests with the actual simulant
- L1 · all targets · `atmospheric_pressure` → Thermal-vacuum chamber with regolith simulant
- L1 · all targets · `radiation_dose` → Accelerator or isotope-source irradiation of components
- L1 · all targets · `regolith_dust` → Use lunar simulant under vacuum; do not claim wear or adhesion results from field soil
- L2 · all targets · `gravity` → Reduced-gravity offload rig, parabolic flight
- L2 · all targets · `atmospheric_pressure` → Thermal-vacuum chamber with regolith simulant
- L2 · all targets · `day_night_cycle` → Thermal-vacuum cycling of hardware
- L2 · all targets · `radiation_dose` → Accelerator or isotope-source irradiation of components
- L2 · all targets · `temperature` → Cryogenic test bench for ice-regolith drilling and mobility
- L2 · all targets · `diffuse_skylight` → Add artificial single-source lighting with black enclosures, or night tests
- L2 · shackleton_rim · `sun_geometry` → High-latitude summer field site or lighting rig for the solar geometry

**Unobserved — this engine cannot say**

- L1 · `Metre-scale boulders and craters < 60 m`: below the 30 m DEM baseline on both sides (LOLA 5 m maps cannot resolve 1-2 m boulders either)
- L2 · `Horizon occlusion beyond 10 km`: shadows are computed inside the 10 km chip only, on both sides

**Literature-only neighbours (not engine-confirmed)**

- M1 seed Salar de Uyuni margin at 149 km: literature-only (no cell-level TRANSFERS in verdicts.parquet)

## Jebel Akhdar, Hajar Mountains (Oman)

`site:E10K_289_551` · 23.14, 57.27 · 1 cells · lenses L2 · ice ok/flag/excluded 1/0/0 · in known-analog buffer 0 · Attention (site name) unknown · showcase rule b

**Field — test here (transfers)**

- L2 Low-Sun Navigation · shackleton_rim · `shadow_casting` · 1 cell(s), best E10K_289_551: native rank (d_shadow) 29 of 49; sigma_shadow 0.65

**Facility — cannot test here**

- L2 · all targets · `gravity` → Reduced-gravity offload rig, parabolic flight
- L2 · all targets · `atmospheric_pressure` → Thermal-vacuum chamber with regolith simulant
- L2 · all targets · `day_night_cycle` → Thermal-vacuum cycling of hardware
- L2 · all targets · `radiation_dose` → Accelerator or isotope-source irradiation of components
- L2 · all targets · `temperature` → Cryogenic test bench for ice-regolith drilling and mobility
- L2 · all targets · `diffuse_skylight` → Add artificial single-source lighting with black enclosures, or night tests
- L2 · shackleton_rim · `sun_geometry` → High-latitude summer field site or lighting rig for the solar geometry

**Unobserved — this engine cannot say**

- L2 · `Horizon occlusion beyond 10 km`: shadows are computed inside the 10 km chip only, on both sides

**Literature-only neighbours (not engine-confirmed)**

- M1 seed Semail ophiolite, Wadi Tayin A at 129 km: literature-only (no cell-level TRANSFERS in verdicts.parquet)
- M1 seed Semail ophiolite, Wadi Tayin B at 106 km: literature-only (no cell-level TRANSFERS in verdicts.parquet)
- M1 seed Semail ophiolite, Ibra at 143 km: literature-only (no cell-level TRANSFERS in verdicts.parquet)

## Zanda (Tsamda) and Gar, Ngari, western Tibet

`site:E10K_379_778` · 31.77, 80.28 · 5 cells · lenses L1 · ice ok/flag/excluded 5/0/0 · in known-analog buffer 0 · Attention (site name) unknown · showcase rule c

**Field — test here (transfers)**

- L1 Touchdown & Traverse · shackleton_rim · `slope_roughness` · 5 cell(s), best E10K_385_776: A12 robust set (intersection (i)&(ii)&(iii)); native rank i/ii/iii = 39/48/42 of 49

**Facility — cannot test here**

- L1 · all targets · `gravity` → Reduced-gravity offload rig, parabolic flight
- L1 · all targets · `angle_of_repose` → Parabolic-flight drum tests or gravity-offload slope tests with the actual simulant
- L1 · all targets · `atmospheric_pressure` → Thermal-vacuum chamber with regolith simulant
- L1 · all targets · `radiation_dose` → Accelerator or isotope-source irradiation of components
- L1 · all targets · `regolith_dust` → Use lunar simulant under vacuum; do not claim wear or adhesion results from field soil

**Unobserved — this engine cannot say**

- L1 · `Metre-scale boulders and craters < 60 m`: below the 30 m DEM baseline on both sides (LOLA 5 m maps cannot resolve 1-2 m boulders either)
