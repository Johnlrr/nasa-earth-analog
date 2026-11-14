"""A12: L1 robust set (rule committed in PLAN before this run).

A cell belongs to the robust set for a reference target when
``native_rank >= n_native / 2`` under ALL three configurations:
  (i)   diagonal metric, the 11 lens descriptors at L = 30 m (= fidelity.parquet)
  (ii)  full metric on [slope_p50, slope_p90, frac_gt20, rms_s1, rms_s16, hurst], L = 30 m
  (iii) the 11 lens descriptors recomputed at L = 60 m on both sides (cached chips)
Robust cells are thinned by NMS (30 km, keep the higher median native rank); all are
reported. If the intersection is empty the set falls back to (i) with a sensitivity note.

Outputs: data/derived/l1_robust_set.parquet (+ L60 descriptor caches
data/derived/earth_L1_L60.parquet, data/derived/targets_L1_L60.parquet).

Usage: .venv/bin/python scripts/l1_robust.py [--recompute-l60]
"""

from __future__ import annotations

import sys
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / "scripts"))

from similitude import io  # noqa: E402
from similitude.descriptors.terrain import terrain_descriptors  # noqa: E402
from similitude.fidelity import (  # noqa: E402
    _great_circle_m,
    _min_scale,
    fit_population,
    mahalanobis_d,
    native_population,
    native_rank,
)

DERIVED = ROOT / "data" / "derived"
OUT = DERIVED / "l1_robust_set.parquet"
EARTH_L60 = DERIVED / "earth_L1_L60.parquet"
TARGETS_L60 = DERIVED / "targets_L1_L60.parquet"
SUBSET_II = ["slope_p50", "slope_p90", "frac_gt20", "rms_s1", "rms_s16", "hurst"]
L60 = 60.0
FOOTPRINT_M = 4000.0
NMS_KM = 30.0
EARTH_R = 6_371_000.0


# ---------------------------------------------------------------------------
# L = 60 m descriptors from cached chips
# ---------------------------------------------------------------------------


def _earth_l60(row: tuple[str, float, float]) -> dict:
    from gee.chip_dem import get_chip

    cell_id, lat, lon = row
    dem, _ = get_chip(lat, lon, chip_m=10_000, res_m=30.0)
    d = terrain_descriptors(dem, 30.0, L60, radius_m=EARTH_R, footprint_m=FOOTPRINT_M)
    return {"cell_id": cell_id, **d}


def earth_l60(earth: pd.DataFrame) -> pd.DataFrame:
    rows = list(earth[["cell_id", "lat", "lon"]].itertuples(index=False, name=None))
    with ProcessPoolExecutor(max_workers=8) as ex:
        out = list(ex.map(_earth_l60, rows, chunksize=8))
    return pd.DataFrame(out)


def moon_l60() -> pd.DataFrame:
    """Recompute the PGDA footprints (same centres and ids as targets_L1) at L = 60 m."""
    import rasterio
    from pyproj import CRS
    from targets import moon_terrain as mt

    rows = []
    for code, name in mt.SITES.items():
        with rasterio.open(mt.DATA_RAW / f"{code}_final_adj_5mpp_surf.tif") as ds:
            dem5 = ds.read(1).astype(np.float64)
            if ds.nodata is not None and not np.isnan(ds.nodata):
                dem5[dem5 == ds.nodata] = np.nan
            tr = ds.transform
        centres = []
        if code in mt.REFERENCE_SITES:
            centres.append((f"{name}_ref", tr.c + dem5.shape[1] / 2 * tr.a,
                            tr.f + dem5.shape[0] / 2 * tr.e))
        grid = mt._grid_footprints(dem5, tr, mt.GRID_STEP_M)
        if len(grid) < 5:
            grid = mt._grid_footprints(dem5, tr, mt.GRID_STEP_FALLBACK)
        centres += [(f"{name}_pop_{i:03d}", cx, cy) for i, (cx, cy) in enumerate(grid)]
        for fp_id, cx, cy in centres:
            chip = mt._chip_at(dem5, tr, mt.CHIP_M, cx, cy)
            if chip is None:
                continue
            d = terrain_descriptors(chip, 5.0, L60, radius_m=mt.RADIUS_M,
                                    footprint_m=mt.FOOTPRINT_M)
            rows.append({"footprint_id": fp_id, **d})
        print(f"  moon L60 {code}: {len(centres)} footprints", flush=True)
    del CRS
    return pd.DataFrame(rows)


# ---------------------------------------------------------------------------
# native rank per configuration
# ---------------------------------------------------------------------------


