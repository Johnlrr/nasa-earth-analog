"""
A3 — Moon terrain targets from PGDA Product 78 (Barker et al. 2021).

Outputs:
  data/derived/targets_L1.parquet       — full terrain descriptors at L=30 m
  data/derived/targets_L1_coarse.parquet — coarse (90 m) descriptors for tier-1 ranking
"""

import time
import warnings
from pathlib import Path

import numpy as np
import pandas as pd
import rasterio
from pyproj import CRS, Transformer

from similitude.descriptors.terrain import (
    aggregate_to_baseline,
    slope_stats,
    terrain_descriptors,
)

warnings.filterwarnings("ignore", category=rasterio.errors.NotGeoreferencedWarning)

ROOT = Path(__file__).resolve().parents[2]
DATA_RAW = ROOT / "data" / "raw" / "moon" / "pgda78"
DATA_OUT = ROOT / "data" / "derived"
DATA_OUT.mkdir(parents=True, exist_ok=True)

SITES = {
    "Site01": "connecting_ridge",
    "Site04": "shackleton_rim",
    "Site06": "nobile_rim_1",
    "Site07": "peak_near_shackleton",
    "Site11": "de_gerlache_rim",
    "Site23": "malapert_massif",
}

REFERENCE_SITES = {"Site01", "Site04"}

L_M = 30.0  # baseline
FOOTPRINT_M = 4000.0
CHIP_M = 10000.0  # footprint + 3 km each side
BUFFER_M = 3000.0
RADIUS_M = 1_737_400.0
NODATA_FRAC_MAX = 0.05

# Grid spacing for population footprints
GRID_STEP_M = 4000.0  # first try non-overlapping
GRID_STEP_FALLBACK = 3000.0

SOURCE_PREFIX = "PGDA78"


# ---------------------------------------------------------------------------
# helpers
# ---------------------------------------------------------------------------


def _crs_geodetic(crs_wkt: str) -> CRS:
    return CRS.from_wkt(crs_wkt).geodetic_crs


def _xy_to_latlon(x: float, y: float, proj_crs: CRS, geo_crs: CRS) -> tuple[float, float]:
    t = Transformer.from_crs(proj_crs, geo_crs, always_xy=True)
    lon, lat = t.transform(x, y)
    return float(lat), float(lon)


def _chip_at(dem: np.ndarray, transform, chip_m: float, cx: float, cy: float) -> np.ndarray | None:
    """Extract a chip_m × chip_m square centred at projected (cx, cy).
    Returns None if chip falls outside raster bounds."""
    res = abs(transform.a)  # pixel size in metres
    half_px = int(round(chip_m / 2 / res))
    chip_px = 2 * half_px

    # Convert projected centre to pixel (row, col)
    col_f = (cx - transform.c) / transform.a
    row_f = (cy - transform.f) / transform.e

    col0 = int(round(col_f)) - half_px
    row0 = int(round(row_f)) - half_px

    nrows, ncols = dem.shape
    if row0 < 0 or col0 < 0 or row0 + chip_px > nrows or col0 + chip_px > ncols:
        return None

    return dem[row0 : row0 + chip_px, col0 : col0 + chip_px]


def _nodata_frac(chip: np.ndarray) -> float:
    return float(np.isnan(chip).mean())


def _coarse_window(dem5: np.ndarray, transform, cx: float, cy: float) -> np.ndarray | None:
    """Return 10 km chip at 5 m res for coarse (90 m) descriptors."""
    return _chip_at(dem5, transform, CHIP_M, cx, cy)


# ---------------------------------------------------------------------------
# R4 verification: compare slope_stats on 5 m DEM vs product _slp.tif
# ---------------------------------------------------------------------------


def r4_check(site_id: str, dem5: np.ndarray, slp5: np.ndarray, transform) -> dict:
    res = abs(transform.a)
    nrows, ncols = dem5.shape
    # 4 km window at centre
    half_px = int(round(FOOTPRINT_M / 2 / res))
    cr, cc = nrows // 2, ncols // 2
    dem_win = dem5[cr - half_px : cr + half_px, cc - half_px : cc + half_px]
    slp_win = slp5[cr - half_px : cr + half_px, cc - half_px : cc + half_px]

    stats_dem = slope_stats(dem_win, res)
    p50_dem = stats_dem["slope_p50"]

    # median of product slope raster (pixels are slope in degrees)
    valid_slp = slp_win[~np.isnan(slp_win)]
    p50_slp = float(np.median(valid_slp)) if valid_slp.size > 0 else np.nan

    diff = abs(p50_dem - p50_slp)
    return {"site": site_id, "p50_dem_5m": p50_dem, "p50_slp_5m": p50_slp, "diff_deg": diff}


