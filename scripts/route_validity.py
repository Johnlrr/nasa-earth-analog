"""V1 (pre-registered, config/prereg_route_v1.yaml): do L1 ridge matches reproduce the ridge's
simulated traverse outcomes?

Groups are frozen to data/derived/route_groups.csv before any outcome is computed.
Outputs: data/derived/route_groups.csv, route_validity.parquet, route_validity.json
Usage  : python scripts/route_validity.py
"""
from __future__ import annotations

import json
import sys

import numpy as np
import pandas as pd
import rasterio
from pyproj import CRS, Transformer
from scipy import stats

from similitude import io
from similitude.descriptors.terrain import aggregate_to_baseline, slope_stats
from similitude.fidelity import _min_scale, fit_population, mahalanobis_d
from similitude.route import OUTCOMES, robust_scale, route_distance, route_outcomes

sys.path.insert(0, str(io.REPO_ROOT / "scripts"))
import cross_dem as cd  # noqa: E402
import l1_regions as lr  # noqa: E402
from gee.chip_dem import get_chip  # noqa: E402

DERIVED = io.REPO_ROOT / "data" / "derived"
MOON = io.REPO_ROOT / "data" / "raw" / "moon" / "pgda78" / "Site01_final_adj_5mpp_surf.tif"
TARGET = "connecting_ridge"
FOOT_M, RES = 4000.0, 30.0
SAME_AS_REF_M = 1000.0  # a native footprint centred within 1 km of the reference IS the reference


# ------------------------------------------------------------------------------------------
def groups() -> pd.DataFrame:
    rob = pd.read_parquet(DERIVED / "l1_robust_set.parquet")
    acc = pd.read_parquet(DERIVED / "access_leads.parquet")
    p1 = rob[rob["target_id"].eq(TARGET) & rob["robust"].astype(bool)][["cell_id", "lat", "lon"]]
    p2 = acc[acc["target_id"].eq(TARGET) & acc["robust"].astype(bool)][["cell_id", "lat", "lon"]]
    passers = pd.concat([p1, p2]).drop_duplicates("cell_id").assign(group="passer")
    e = pd.read_parquet(DERIVED / "earth_L1.parquet").drop_duplicates("cell_id")
    n1 = e[e["sample_role"].eq("null")][["cell_id", "lat", "lon"]]
    n2 = pd.read_parquet(DERIVED / "earth_L1_null2.parquet")[["cell_id", "lat", "lon"]]
    null = pd.concat([n1, n2]).drop_duplicates("cell_id").assign(group="null")
    st = pd.read_parquet(DERIVED / "site_stability.parquet")
    cl = st[st["group"].eq("Classic analog") & st["dem"].eq("GLO-30")]
    classic = cl[["cell_id", "lat", "lon"]].assign(group="classic", site=cl["site"].to_numpy())
    return pd.concat([passers, null, classic], ignore_index=True)


def centre(dem: np.ndarray, n_px: int) -> np.ndarray:
    r0 = (dem.shape[0] - n_px) // 2
    c0 = (dem.shape[1] - n_px) // 2
    return dem[r0:r0 + n_px, c0:c0 + n_px]


