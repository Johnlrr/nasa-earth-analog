"""
Spike R5 — Earth terrain separation test for A4.

Compare 5 Earth DEM chips against the Moon Connecting Ridge target descriptor.

EXPECTED OUTCOMES (written before seeing results, per PLAN.md rules):
  Haughton impact structure, Devon Island (75.38, -89.68)   → expected HIGH similarity
  SP Crater / Black Point lava flow, Arizona (35.58, -111.63) → expected UNCERTAIN

σ formula used here is a TEMPORARY diagonal approximation:
    z_k = (e_k - t_k) / max(std_pop_k, min_scale_k)
    d = sqrt(Σ z_k²)
This will be replaced by similitude.fidelity (Mahalanobis + chi² → σ) in A5.

Usage:
    python scripts/spike_r5.py                   # full run (needs targets_L1.parquet)
    python scripts/spike_r5.py --fetch-only      # fetch and cache 5 chips, then stop
"""

from __future__ import annotations

import argparse
import logging
import math
import random
import sys
from pathlib import Path

import numpy as np
import pandas as pd

# Allow running from repo root
sys.path.insert(0, str(Path(__file__).parents[1] / "src"))
sys.path.insert(0, str(Path(__file__).parents[1] / "scripts" / "gee"))

from chip_dem import get_chip

from similitude.descriptors.terrain import terrain_descriptors

log = logging.getLogger(__name__)

logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

CHIP_M = 10_000.0
RES_M = 30.0
FOOTPRINT_M = 4_000.0
RADIUS_M = 6_371_000.0  # Earth radius for shadow curvature correction

# Controls: (label, lat, lon, expected)
POSITIVE_CONTROLS = [
    ("Haughton_Devon", 75.38, -89.68, "high"),
    ("SP_Crater_Arizona", 35.58, -111.63, "uncertain"),
]

# Fallback random deserts if tier1_terrain.csv is absent (seed=42)
DESERT_BBOXES = [
    ("Sahara", -5.0, 18.0, 25.0, 28.0),  # (name, lon_min, lat_min, lon_max, lat_max)
    ("AustraliaInterior", 125.0, -28.0, 140.0, -20.0),
    ("Gobi", 95.0, 41.0, 110.0, 45.0),
]

TARGETS_PATH = Path("data/derived/targets_L1.parquet")
TIER1_CSV = Path("data/derived/tier1_terrain.csv")
SPIKE_OUT = Path("data/derived/spike_r5.csv")

# min_scale per descriptor (physical tolerance)
MIN_SCALE = {
    "slope_p50": 1.0,  # 1 degree
    "slope_p90": 1.0,
    "frac_gt8": 0.05,
    "frac_gt15": 0.05,
    "frac_gt20": 0.05,
    "rms_s1": None,  # filled dynamically as 10% of target
    "rms_s2": None,
    "rms_s4": None,
    "rms_s8": None,
    "rms_s16": None,
    "hurst": 0.05,
    "shadow_e2": 0.05,
    "shadow_e5": 0.05,
    "shadow_e7": 0.05,
}
RMS_FRAC = 0.10  # 10% of target value for rms_s* min_scale


def _random_points_in_desert(seed: int = 42) -> list[tuple[str, float, float]]:
    """Return 3 random (label, lat, lon) points, one per desert bbox."""
    rng = random.Random(seed)
    points = []
    for name, lon_min, lat_min, lon_max, lat_max in DESERT_BBOXES:
        lat = rng.uniform(lat_min, lat_max)
        lon = rng.uniform(lon_min, lon_max)
        points.append((f"Random_{name}", lat, lon))
    return points


def _random_points_from_tier1(seed: int = 42, n: int = 3) -> list[tuple[str, float, float]]:
    """Pick n random rows from tier1_terrain.csv."""
    df = pd.read_csv(TIER1_CSV)
    sample = df.sample(n=n, random_state=seed)
    points = []
    for i, row in sample.iterrows():
        label = f"Tier1_{i}"
        points.append((label, float(row["lat"]), float(row["lon"])))
    return points


def _build_site_list() -> list[tuple[str, float, float, str]]:
    """Return list of (label, lat, lon, expected) for the 5 Earth sites."""
    sites = [(lbl, lat, lon, exp) for lbl, lat, lon, exp in POSITIVE_CONTROLS]

    if TIER1_CSV.exists():
        log.info("Using tier1_terrain.csv for 3 random sites")
        randoms = _random_points_from_tier1()
    else:
        log.info("tier1_terrain.csv absent — using desert fallback (seed=42)")
        randoms = _random_points_in_desert()

    for lbl, lat, lon in randoms:
        sites.append((lbl, lat, lon, "random"))

    return sites


