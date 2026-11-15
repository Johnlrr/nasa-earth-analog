"""B: a crewed-landing candidate with shallow ice (Arcadia Planitia, HiRISE DTM) as the terrain
target, combined with the X1 ice test on Earth (pre-registered, config/prereg_mars_base.yaml).

DTM (1 m), download once into data/raw/mars/dtm/:
  https://uahirise.org/PDS/DTM/ESP/ORB_060700_060799/ESP_060706_2195_ESP_060416_2195/
  DTEEC_060706_2195_060416_2195_A01.IMG
Earth descriptors (GLO-30 slope and planner outcomes of the 1,000 random cells and the 45
classic Mars footprints) are read from mars_m1_square.parquet, the same chips the M1 lens used.

Outputs: data/derived/mars_base_lens.json, mars_base_lens.parquet
Usage  : EE_PROJECT=<project> python scripts/mars_base_lens.py
"""
from __future__ import annotations

import json
import sys

import numpy as np
import pandas as pd
import rasterio
from scipy import ndimage

from similitude import io
from similitude.descriptors.terrain import aggregate_to_baseline
from similitude.route import OUTCOMES, route_distance

sys.path.insert(0, str(io.REPO_ROOT / "scripts"))
sys.path.insert(0, str(io.REPO_ROOT / "scripts" / "access"))
sys.path.insert(0, str(io.REPO_ROOT / "scripts" / "gee"))
import artemis3_lens as a3  # noqa: E402
import route_validity as rv  # noqa: E402

D = io.REPO_ROOT / "data" / "derived"
DTM = io.REPO_ROOT / "data" / "raw" / "mars" / "dtm" / "DTEEC_060706_2195_060416_2195_A01.IMG"
JEZERO_NULL_SHARE = 187 / 994          # M1 lens, square cells (Deviations 40)
MIN_NEIGHBOURS = 30


def dtm_5m() -> tuple[np.ndarray, dict]:
    with rasterio.open(DTM) as ds:
        z = ds.read(1).astype(np.float32)
        tr = ds.transform
        wkt = ds.crs.to_wkt()
        r_m = ds.crs.to_dict().get("R") or 3389574.3490888
    z[z < -1e30] = np.nan
    sp = 35.0 if "standard_parallel_1\",35]" in wkt else None
    if sp is None:
        raise SystemExit("unexpected projection; check the label before running")
    lat_c = np.degrees((tr.f + tr.e * z.shape[0] / 2) / r_m)
    k = float(np.cos(np.radians(lat_c)) / np.cos(np.radians(sp)))
    # square ground cells: x is k times shorter on the ground than the projected pixel
    zx = ndimage.zoom(np.nan_to_num(z, nan=0.0), (1.0, k), order=1)
    mx = ndimage.zoom(np.isnan(z).astype(np.float32), (1.0, k), order=1) > 0.0
    zx[mx] = np.nan
    z5 = aggregate_to_baseline(zx, abs(tr.a), a3.PX)
    return z5, {"centre_lat": round(float(lat_c), 4), "standard_parallel": sp,
                "x_factor": round(k, 4), "pixel_m": round(abs(tr.a), 4),
                "shape_5m": list(z5.shape)}


def x1(cells: pd.DataFrame) -> pd.DataFrame:
    import os

    import ee
    ee.Initialize(project=os.environ.get("EE_PROJECT"))
    import tier_x1 as tx
    import x1_checklist as xc
    pts = [{"cell_id": r.cell_id, "lat": float(r.lat), "lon": float(r.lon)}
           for r in cells.itertuples()]
    v = tx.sample_points(tx.composite(), pts)
    v = cells[["cell_id", "lat", "lon"]].merge(v, on="cell_id", how="left")
    v["ice_frac"] = xc.ice_fraction(v)
    return xc.evaluate(v)