# ---------------------------------------------------------------------------
# grid footprints for population
# ---------------------------------------------------------------------------


def _grid_footprints(dem5: np.ndarray, transform, step_m: float) -> list[tuple[float, float]]:
    """Return (cx, cy) in projected coords for all valid footprints on a grid."""
    res = abs(transform.a)
    nrows, ncols = dem5.shape

    chip_px = int(round(CHIP_M / res))
    half_chip_px = chip_px // 2
    step_px = int(round(step_m / res))

    centres = []
    # Start row/col: half_chip_px from edge so full chip fits
    r = half_chip_px
    while r + half_chip_px <= nrows:
        c = half_chip_px
        while c + half_chip_px <= ncols:
            # Projected centre
            cx = transform.c + (c + 0.5) * transform.a
            cy = transform.f + (r + 0.5) * transform.e

            chip = dem5[r - half_chip_px : r + half_chip_px, c - half_chip_px : c + half_chip_px]
            if _nodata_frac(chip) < NODATA_FRAC_MAX:
                centres.append((cx, cy))
            c += step_px
        r += step_px
    return centres


# ---------------------------------------------------------------------------
# coarse descriptors at 90 m over 10 km window
# ---------------------------------------------------------------------------


def _coarse_descriptors(chip5: np.ndarray) -> dict:
    dem90 = aggregate_to_baseline(chip5, 5.0, 90.0)
    ss = slope_stats(dem90, 90.0)
    valid = dem90[~np.isnan(dem90)]
    relief = float(valid.max() - valid.min()) if valid.size > 0 else np.nan
    return {
        "slope_p50_90m": ss["slope_p50"],
        "frac_gt8_90m": ss["frac_gt8"],
        "frac_gt20_90m": ss["frac_gt20"],
        "relief_90m": relief,
    }


# ---------------------------------------------------------------------------
# main
# ---------------------------------------------------------------------------