def _compute_descriptors(lat: float, lon: float, cache_dir: str) -> tuple[dict, dict]:
    """Fetch chip and compute terrain_descriptors. Returns (descriptors, meta)."""
    dem, meta = get_chip(lat, lon, chip_m=CHIP_M, res_m=RES_M, cache_dir=cache_dir)
    desc = terrain_descriptors(
        dem,
        RES_M,
        RES_M,
        radius_m=RADIUS_M,
        footprint_m=FOOTPRINT_M,
    )
    return desc, meta


def _load_target(target_id: str = "connecting_ridge") -> dict:
    """Load target descriptor row from targets_L1.parquet."""
    df = pd.read_parquet(TARGETS_PATH)
    # Filter to target row (is_reference=True and matching target_id)
    mask = df["target_id"].str.lower().str.contains(target_id.replace("_", "").replace(" ", ""))
    if not mask.any():
        # Fallback: first is_reference=True row
        log.warning("target_id '%s' not found; using first is_reference=True row", target_id)
        mask = df["is_reference"].astype(bool)
    row = df[mask].iloc[0]
    return row.to_dict()


def _descriptor_keys(desc: dict) -> list[str]:
    """Return descriptor keys common between earth and target, excluding metadata keys."""
    skip = {"L_m", "footprint_m"}
    return [k for k in desc if k not in skip]


def _sigma_diagonal(
    earth_desc: dict,
    target_desc: dict,
    pop_rows: list[dict],
    keys: list[str],
) -> tuple[float, str, dict[str, float]]:
    """Compute TEMPORARY diagonal sigma.

    z_k = (e_k - t_k) / max(std_pop_k, min_scale_k)
    d = sqrt(Σ z_k²)

    Returns (d, worst_key, z_dict).
    NOTE: This is a temporary approximation; will be replaced by
    similitude.fidelity (A5) using the full Mahalanobis formula.
    """
    pop_vals: dict[str, list[float]] = {k: [] for k in keys}
    for row in pop_rows:
        for k in keys:
            v = row.get(k)
            if v is not None and not (isinstance(v, float) and math.isnan(v)):
                pop_vals[k].append(float(v))

    z_dict = {}
    for k in keys:
        e_k = earth_desc.get(k)
        t_k = target_desc.get(k)
        if e_k is None or t_k is None:
            continue
        if isinstance(e_k, float) and math.isnan(e_k):
            continue
        if isinstance(t_k, float) and math.isnan(t_k):
            continue

        std_pop = float(np.std(pop_vals[k])) if len(pop_vals[k]) >= 2 else 0.0

        # min_scale
        ms = MIN_SCALE.get(k)
        if ms is None:
            # rms_s* : 10% of target value
            ms = abs(float(t_k)) * RMS_FRAC if float(t_k) != 0 else 1.0

        scale = max(std_pop, ms)
        if scale == 0:
            scale = 1.0

        z_dict[k] = (float(e_k) - float(t_k)) / scale

    if not z_dict:
        return np.nan, "", {}

    d = float(np.sqrt(sum(z**2 for z in z_dict.values())))
    worst_key = max(z_dict, key=lambda k: abs(z_dict[k]))
    return d, worst_key, z_dict


