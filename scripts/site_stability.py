"""PLAN 2e — is a ridge match one lucky 4 km footprint, or an area a camp could work in?

For each usable Connecting Ridge cell, the 3 x 3 block of 4 km footprints centred on it (the
cell and its eight neighbours, 4 km apart) is scored with the unchanged rule, once from
Copernicus GLO-30 and once from the second DEM (NASADEM / ArcticDEM). The same block is scored
around the six classic control sites (first DEM only): is any footprint next to the famous one a
match? Exploratory local
sensitivity (Deviations 29): neighbours are NOT candidates and never enter verdicts.parquet.

Output: data/derived/site_stability.parquet
Usage : EE_PROJECT=<project> python scripts/site_stability.py
"""

from __future__ import annotations

import sys

import numpy as np
import pandas as pd

from similitude import io
from similitude.descriptors.terrain import terrain_descriptors

sys.path.insert(0, str(io.REPO_ROOT / "scripts"))
import cross_dem as cd  # noqa: E402
import l1_regions as lr  # noqa: E402
from gee.chip_dem import get_chip  # noqa: E402

DERIVED = io.REPO_ROOT / "data" / "derived"
STEP_M = 4000.0


def block(lat: float, lon: float) -> list[tuple[int, int, float, float]]:
    out = []
    for dy in (-1, 0, 1):
        for dx in (-1, 0, 1):
            la = lat + dy * STEP_M / 111_320.0
            lo = lon + dx * STEP_M / (111_320.0 * max(np.cos(np.radians(lat)), 1e-6))
            out.append((dx, dy, round(la, 5), round(lo, 5)))
    return out


def _desc(dem: np.ndarray, cid: str) -> tuple[dict, dict, bool]:
    ok = float(np.isnan(dem).mean()) < 0.05
    a = terrain_descriptors(dem, cd.RES_M, 30.0, radius_m=cd.EARTH_R, footprint_m=cd.FOOTPRINT_M)
    b = terrain_descriptors(dem, cd.RES_M, 60.0, radius_m=cd.EARTH_R, footprint_m=cd.FOOTPRINT_M)
    return {"cell_id": cid, **a}, {"cell_id": cid, **b}, ok


def main() -> None:
    crit = pd.read_parquet(DERIVED / "mission_criteria.parquet")
    kept = crit[crit["group"].isin(["Engine match", "Classic analog"])]
    earth = pd.read_parquet(DERIVED / "earth_L1.parquet").drop_duplicates("cell_id")
    earth = earth.set_index("cell_id")
    ctx = lr.context()
    rows = []
    for k in kept.itertuples():
        lat, lon = float(earth.loc[k.id, "lat"]), float(earth.loc[k.id, "lon"])
        src = cd.source_for(lat)
        # classic controls: first DEM only (is any footprint next to the famous one a match?)
        for dem_name in (("GLO-30", src) if k.group == "Engine match" else ("GLO-30",)):
            d30, d60, meta = [], [], []
            for dx, dy, la, lo in block(lat, lon):
                cid = f"{k.id}:{dx:+d}{dy:+d}"
                try:
                    dem = (get_chip(la, lo, chip_m=10_000, res_m=30.0)[0] if dem_name == "GLO-30"
                           else cd.alt_chip(la, lo, src))
                    a, b, ok = _desc(dem, cid)
                except Exception as exc:
                    print(f"  {cid} {dem_name}: {type(exc).__name__} {str(exc)[:80]}")
                    a, b, ok = {"cell_id": cid}, {"cell_id": cid}, False
                d30.append(a)
                d60.append(b)
                meta.append({"cell_id": cid, "anchor": k.id, "site": k.name, "group": k.group,
                             "dx": dx, "dy": dy,
                             "lat": la, "lon": lo, "dem": dem_name, "ok": ok})
            e30, e60 = pd.DataFrame(d30), pd.DataFrame(d60)
            s = lr.score_cells(ctx, e30, e60, ["connecting_ridge"])
            keep = ["cell_id", "nr_i", "nr_ii", "nr_iii", "n_i", "robust"]
            rows.append(pd.DataFrame(meta).merge(s[keep], on="cell_id").merge(
                e30[["cell_id", "frac_gt8", "frac_gt20"]], on="cell_id"))
    out = pd.concat(rows, ignore_index=True)
    out.loc[~out["ok"], "robust"] = False
    out.to_parquet(DERIVED / "site_stability.parquet", index=False)
    g = out[out["ok"]].groupby(["group", "site", "dem"]).agg(
        n=("robust", "size"), robust=("robust", "sum"), any_config=(
            "nr_i", lambda s: int(((out.loc[s.index, ["nr_i", "nr_ii", "nr_iii"]].to_numpy()
                                    >= out.loc[s.index, "n_i"].to_numpy()[:, None] / 2)
                                   .any(axis=1)).sum())))
    print(g.to_string())


if __name__ == "__main__":
    main()
