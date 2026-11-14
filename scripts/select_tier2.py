"""
Select tier-2 chip sites for Earth L1.

Outputs: data/derived/tier2_L1_selection.csv

Groups
------
rank   : top 300 coarse-sigma candidates (Connecting Ridge target, diagonal sigma).
         Non-max suppression: keep only the lower-d cell within any 30 km pair.
null   : 200 random bare-ground cells stratified by 20°-latitude band (seed=20261114).
         Excludes cells already chosen for 'rank'.
control: sites from config/controls.yaml (lens_id L1 or L2); fallback list if absent.
decoy  : same source.
seed   : fixed reference locations.

The 4 coarse descriptors used for ranking are the same 4 that tier1_terrain.py exports:
  slope_p50_90m, frac_gt8_90m, frac_gt20_90m, relief_90m
(coarse, 90-m window; for display only — fine descriptors come in build_earth_L1.py).

min_scale per PLAN: slope 1°, frac 0.05, relief = 10% of target value.
"""

from __future__ import annotations

import math
from pathlib import Path

import numpy as np
import pandas as pd
import yaml

ROOT = Path(__file__).resolve().parents[1]

# ---------------------------------------------------------------------------
# Coarse ranking helpers
# ---------------------------------------------------------------------------

RANK_COLS = ["slope_p50_90m", "frac_gt8_90m", "frac_gt20_90m", "relief_90m"]


def _min_scales(target: dict[str, float]) -> np.ndarray:
    """Return min_scale vector for the 4 coarse columns."""
    return np.array(
        [
            1.0,  # slope_p50_90m: 1°
            0.05,  # frac_gt8_90m: 0.05
            0.05,  # frac_gt20_90m: 0.05
            max(target["relief_90m"] * 0.10, 10.0),  # relief: 10% of target, min 10 m
        ]
    )


def _diagonal_d(
    earth: np.ndarray,  # (N, 4)
    target: np.ndarray,  # (4,)
    pop_std: np.ndarray,  # (4,)
    min_scale: np.ndarray,  # (4,)
) -> np.ndarray:
    """Diagonal (uncorrelated) Mahalanobis distance."""
    scale = np.maximum(pop_std, min_scale)
    z = (earth - target) / scale
    return np.sqrt((z**2).sum(axis=1))


# ---------------------------------------------------------------------------
# Non-max suppression: within 30 km radius keep lower d
# ---------------------------------------------------------------------------


def _nms_30km(df: pd.DataFrame, d_col: str = "d_coarse") -> pd.DataFrame:
    """Remove cells closer than 30 km to a better (lower-d) neighbour.

    Uses a simple O(N²) pass — N≤300 so this is fast.
    Haversine distance.
    """
    lats = df["lat"].to_numpy()
    lons = df["lon"].to_numpy()
    ds = df[d_col].to_numpy()
    n = len(df)
    keep = np.ones(n, dtype=bool)

    for i in range(n):
        if not keep[i]:
            continue
        for j in range(i + 1, n):
            if not keep[j]:
                continue
            dist_km = _haversine_km(lats[i], lons[i], lats[j], lons[j])
            if dist_km < 30.0:
                # Remove the one with larger d
                if ds[i] <= ds[j]:
                    keep[j] = False
                else:
                    keep[i] = False
                    break  # i is gone, skip rest for i

    return df[keep].copy()


def _haversine_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    R = 6371.0
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)
    a = (
        math.sin(dlat / 2) ** 2
        + math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.sin(dlon / 2) ** 2
    )
    return R * 2 * math.asin(math.sqrt(a))


# ---------------------------------------------------------------------------
# Stratified null sample
# ---------------------------------------------------------------------------

BAND_EDGES = [-60, -40, -20, 0, 20, 40, 60, 84]  # 7 bands


def _latitude_band(lat: float) -> int:
    """Return band index (0-based) for a given latitude."""
    for i in range(len(BAND_EDGES) - 1):
        if BAND_EDGES[i] <= lat < BAND_EDGES[i + 1]:
            return i
    return len(BAND_EDGES) - 2  # clamp to last band