def main(fetch_only: bool = False) -> None:
    print("=" * 70)
    print("SPIKE R5 — Earth terrain separation test")
    print("=" * 70)
    print()
    print("EXPECTED OUTCOMES (declared before running):")
    for lbl, lat, lon, exp in POSITIVE_CONTROLS:
        print(f"  {lbl} ({lat}, {lon}): {exp}")
    print()

    sites = _build_site_list()
    cache_dir = "data/raw/earth/chips"

    # --- fetch and cache all 5 chips ---
    print("Fetching / loading DEM chips...")
    chip_results: list[tuple[str, float, float, str, dict, dict | None]] = []
    for lbl, lat, lon, exp in sites:
        log.info("Site: %s (%.4f, %.4f)", lbl, lat, lon)
        try:
            desc, meta = _compute_descriptors(lat, lon, cache_dir)
            chip_results.append((lbl, lat, lon, exp, desc, meta))
            print(
                f"  {lbl}: shape=({int(CHIP_M / RES_M)},{int(CHIP_M / RES_M)}), "
                f"nodata_frac={meta['nodata_frac']:.3f}, tiles={meta.get('tiles', [])}"
            )
        except Exception as exc:
            log.error("Failed to get chip for %s: %s", lbl, exc)
            chip_results.append((lbl, lat, lon, exp, {}, None))

    if fetch_only:
        print()
        print("--fetch-only mode: chips cached. Stopping here (targets_L1.parquet not needed yet).")
        return

    # --- load target ---
    if not TARGETS_PATH.exists():
        print()
        print(f"ERROR: {TARGETS_PATH} not found.")
        print("Run scripts/targets/moon_terrain.py (A3) first, or use --fetch-only.")
        sys.exit(1)

    print()
    print(f"Loading target from {TARGETS_PATH} ...")
    target_dict = _load_target("connecting_ridge")
    target_id = target_dict.get("target_id", "connecting_ridge")
    print(f"  Target: {target_id}")

    # Determine descriptor keys from first successful earth chip
    first_desc = next((d for _, _, _, _, d, m in chip_results if d and m is not None), {})
    keys = _descriptor_keys(first_desc) if first_desc else []

    # --- population for sigma (non-reference rows in targets_L1) ---
    df_targets = pd.read_parquet(TARGETS_PATH)
    pop_df = df_targets[~df_targets["is_reference"].astype(bool)]
    pop_rows: list[dict] = []
    for _, row in pop_df.iterrows():
        pop_rows.append(row.to_dict())

    if len(pop_rows) < 2:
        log.warning("Population has < 2 rows; std will be 0 for all descriptors.")

    # --- compute sigma for each site ---
    print()
    print("Computing diagonal σ (temporary; will be replaced by similitude.fidelity in A5):")
    print()

    rows_out = []
    for lbl, lat, lon, exp, desc, meta in chip_results:
        if not desc or meta is None:
            d, worst, z_dict = np.nan, "N/A", {}
        else:
            d, worst, z_dict = _sigma_diagonal(desc, target_dict, pop_rows, keys)

        row = {
            "label": lbl,
            "lat": lat,
            "lon": lon,
            "expected": exp,
            "d_diagonal": d,
            "worst_descriptor": worst,
            "nodata_frac": meta["nodata_frac"] if meta else np.nan,
        }
        for k in keys:
            row[k] = desc.get(k, np.nan) if desc else np.nan
        rows_out.append(row)

    df_out = pd.DataFrame(rows_out)

    # --- add target row ---
    target_row = {
        "label": f"TARGET_{target_id}",
        "lat": target_dict.get("lat"),
        "lon": target_dict.get("lon"),
        "expected": "target",
        "d_diagonal": 0.0,
        "worst_descriptor": "—",
        "nodata_frac": 0.0,
    }
    for k in keys:
        target_row[k] = target_dict.get(k, np.nan)
    df_out = pd.concat([pd.DataFrame([target_row]), df_out], ignore_index=True)

    # --- print results ---
    print("Descriptor table (target + 5 Earth sites):")
    pd.set_option("display.max_columns", None)
    pd.set_option("display.width", 120)
    pd.set_option("display.float_format", "{:.4f}".format)
    print(
        df_out[["label", "d_diagonal", "worst_descriptor", "expected"] + keys].to_string(
            index=False
        )
    )

    print()
    print("Distance summary (d_diagonal):")
    for _, row in df_out.iterrows():
        if row["label"].startswith("TARGET_"):
            continue
        print(f"  {row['label']:<30} d={row['d_diagonal']:.3f}  expected={row['expected']}")

    # --- R5 criterion check ---
    print()
    print("R5 CRITERION CHECK:")
    print("  Both positive controls must have d < all 3 random points.")
    pos_ds = df_out[df_out["expected"].isin(["high", "uncertain"])]["d_diagonal"].tolist()
    rnd_ds = df_out[df_out["expected"] == "random"]["d_diagonal"].tolist()

    if not rnd_ds or any(pd.isna(d) for d in pos_ds + rnd_ds):
        print("  CANNOT EVALUATE — missing data")
        r5_pass = None
    else:
        r5_pass = all(pd.notna(pd.Series(pos_ds))) and max(pos_ds) < min(rnd_ds)
        status = "PASS ✓" if r5_pass else "FAIL ✗"
        print(
            f"  max(controls d) = {max(pos_ds):.3f}, min(random d) = {min(rnd_ds):.3f} → {status}"
        )

    # --- save ---
    SPIKE_OUT.parent.mkdir(parents=True, exist_ok=True)
    df_out.to_csv(SPIKE_OUT, index=False)
    print()
    print(f"Saved → {SPIKE_OUT}")

    # --- worst descriptor for each positive control ---
    print()
    print("Worst descriptor per site:")
    for _, row in df_out.iterrows():
        if row["label"].startswith("TARGET_"):
            continue
        print(f"  {row['label']:<30} worst={row['worst_descriptor']}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Spike R5: Earth terrain separation test.")
    parser.add_argument(
        "--fetch-only",
        action="store_true",
        help="Only fetch and cache DEM chips; skip sigma (targets_L1.parquet not ready).",
    )
    args = parser.parse_args()
    main(fetch_only=args.fetch_only)