def rank_config(earth: pd.DataFrame, targets: pd.DataFrame, lens: dict, names: list[str],
                mode: str) -> pd.DataFrame:
    """native_rank of every earth cell vs each reference target under one configuration."""
    ref = targets[targets.is_reference.astype(bool)]
    pop = targets[~targets.is_reference.astype(bool)]
    out = []
    for _, t in ref.iterrows():
        tv = t[names].to_numpy(float)
        ms = np.array([_min_scale(lens, n, t[n]) for n in names])
        m = fit_population(pop[names].to_numpy(float), ms, mode=mode)
        nat = native_population(pop, t)
        d_nat = mahalanobis_d(nat[names].to_numpy(float), tv, m)
        d = mahalanobis_d(earth[names].to_numpy(float), tv, m)
        out.append(pd.DataFrame({
            "cell_id": earth.cell_id.to_numpy(), "target_id": t.target_id,
            "native_rank": native_rank(d, d_nat), "n_native": len(nat), "metric_mode": m.mode,
        }))
    return pd.concat(out, ignore_index=True)


def nms(df: pd.DataFrame, km: float) -> pd.Series:
    """Greedy NMS on (lat, lon): keep highest score, drop others within ``km``."""
    order = df.sort_values(["score", "cell_id"], ascending=[False, True]).index
    keep: list[int] = []
    for i in order:
        if all(_great_circle_m(df.at[i, "lat"], df.at[i, "lon"], df.at[j, "lat"],
                               df.at[j, "lon"], EARTH_R) >= km * 1000 for j in keep):
            keep.append(i)
    return df.index.isin(keep)


def main() -> None:
    from run_all import load

    lens = io.load_lenses()["L1"]
    names = lens["descriptors"]
    earth, targets = load("L1")

    if "--recompute-l60" in sys.argv or not (EARTH_L60.exists() and TARGETS_L60.exists()):
        print("computing L = 60 m descriptors ...", flush=True)
        e60 = earth_l60(earth)
        e60.to_parquet(EARTH_L60, index=False)
        m60 = moon_l60()
        m60.to_parquet(TARGETS_L60, index=False)
    e60 = pd.read_parquet(EARTH_L60)
    m60 = pd.read_parquet(TARGETS_L60)
    earth60 = earth[["cell_id"]].merge(e60, on="cell_id", how="left")
    meta = ["footprint_id", "target_id", "is_reference", "lat", "lon", "body", "footprint_m"]
    targets60 = targets[meta].merge(m60, on="footprint_id", how="inner")
    if len(targets60) != len(targets):
        raise SystemExit(f"L60 moon footprints {len(targets60)} != targets_L1 {len(targets)}")

    cfg = {
        "i": rank_config(earth, targets, lens, names, "diag"),
        "ii": rank_config(earth, targets, lens, SUBSET_II, "auto"),
        "iii": rank_config(earth60, targets60, lens, names, "diag"),
    }
    res = None
    for k, df in cfg.items():
        df = df.rename(columns={"native_rank": f"nr_{k}", "n_native": f"n_{k}",
                                "metric_mode": f"mode_{k}"})
        df[f"in_{k}"] = df[f"nr_{k}"] >= df[f"n_{k}"] / 2
        res = df if res is None else res.merge(df, on=["cell_id", "target_id"])
    info = earth[["cell_id", "lat", "lon", "sample_role", "name"]]
    res = res.merge(info, on="cell_id")
    res["robust"] = res.in_i & res.in_ii & res.in_iii
    res["score"] = res[["nr_i", "nr_ii", "nr_iii"]].median(axis=1)

    cand = res.sample_role.isin(["rank", "seed"])
    res["set_rule"] = "intersection (i)&(ii)&(iii)"
    res["nms_keep"] = False
    for tid, sub in res[cand].groupby("target_id"):
        member = sub[sub.robust]
        if member.empty:
            member = sub[sub.in_i]
            res.loc[member.index, "set_rule"] = "fallback (i) only: intersection empty"
        res.loc[member.index, "nms_keep"] = nms(member, NMS_KM)
        print(f"\n{tid}: rank+seed cells {len(sub)} | (i) {sub.in_i.sum()} (ii) "
              f"{sub.in_ii.sum()} (iii) {sub.in_iii.sum()} | intersection {sub.robust.sum()} "
              f"| union {(sub.in_i | sub.in_ii | sub.in_iii).sum()} | after NMS {30:.0f} km "
              f"{res.loc[member.index, 'nms_keep'].sum()} | modes "
              f"{sub.mode_i.iloc[0]}/{sub.mode_ii.iloc[0]}/{sub.mode_iii.iloc[0]} "
              f"n_native {sub.n_i.iloc[0]}")
        top = res.loc[member.index][res.loc[member.index, "nms_keep"]].nlargest(10, "score")
        print(top[["cell_id", "name", "lat", "lon", "nr_i", "nr_ii", "nr_iii"]]
              .round(2).to_string(index=False))
    res.to_parquet(OUT, index=False)
    print(f"\nwrote {OUT.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