def _stratified_null(
    tier1: pd.DataFrame,
    exclude_ids: set[str],
    n_total: int = 200,
    seed: int = 20261114,
) -> pd.DataFrame:
    """Sample n_total cells stratified by 20°-latitude band.

    Cells in exclude_ids are removed before sampling.
    Allocation is proportional to band population after exclusion.
    """
    pool = tier1[~tier1["cell_id"].isin(exclude_ids)].copy()
    pool["_band"] = pool["lat"].apply(_latitude_band)

    band_counts = pool.groupby("_band").size()
    total_pool = band_counts.sum()
    if total_pool < n_total:
        raise RuntimeError(f"Pool too small for null sample: {total_pool} < {n_total}")

    # Proportional allocation
    allocation = (band_counts / total_pool * n_total).apply(np.floor).astype(int)
    deficit = n_total - allocation.sum()
    # Distribute remainder to largest bands
    remainders = (band_counts / total_pool * n_total) - allocation
    for band_idx in remainders.nlargest(int(deficit)).index:
        allocation[band_idx] += 1

    rng = np.random.default_rng(seed)
    sampled = []
    for band_idx, quota in allocation.items():
        if quota == 0:
            continue
        band_pool = pool[pool["_band"] == band_idx]
        chosen = band_pool.sample(
            n=min(quota, len(band_pool)), random_state=int(rng.integers(2**31))
        )
        sampled.append(chosen)

    result = pd.concat(sampled, ignore_index=True)
    result = result.drop(columns=["_band"])
    return result


# ---------------------------------------------------------------------------
# Control / decoy / seed fallback lists
# ---------------------------------------------------------------------------

FALLBACK_CONTROLS = [
    {"name": "Haughton", "lat": 75.38, "lon": -89.68, "expected": "high", "sample_role": "control"},
    {
        "name": "SP_Crater",
        "lat": 35.58,
        "lon": -111.63,
        "expected": "uncertain",
        "sample_role": "control",
    },
    {
        "name": "Kilauea",
        "lat": 19.41,
        "lon": -155.29,
        "expected": "uncertain",
        "sample_role": "control",
    },
    {
        "name": "Lava_Beds",
        "lat": 41.71,
        "lon": -121.51,
        "expected": "uncertain",
        "sample_role": "control",
    },
    {
        "name": "Mistastin",
        "lat": 55.88,
        "lon": -63.31,
        "expected": "uncertain",
        "sample_role": "control",
    },
    {"name": "Wadi_Rum", "lat": 29.58, "lon": 35.42, "expected": "low", "sample_role": "decoy"},
]

SEEDS = [
    {"name": "Peary_Land", "lat": 82.5, "lon": -33.0},
    {"name": "Harrat_Khaybar", "lat": 25.7, "lon": 39.9},
    {"name": "Karakul", "lat": 39.0, "lon": 73.5},
    {"name": "Tenoumer", "lat": 22.92, "lon": -10.40},
    {"name": "Roter_Kamm", "lat": -27.77, "lon": 16.29},
    {"name": "Wolfe_Creek", "lat": -19.17, "lon": 127.80},
]


def _load_controls_yaml(controls_path: Path) -> tuple[list[dict], list[dict]]:
    """Load controls.yaml; return (controls, decoys) or ([], []) if absent."""
    if not controls_path.exists():
        return [], []
    with open(controls_path) as f:
        data = yaml.safe_load(f) or {}
    entries = data if isinstance(data, list) else data.get("entries", data.get("controls", []))
    controls, decoys = [], []
    for entry in entries:
        lens_ids = entry.get("lens_id", [])
        if isinstance(lens_ids, str):
            lens_ids = [lens_ids]
        if not any(lid in ("L1", "L2") for lid in lens_ids):
            continue
        expected = entry.get("expected", "uncertain")
        role = "decoy" if expected == "low" else "control"
        item = {
            "name": entry.get("name", entry.get("id", "unknown")),
            "lat": float(entry["lat"]),
            "lon": float(entry["lon"]),
            "expected": expected,
            "sample_role": role,
        }
        if role == "control":
            controls.append(item)
        else:
            decoys.append(item)
    return controls, decoys


def _special_rows(items: list[dict], role_prefix: str, source: str) -> list[dict]:
    """Convert control/decoy/seed dicts to output row dicts."""
    rows = []
    for item in items:
        name = item["name"]
        rows.append(
            {
                "cell_id": f"{role_prefix}{name}",
                "lat": item["lat"],
                "lon": item["lon"],
                "sample_role": item.get("sample_role", role_prefix.rstrip("_").lower()),
                "d_coarse": float("nan"),
                "in_exclusion_buffer": False,
                "name": name,
                "expected": item.get("expected", ""),
                "source": source,
            }
        )
    return rows


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------