def main():
    t0 = time.time()

    rows_L1 = []
    rows_coarse = []
    r4_rows = []

    total_pop = 0

    for site_code, site_name in SITES.items():
        dem_path = DATA_RAW / f"{site_code}_final_adj_5mpp_surf.tif"
        slp_path = DATA_RAW / f"{site_code}_final_adj_5mpp_slp.tif"

        with rasterio.open(dem_path) as ds:
            dem5 = ds.read(1).astype(np.float64)
            nodata = ds.nodata
            transform = ds.transform
            crs_wkt = ds.crs.to_wkt()
            print(f"\n{site_code}: shape={dem5.shape}, nodata={nodata}")
        with rasterio.open(slp_path) as ds:
            slp5 = ds.read(1).astype(np.float64)
            slp_nodata = ds.nodata
        if nodata is not None and not np.isnan(nodata):
            dem5[dem5 == nodata] = np.nan
        if slp_nodata is not None and not np.isnan(slp_nodata):
            slp5[slp5 == slp_nodata] = np.nan

        proj_crs = CRS.from_wkt(crs_wkt)
        geo_crs = _crs_geodetic(crs_wkt)

        # --- R4 check ---
        r4 = r4_check(site_code, dem5, slp5, transform)
        r4_rows.append(r4)

        # centre of raster
        cx_centre = transform.c + (dem5.shape[1] / 2) * transform.a
        cy_centre = transform.f + (dem5.shape[0] / 2) * transform.e

        # --- reference targets ---
        if site_code in REFERENCE_SITES:
            chip = _chip_at(dem5, transform, CHIP_M, cx_centre, cy_centre)
            if chip is None:
                print(f"  WARNING: reference chip out of bounds for {site_code}")
            else:
                nd_frac = _nodata_frac(chip)
                lat, lon = _xy_to_latlon(cx_centre, cy_centre, proj_crs, geo_crs)
                desc = terrain_descriptors(
                    chip, 5.0, L_M, radius_m=RADIUS_M, footprint_m=FOOTPRINT_M
                )
                fp_id = f"{site_name}_ref"
                row = {
                    "target_id": site_name,
                    "body": "moon",
                    "lens_id": "L1",
                    "footprint_id": fp_id,
                    "is_reference": True,
                    "lat": lat,
                    "lon": lon,
                    "L_m": L_M,
                    "footprint_m": FOOTPRINT_M,
                    "source": f"{SOURCE_PREFIX} {site_code}",
                    "nodata_frac": nd_frac,
                }
                row.update(desc)
                rows_L1.append(row)

                # coarse
                coarse = _coarse_descriptors(chip)
                rows_coarse.append(
                    {
                        "target_id": site_name,
                        "footprint_id": fp_id,
                        "is_reference": True,
                        "lat": lat,
                        "lon": lon,
                        "source": f"{SOURCE_PREFIX} {site_code}",
                        **coarse,
                    }
                )

        # --- population grid ---
        centres = _grid_footprints(dem5, transform, GRID_STEP_M)
        note = ""
        if len(centres) < 5:  # too few, try fallback
            centres = _grid_footprints(dem5, transform, GRID_STEP_FALLBACK)
            note = " (3km step)"

        print(f"  {site_code}: {len(centres)} population footprints{note}")
        total_pop += len(centres)

        for i, (cx, cy) in enumerate(centres):
            chip = _chip_at(dem5, transform, CHIP_M, cx, cy)
            if chip is None:
                continue
            lat, lon = _xy_to_latlon(cx, cy, proj_crs, geo_crs)
            nd_frac = _nodata_frac(chip)
            desc = terrain_descriptors(chip, 5.0, L_M, radius_m=RADIUS_M, footprint_m=FOOTPRINT_M)
            source_str = f"{SOURCE_PREFIX} {site_code}{note}"
            fp_id = f"{site_name}_pop_{i:03d}"
            row = {
                "target_id": site_name,
                "body": "moon",
                "lens_id": "L1",
                "footprint_id": fp_id,
                "is_reference": False,
                "lat": lat,
                "lon": lon,
                "L_m": L_M,
                "footprint_m": FOOTPRINT_M,
                "source": source_str,
                "nodata_frac": nd_frac,
            }
            row.update(desc)
            rows_L1.append(row)

            coarse = _coarse_descriptors(chip)
            rows_coarse.append(
                {
                    "target_id": site_name,
                    "footprint_id": fp_id,
                    "is_reference": False,
                    "lat": lat,
                    "lon": lon,
                    "source": source_str,
                    **coarse,
                }
            )

    # --- R4 table ---
    print("\n=== R4 Verification (5 m slope_stats vs product _slp.tif, 4 km window at centre) ===")
    r4_df = pd.DataFrame(r4_rows)
    print(r4_df.to_string(index=False))
    max_diff = r4_df["diff_deg"].max()
    if max_diff > 2.0:
        print(f"\nWARNING: R4 max diff = {max_diff:.2f}° > 2°. See PLAN.md open questions.")
    else:
        print(f"\nR4 PASS: max diff = {max_diff:.2f}° ≤ 2°")

    # --- totals ---
    df_L1 = pd.DataFrame(rows_L1)
    df_coarse = pd.DataFrame(rows_coarse)

    pop_count = int((df_L1["is_reference"] == False).sum())  # noqa: E712
    print(f"\nTotal population footprints: {pop_count}")
    if pop_count < 30:
        print("WARNING: total population < 30. Check grid step logic.")

    # --- summary table ---
    print("\n=== Descriptor summary: reference vs population median ===")
    desc_cols = [
        c
        for c in df_L1.columns
        if c
        not in {
            "target_id",
            "body",
            "lens_id",
            "footprint_id",
            "is_reference",
            "lat",
            "lon",
            "L_m",
            "footprint_m",
            "source",
            "nodata_frac",
        }
    ]
    ref_rows = df_L1[df_L1["is_reference"] == True]  # noqa: E712
    pop_rows = df_L1[df_L1["is_reference"] == False]  # noqa: E712
    summary = pd.DataFrame(
        {
            "descriptor": desc_cols,
            "ref_connecting_ridge": [
                ref_rows[ref_rows["target_id"] == "connecting_ridge"][c].values[0]
                if "connecting_ridge" in ref_rows["target_id"].values and c in ref_rows.columns
                else np.nan
                for c in desc_cols
            ],
            "ref_shackleton_rim": [
                ref_rows[ref_rows["target_id"] == "shackleton_rim"][c].values[0]
                if "shackleton_rim" in ref_rows["target_id"].values and c in ref_rows.columns
                else np.nan
                for c in desc_cols
            ],
            "pop_median": [
                pop_rows[c].median() if c in pop_rows.columns else np.nan for c in desc_cols
            ],
        }
    )
    print(summary.to_string(index=False))

    # --- export ---
    out_L1 = DATA_OUT / "targets_L1.parquet"
    out_coarse = DATA_OUT / "targets_L1_coarse.parquet"
    df_L1.to_parquet(out_L1, index=False)
    df_coarse.to_parquet(out_coarse, index=False)
    print(f"\nWrote {out_L1}  ({len(df_L1)} rows)")
    print(f"Wrote {out_coarse}  ({len(df_coarse)} rows)")

    elapsed = time.time() - t0
    print(f"\nTotal runtime: {elapsed:.1f} s ({elapsed / 60:.1f} min)")
    if elapsed > 600:
        print("WARNING: runtime > 10 min")

    return r4_df, df_L1


if __name__ == "__main__":
    main()