def earth_footprint(lat: float, lon: float) -> np.ndarray:
    dem, _ = get_chip(lat, lon, chip_m=10_000, res_m=RES)
    return centre(dem, int(FOOT_M // RES))


def moon_footprints() -> tuple[np.ndarray, list[tuple[str, np.ndarray]]]:
    with rasterio.open(MOON) as ds:
        z = ds.read(1).astype(np.float64)
        if ds.nodata is not None:
            z[z == ds.nodata] = np.nan
        tr, crs = ds.transform, CRS.from_wkt(ds.crs.to_wkt())
    half = int(round(FOOT_M / 2 / abs(tr.a)))
    c = z.shape[0] // 2, z.shape[1] // 2
    ref = aggregate_to_baseline(z[c[0] - half:c[0] + half, c[1] - half:c[1] + half], 5.0, RES)
    t = pd.read_parquet(DERIVED / "targets_L1.parquet")
    pop = t[t["target_id"].eq(TARGET) & ~t["is_reference"].astype(bool)]
    to_xy = Transformer.from_crs(crs.geodetic_crs, crs, always_xy=True)
    cx_ref = tr.c + (c[1] + 0.0) * tr.a
    cy_ref = tr.f + (c[0] + 0.0) * tr.e
    nat = []
    for r in pop.itertuples():
        x, y = to_xy.transform(r.lon, r.lat)
        if np.hypot(x - cx_ref, y - cy_ref) < SAME_AS_REF_M:
            continue
        col = int(round((x - tr.c) / tr.a))
        row = int(round((y - tr.f) / tr.e))
        w = z[row - half:row + half, col - half:col + half]
        if w.shape != (2 * half, 2 * half):
            continue
        nat.append((r.footprint_id, aggregate_to_baseline(w, 5.0, RES)))
    return ref, nat


def l1_distance(cells: pd.DataFrame) -> np.ndarray:
    """L1 configuration (i) Mahalanobis distance of Earth descriptor rows to the ridge."""
    ctx = lr.context()
    table, names, mode = ctx["cfg"]["i"]
    tt = ctx[table]
    ref_id = ctx["refs"][TARGET]
    t = tt[tt["footprint_id"].eq(ref_id)].iloc[0]
    pop = tt[tt["footprint_id"].isin(ctx["pop_ids"]) & tt["footprint_id"].ne(ref_id)]
    tv = t[names].to_numpy(float)
    ms = np.array([_min_scale(ctx["lens"], n, t[n]) for n in names])
    m = fit_population(pop[names].to_numpy(float), ms, mode=mode)
    e = pd.concat([pd.read_parquet(DERIVED / "earth_L1.parquet"),
                   pd.read_parquet(DERIVED / "earth_L1_null2.parquet")]).drop_duplicates("cell_id")
    e = cells[["cell_id"]].merge(e[["cell_id", *names]], on="cell_id", how="left")
    return mahalanobis_d(e[names].to_numpy(float), tv, m)


def fisher(a_yes: int, a_n: int, b_yes: int, b_n: int) -> float:
    return float(stats.fisher_exact([[a_yes, a_n - a_yes], [b_yes, b_n - b_yes]],
                                    alternative="greater")[1])


# ------------------------------------------------------------------------------------------
def main() -> None:
    g = groups()
    g.to_csv(DERIVED / "route_groups.csv", index=False)
    print({k: int(v) for k, v in g["group"].value_counts().items()})

    ref, nat = moon_footprints()
    fg8 = slope_stats(ref, RES)["frac_gt8"]
    print(f"ridge 30 m frac_gt8 = {fg8:.4f} (published 0.7584); natives = {len(nat)}")
    o_ref = route_outcomes(ref, RES)
    o_nat = pd.DataFrame([{"cell_id": fid, **route_outcomes(d, RES)} for fid, d in nat])
    scale = robust_scale(o_nat[list(OUTCOMES)].to_numpy())
    o_nat["D_route"] = route_distance(o_nat[list(OUTCOMES)].to_numpy(),
                                      [o_ref[k] for k in OUTCOMES], scale)
    tau = float(np.median(o_nat["D_route"]))
    print(f"tau = {tau:.4f}; scale = {np.round(scale, 4).tolist()}")

    rows = []
    for i, r in enumerate(g.itertuples()):
        try:
            o = route_outcomes(earth_footprint(r.lat, r.lon), RES)
            err = ""
        except Exception as exc:  # missing chip and no network: counted, not imputed
            o, err = {k: np.nan for k in ("nan_frac", *OUTCOMES)}, type(exc).__name__
        rows.append({"cell_id": r.cell_id, "group": r.group, "dem": "GLO-30", **o, "error": err})
        if i % 100 == 0:
            print(f"  {i}/{len(g)}")
    # robustness: passers on the second DEM (cached chips only)
    for r in g[g["group"].eq("passer")].itertuples():
        src = cd.source_for(r.lat)
        try:
            d = centre(cd.alt_chip(r.lat, r.lon, src), int(FOOT_M // RES))
            o, err = route_outcomes(d, RES), ""
        except Exception as exc:
            o, err = {k: np.nan for k in ("nan_frac", *OUTCOMES)}, type(exc).__name__
        rows.append({"cell_id": r.cell_id, "group": "passer_alt", "dem": src, **o, "error": err})

    res = pd.DataFrame(rows)
    ok = res[list(OUTCOMES)].notna().all(axis=1)
    res["D_route"] = np.where(ok, route_distance(res[list(OUTCOMES)].fillna(0).to_numpy(),
                                                 [o_ref[k] for k in OUTCOMES], scale), np.nan)
    res["reproduces"] = res["D_route"] <= tau
    moon = o_nat.assign(group="moon_native", dem="PGDA78")
    moon["reproduces"] = moon["D_route"] <= tau
    ref_row = pd.DataFrame([{"cell_id": "connecting_ridge_ref", "group": "moon_reference",
                             "dem": "PGDA78", **o_ref, "D_route": 0.0, "reproduces": True}])
    out = pd.concat([ref_row, moon, res], ignore_index=True)
    out.to_parquet(DERIVED / "route_validity.parquet", index=False)

    def share(grp):
        s = out[out["group"].eq(grp) & out["D_route"].notna()]
        return int(s["reproduces"].sum()), len(s)

    pa, nu, cl, alt = share("passer"), share("null"), share("classic"), share("passer_alt")
    nulls = out[out["group"].eq("null") & out["D_route"].notna()].copy()
    nulls["d_l1"] = l1_distance(nulls)
    nn = nulls.dropna(subset=["d_l1"])
    rho = float(stats.spearmanr(nn["d_l1"], nn["D_route"])[0])
    h1p, h1bp = fisher(*pa, *nu), fisher(*pa, *cl)
    summary = {
        "prereg": "config/prereg_route_v1.yaml (commit 4e9ceff)",
        "ridge_frac_gt8_30m": round(fg8, 4),
        "n_moon_native": len(o_nat), "tau": round(tau, 4),
        "scale": dict(zip(OUTCOMES, np.round(scale, 5).tolist(), strict=True)),
        "ridge_outcomes": {k: round(o_ref[k], 4) for k in OUTCOMES},
        "moon_native_reproduce": [int(moon["reproduces"].sum()), len(moon)],
        "passer": list(pa), "null": list(nu), "classic": list(cl), "passer_second_dem": list(alt),
        "skipped": {k: int((res["group"].eq(k) & res["D_route"].isna()).sum())
                    for k in ("passer", "null", "classic", "passer_alt")},
        "H1_p": round(h1p, 5), "H1_pass": h1p < 0.05,
        "H1b_p": round(h1bp, 5), "H1b_pass": h1bp < 0.05,
        "H2_rho": round(rho, 3), "H2_n": len(nn), "H2_pass": rho >= 0.30,
    }
    summary["decision"] = ("H1 pass: slope distribution AND simulated traverse outcomes match"
                           if summary["H1_pass"] else
                           "H1 fail: L1 TRANSFERS narrowed to 'slope distribution similar'")
    (DERIVED / "route_validity.json").write_text(json.dumps(summary, indent=2))
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
