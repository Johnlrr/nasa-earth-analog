"""PLAN 2e — does the L1 verdict survive a second, independent Earth DEM?

The published verdicts use Copernicus GLO-30 (TanDEM-X radar, 2011-2015). This script recomputes
the same L1 descriptors, with the same code and baselines, from NASADEM (NASA, SRTM C-band radar,
2000; 60 S-60 N) and, above 60 N, from the ArcticDEM mosaic (stereo optical, averaged to 30 m),
for the cells kept for Connecting Ridge, the classic controls and a seeded sample of the cells
kept for the Shackleton inner wall. It then applies the unchanged robust-set rule.

Post hoc robustness check (Deviations 29): no threshold or verdict changes.

Output: data/derived/cross_dem.parquet (+ chips cached in data/raw/earth/chips_alt/)
Usage : EE_PROJECT=<project> python scripts/cross_dem.py [--n-wall 30]
"""

from __future__ import annotations

import argparse
import io as _io
import os
import sys

import numpy as np
import pandas as pd

from similitude import io
from similitude.descriptors.terrain import terrain_descriptors

sys.path.insert(0, str(io.REPO_ROOT / "scripts"))
import l1_regions as lr  # noqa: E402
from gee.chip_dem import _utm_epsg  # noqa: E402

DERIVED = io.REPO_ROOT / "data" / "derived"
CACHE = io.REPO_ROOT / "data" / "raw" / "earth" / "chips_alt"
CHIP_M, RES_M, FOOTPRINT_M, EARTH_R = 10_000.0, 30.0, 4000.0, 6_371_000.0
SEED = 20261115
SOURCES = {"NASADEM": "NASA/NASADEM_HGT/001", "ArcticDEM": "UMN/PGC/ArcticDEM/V3/2m_mosaic"}


def source_for(lat: float) -> str | None:
    if -56.0 <= lat <= 60.0:
        return "NASADEM"
    return "ArcticDEM" if lat > 60.0 else None


def alt_chip(lat: float, lon: float, source: str) -> np.ndarray:
    """10 km chip at 30 m in the local UTM zone, same geometry as gee.chip_dem.get_chip."""
    path = CACHE / f"{source}_{lat:.4f}_{lon:.4f}.npy"
    if path.exists():
        return np.load(path)
    import ee
    from pyproj import Transformer

    ee.Initialize(project=os.environ["EE_PROJECT"])
    epsg = _utm_epsg(lat, lon)
    x, y = Transformer.from_crs(4326, epsg, always_xy=True).transform(lon, lat)
    n = int(round(CHIP_M / RES_M))
    img = ee.Image(SOURCES[source]).select("elevation")
    if source == "ArcticDEM":  # 2 m mosaic -> mean over the 30 m pixel
        img = img.reduceResolution(ee.Reducer.mean(), bestEffort=True, maxPixels=1024)
    else:
        img = img.resample("bilinear")
    raw = ee.data.computePixels({
        "expression": img.toFloat(), "fileFormat": "NPY",
        "grid": {"dimensions": {"width": n, "height": n}, "crsCode": f"EPSG:{epsg}",
                 "affineTransform": {"scaleX": RES_M, "shearX": 0, "translateX": x - CHIP_M / 2,
                                     "shearY": 0, "scaleY": -RES_M,
                                     "translateY": y + CHIP_M / 2}}})
    dem = np.load(_io.BytesIO(raw))["elevation"].astype(np.float64)
    dem[~np.isfinite(dem) | (dem < -1000)] = np.nan
    CACHE.mkdir(parents=True, exist_ok=True)
    np.save(path, dem)
    return dem


def cells_to_check(n_wall: int) -> pd.DataFrame:
    earth = pd.read_parquet(DERIVED / "earth_L1.parquet").drop_duplicates("cell_id")
    rob = pd.read_parquet(DERIVED / "l1_robust_set.parquet")
    rank = rob["sample_role"].isin(["rank", "seed"]) & rob["robust"]
    ridge = set(rob[rank & rob["target_id"].eq("connecting_ridge")]["cell_id"])
    wall = rob[rank & rob["target_id"].eq("shackleton_rim")]["cell_id"]
    wall = set(wall.sample(n=min(n_wall, len(wall)), random_state=SEED))
    ctrl = set(earth[earth["cell_id"].str.startswith("CTRL_")]["cell_id"])
    out = earth[earth["cell_id"].isin(ridge | wall | ctrl)][["cell_id", "lat", "lon", "name"]]
    out = out.assign(group=["ridge match" if c in ridge else "control" if c in ctrl
                            else "wall match" for c in out["cell_id"]])
    return out.reset_index(drop=True)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--n-wall", type=int, default=30)
    args = ap.parse_args()
    cells = cells_to_check(args.n_wall)
    d30, d60, src = [], [], []
    for r in cells.itertuples():
        s = source_for(r.lat)
        src.append(s)
        try:
            dem = alt_chip(r.lat, r.lon, s)
            ok = float(np.isnan(dem).mean()) < 0.05
            a = terrain_descriptors(dem, RES_M, 30.0, radius_m=EARTH_R, footprint_m=FOOTPRINT_M)
            b = terrain_descriptors(dem, RES_M, 60.0, radius_m=EARTH_R, footprint_m=FOOTPRINT_M)
        except Exception as exc:
            print(f"  {r.cell_id}: {type(exc).__name__} {str(exc)[:100]}")
            ok, a, b = False, {}, {}
        d30.append({"cell_id": r.cell_id, "alt_ok": ok, **a})
        d60.append({"cell_id": r.cell_id, **b})
    e30, e60 = pd.DataFrame(d30), pd.DataFrame(d60)
    ctx = lr.context()
    alt = lr.score_cells(ctx, e30, e60, ["connecting_ridge", "shackleton_rim"])
    base = pd.read_parquet(DERIVED / "l1_robust_set.parquet")[
        ["cell_id", "target_id", "robust"]].rename(columns={"robust": "robust_glo30"})
    earth = pd.read_parquet(DERIVED / "earth_L1.parquet").drop_duplicates("cell_id")
    keep = ["frac_gt8", "frac_gt20", "slope_p50"]
    out = (alt.merge(base, on=["cell_id", "target_id"], how="left")
           .merge(cells.assign(alt_source=src), on="cell_id")
           .merge(e30[["cell_id", "alt_ok", *keep]].rename(columns={k: f"{k}_alt" for k in keep}),
                  on="cell_id")
           .merge(earth[["cell_id", *keep]].rename(columns={k: f"{k}_glo30" for k in keep}),
                  on="cell_id"))
    out.to_parquet(DERIVED / "cross_dem.parquet", index=False)
    v = out[out["alt_ok"]]
    for (g, t), d in v.groupby(["group", "target_id"]):
        print(f"{g:12s} {t:17s} n={len(d):3d} robust GLO-30 {int(d['robust_glo30'].sum()):3d} "
              f"robust alt {int(d['robust'].sum()):3d} agree "
              f"{int((d['robust'] == d['robust_glo30']).sum()):3d}")
    print(out[out["group"].ne("wall match") & out["target_id"].eq("connecting_ridge")][
        ["cell_id", "alt_source", "alt_ok", "frac_gt8_glo30", "frac_gt8_alt", "frac_gt20_glo30",
         "frac_gt20_alt", "robust_glo30", "robust"]].round(3).to_string(index=False))


if __name__ == "__main__":
    main()