def main() -> None:
    tier1 = pd.read_parquet(ROOT / "data/derived/tier1_terrain.parquet")
    coarse = pd.read_parquet(ROOT / "data/derived/targets_L1_coarse.parquet")

    # --- reference target: Connecting Ridge ---
    ref_row = coarse[(coarse["target_id"] == "connecting_ridge") & (coarse["is_reference"])].iloc[0]
    target = ref_row[RANK_COLS].to_numpy(dtype=np.float64)

    pop = coarse[~coarse["is_reference"].astype(bool)]
    pop_std = pop[RANK_COLS].std().to_numpy(dtype=np.float64)
    min_scale = _min_scales({"relief_90m": float(ref_row["relief_90m"])})

    # --- RANK: compute d for all tier1 cells, pick top 300 + NMS ---
    earth_mat = tier1[RANK_COLS].to_numpy(dtype=np.float64).copy()
    # Replace NaN with large value so they sort last
    earth_mat = np.where(np.isnan(earth_mat), 1e9, earth_mat)

    d_all = _diagonal_d(earth_mat, target, pop_std, min_scale)
    tier1 = tier1.copy()
    tier1["d_coarse"] = d_all

    # Sort by d, take top 600 candidates before NMS to give NMS room to work
    top_pool = tier1.nsmallest(600, "d_coarse").copy()
    top_pool = _nms_30km(top_pool, "d_coarse")
    rank_df = top_pool.nsmallest(300, "d_coarse").copy()
    rank_df["sample_role"] = "rank"
    rank_df["name"] = ""
    rank_df["expected"] = ""
    rank_df["source"] = "tier1_terrain"

    rank_ids = set(rank_df["cell_id"].tolist())

    # --- NULL: stratified random sample, excluding rank cells ---
    null_pool_df = _stratified_null(tier1, rank_ids, n_total=200, seed=20261114)
    null_df = null_pool_df.copy()
    null_df["sample_role"] = "null"
    null_df["name"] = ""
    null_df["expected"] = ""
    null_df["source"] = "tier1_terrain"
    # d_coarse stays (from tier1 augmented with d_coarse above)

    # --- CONTROL / DECOY from controls.yaml or fallback ---
    controls_path = ROOT / "config" / "controls.yaml"
    yaml_controls, yaml_decoys = _load_controls_yaml(controls_path)
    if yaml_controls or yaml_decoys:
        ctrl_source = "controls.yaml"
        ctrl_items = yaml_controls
        decoy_items = yaml_decoys
    else:
        ctrl_source = "PLAN suggestion (controls.yaml not yet merged)"
        ctrl_items = [c for c in FALLBACK_CONTROLS if c["sample_role"] == "control"]
        decoy_items = [c for c in FALLBACK_CONTROLS if c["sample_role"] == "decoy"]

    ctrl_rows = _special_rows(ctrl_items, "CTRL_", ctrl_source)
    decoy_rows = _special_rows(decoy_items, "DECOY_", ctrl_source)

    # --- SEED ---
    seed_rows = _special_rows(
        [
            {
                "name": s["name"],
                "lat": s["lat"],
                "lon": s["lon"],
                "expected": "",
                "sample_role": "seed",
            }
            for s in SEEDS
        ],
        "SEED_",
        "PLAN seeds",
    )

    # --- Assemble output ---
    out_cols = [
        "cell_id",
        "lat",
        "lon",
        "sample_role",
        "d_coarse",
        "in_exclusion_buffer",
        "name",
        "expected",
        "source",
    ]

    rank_out = rank_df[
        [
            "cell_id",
            "lat",
            "lon",
            "sample_role",
            "d_coarse",
            "in_exclusion_buffer",
            "name",
            "expected",
            "source",
        ]
    ].copy()
    null_out = null_df[
        [
            "cell_id",
            "lat",
            "lon",
            "sample_role",
            "d_coarse",
            "in_exclusion_buffer",
            "name",
            "expected",
            "source",
        ]
    ].copy()

    special_dfs = []
    for rows in (ctrl_rows, decoy_rows, seed_rows):
        if rows:
            special_dfs.append(pd.DataFrame(rows, columns=out_cols))

    all_parts = [rank_out, null_out] + special_dfs
    result = pd.concat(all_parts, ignore_index=True)

    out_path = ROOT / "data/derived/tier2_L1_selection.csv"
    result.to_csv(out_path, index=False)

    print(f"Written {len(result)} rows to {out_path}")
    print(f"  rank: {(result['sample_role'] == 'rank').sum()}")
    print(f"  null: {(result['sample_role'] == 'null').sum()}")
    print(f"  control: {(result['sample_role'] == 'control').sum()}")
    print(f"  decoy: {(result['sample_role'] == 'decoy').sum()}")
    print(f"  seed: {(result['sample_role'] == 'seed').sum()}")
    print(f"  in_exclusion_buffer: {result['in_exclusion_buffer'].sum()} rows flagged")


if __name__ == "__main__":
    main()