def main() -> None:
    z5, geo = dtm_5m()
    L = a3.lens(z5)
    thin = L["n_neighbours"] < MIN_NEIGHBOURS
    print(geo, L["n_windows"], L["n_neighbours"], L["tau"])
    e = pd.read_parquet(D / "mars_m1_square.parquet")
    e = e[e.group.isin(["null", "classic_mars"])].drop(columns=["D_slope", "D_route", "match",
                                                               "country"])
    for f, ks in (("slope", list(a3.SLOPE)), ("route", list(OUTCOMES))):
        ok = e[ks].notna().all(axis=1)
        e[f"D_{f}"] = np.where(ok, route_distance(e[ks].fillna(0).to_numpy(), L["vec"][f],
                                                  L["scale"][f]), np.nan)
    e = e.dropna(subset=["D_slope", "D_route"]).copy()
    e["terrain"] = (e.D_slope <= L["tau"]["slope"]) & (e.D_route <= L["tau"]["route"])
    hits = e[e.terrain]
    xv = x1(hits) if len(hits) else pd.DataFrame(columns=["cell_id", "candidate"])
    e = e.merge(xv[["cell_id", "maat_c", "ft_yr", "aridity_p_pet", "failed", "candidate"]],
                on="cell_id", how="left")
    e["x1"] = e["candidate"].fillna(False).astype(bool)
    e["base"] = e.terrain & e.x1
    nh = e[e.group.eq("null") & e.terrain]
    if len(nh):
        import access_screen as acs
        cmap = dict(zip(nh.cell_id, acs.countries(nh).to_numpy(), strict=True))
    else:
        cmap = {}
    e["country"] = e.cell_id.map(cmap)
    e.to_parquet(D / "mars_base_lens.parquet", index=False)
    nu, cl = e[e.group.eq("null")], e[e.group.eq("classic_mars")]
    kt, n = int(nu.terrain.sum()), len(nu)
    kc, nc = int(cl.terrain.sum()), len(cl)
    p = rv.fisher(kc, nc, kt, n)
    base_open = nu[nu.base & nu.country.notna() & ~nu.country.isin(a3.CLOSED)]
    res = {
        "prereg": "config/prereg_mars_base.yaml (commit 30f201d)",
        "target": {"name": "Candidate landing site for SpaceX Starship near Arcadia Planitia",
                   "dtm": DTM.name, **geo,
                   **{k: round(float(v), 4) for k, v in L["ref"].items()}},
        "n_windows": L["n_windows"], "n_neighbours": L["n_neighbours"],
        "exploratory_thin_threshold": thin,
        "tau": {f: round(t, 4) for f, t in L["tau"].items()},
        "null_terrain": [kt, n], "null_terrain_share": round(kt / n, 4),
        "null_terrain_ci": a3.ci(kt, n), "jezero_null_share": round(JEZERO_NULL_SHARE, 4),
        "selective": kt / n < JEZERO_NULL_SHARE,
        "classic_terrain": [kc, nc], "HB1_p": round(p, 5), "HB1_pass": p < 0.05,
        "classic_per_site": {s: [int(t.terrain.sum()), len(t)] for s, t in cl.groupby("site")},
        "null_terrain_and_x1": int(nu.base.sum()),
        "classic_terrain_and_x1": int(cl.base.sum()),
        "base_site_available": len(base_open) > 0,
        "x1_failed_conditions_among_null_terrain_matches":
            nu[nu.terrain].failed.value_counts().to_dict(),
        "terrain_countries": nu[nu.terrain].country.value_counts().to_dict(),
        "base_open": [{"cell_id": r.cell_id, "country": r.country, "lat": round(r.lat, 4),
                       "lon": round(r.lon, 4), "maat_c": round(r.maat_c, 2),
                       "ft_yr": round(r.ft_yr, 1), "aridity_p_pet": round(r.aridity_p_pet, 3),
                       "frac_gt8": round(r.frac_gt8, 3)} for r in base_open.itertuples()]}
    (D / "mars_base_lens.json").write_text(json.dumps(res, indent=2, default=float))
    print(json.dumps(res, indent=1, default=float))


if __name__ == "__main__":
    main()
