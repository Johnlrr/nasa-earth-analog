"""PLAN 2e — a larger random sample of bare land for unbiased prevalence estimates.

The pre-registered null sample has 200 cells; one of them passes the L1 robust test for
Connecting Ridge, so the prevalence estimate is 0.5 % with a 95 % CI of 0.01-2.8 %. This script
draws 800 more cells by the SAME rule (scripts/select_tier2.py `_stratified_null`: bare-land cells
of tier 1, proportional to 20-degree latitude bands), with a new seed, excluding the screened
cells and the first 200 null cells, and computes the same L1 descriptors at L = 30 m and 60 m
from the same DEM (Copernicus GLO-30). Drawn before any of the new cells was scored.

Post hoc extension of the sample (Deviations 28). The original 200 cells are never altered.

Outputs: data/derived/earth_L1_null2.parquet, data/derived/earth_L1_null2_L60.parquet
Usage  : python scripts/null_expand.py [--n 800]
"""

from __future__ import annotations

import argparse
import sys
from concurrent.futures import ProcessPoolExecutor

import pandas as pd

from similitude import io
from similitude.descriptors.terrain import terrain_descriptors

sys.path.insert(0, str(io.REPO_ROOT / "scripts"))
from gee.chip_dem import get_chip  # noqa: E402
from select_tier2 import _stratified_null  # noqa: E402

DERIVED = io.REPO_ROOT / "data" / "derived"
OUT, OUT60 = DERIVED / "earth_L1_null2.parquet", DERIVED / "earth_L1_null2_L60.parquet"
SEED = 20261115
RES_M, FOOTPRINT_M, EARTH_R = 30.0, 4000.0, 6_371_000.0


def draw(n: int) -> pd.DataFrame:
    tier1 = pd.read_parquet(DERIVED / "tier1_terrain.parquet")
    earth = pd.read_parquet(DERIVED / "earth_L1.parquet")
    used = set(earth.loc[earth["sample_role"].isin(["rank", "null"]), "cell_id"])
    return _stratified_null(tier1, used, n_total=n, seed=SEED)


def _one(row: tuple) -> tuple[dict, dict]:
    cell_id, lat, lon, zone = row
    base = {"cell_id": cell_id, "lat": lat, "lon": lon, "sample_role": "null2",
            "in_exclusion_buffer": bool(zone), "L_m": RES_M}
    try:
        dem, meta = get_chip(lat, lon, chip_m=10_000, res_m=RES_M)
        nodata = float(meta.get("nodata_frac", 1.0))
        d30 = terrain_descriptors(dem, RES_M, 30.0, radius_m=EARTH_R, footprint_m=FOOTPRINT_M)
        d60 = terrain_descriptors(dem, RES_M, 60.0, radius_m=EARTH_R, footprint_m=FOOTPRINT_M)
        return ({**base, "qa_flag": "ok" if nodata < 0.05 else "nodata", **d30},
                {"cell_id": cell_id, **d60})
    except Exception as exc:  # recorded, never silently dropped
        return ({**base, "qa_flag": f"error:{str(exc)[:120]}"}, {"cell_id": cell_id})


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--n", type=int, default=800)
    ap.add_argument("--workers", type=int, default=12)
    args = ap.parse_args()
    cells = draw(args.n)
    rows = list(cells[["cell_id", "lat", "lon", "in_exclusion_buffer"]].itertuples(
        index=False, name=None))
    with ProcessPoolExecutor(max_workers=args.workers) as ex:  # descriptors are CPU-bound
        out = list(ex.map(_one, rows, chunksize=4))
    pd.DataFrame([a for a, _ in out]).to_parquet(OUT, index=False)
    pd.DataFrame([b for _, b in out]).to_parquet(OUT60, index=False)
    e = pd.read_parquet(OUT)
    print(f"{len(e)} cells; qa: {e['qa_flag'].str.slice(0, 12).value_counts().to_dict()}")


if __name__ == "__main__":
    main()
