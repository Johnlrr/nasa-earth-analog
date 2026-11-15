"""V2 lunar threshold and M1 Mars lens (pre-registered, config/prereg_v2_mars.yaml, commit 67920dd).

V2: the V1 test with scale and tau estimated from 124 non-overlapping 4 km windows of Site01
    instead of 8. Earth outcomes are read from route_validity.parquet (not recomputed).
M1: Jezero delta front (CTX DTM) as a target for the same slope and planner descriptors; null and
    passer outcomes from route_validity.parquet, classic Mars sites computed here.

Mars DTM: USGS Mars 2020 TRN CTX DTM (Jezero), download once:
  curl -L -o data/raw/mars/dtm/JEZ_ctx_B_soc_008_DTM_20m.tif https://planetarymaps.usgs.gov/mosaic/\
mars2020_trn/CTX/JEZ_ctx_B_soc_008_DTM_MOLAtopography_DeltaGeoid_20m_Eqc_latTs0_lon0.tif
Jezero is a robotic landing site, not a candidate for a crewed base; the lens shows that the
method transfers to Mars, not where a Mars base should go.

Outputs: data/derived/route_v2.json, route_v2.parquet, mars_m1.json, mars_m1.parquet
Usage  : EE_PROJECT=<project> python scripts/v2_mars.py
"""
from __future__ import annotations

import json
import sys

import numpy as np
import pandas as pd
import rasterio
from scipy import stats

from similitude import io
from similitude.descriptors.terrain import aggregate_to_baseline, slope_stats
from similitude.route import OUTCOMES, robust_scale, route_distance, route_outcomes

sys.path.insert(0, str(io.REPO_ROOT / "scripts"))
sys.path.insert(0, str(io.REPO_ROOT / "scripts" / "access"))
import route_validity as rv  # noqa: E402

D = io.REPO_ROOT / "data" / "derived"
MARS = io.REPO_ROOT / "data" / "raw" / "mars" / "dtm" / "JEZ_ctx_B_soc_008_DTM_20m.tif"
R_MARS = 3396190.0
TARGET = (18.4532, 77.4022)
SLOPE = ("slope_p50", "slope_p90", "frac_gt8", "frac_gt15", "frac_gt20")
MARS_SITES = {"MDRS Hanksville, Utah": (38.4063, -110.7918),
              "Atacama, Yungay": (-24.0833, -70.0167),
              "McMurdo Wright Valley": (-77.52, 161.85),
              "HI-SEAS, Mauna Loa": (19.6022, -155.4858)}
HAUGHTON = "Haughton impact structure, Devon Island"
CLOSED = ("China", "Aksai Chin", "Russia")


# ------------------------------------------------------------------------------------------ V2
def moon_grid() -> tuple[dict, np.ndarray]:
    with rasterio.open(rv.MOON) as ds:
        z = ds.read(1).astype(np.float64)
        if ds.nodata is not None:
            z[z == ds.nodata] = np.nan
    half, step = 400, 200
    c = z.shape[0] // 2, z.shape[1] // 2
    ref = route_outcomes(aggregate_to_baseline(z[c[0] - half:c[0] + half,
                                                 c[1] - half:c[1] + half], 5.0, rv.RES), rv.RES)
    rows = []
    for r in range(half, z.shape[0] - half + 1, step):
        for cc in range(half, z.shape[1] - half + 1, step):
            if np.hypot(r - c[0], cc - c[1]) * 5.0 < 4000.0:
                continue
            w = z[r - half:r + half, cc - half:cc + half]
            if np.isnan(w).mean() > 0.05:
                continue
            rows.append(route_outcomes(aggregate_to_baseline(w, 5.0, rv.RES), rv.RES))
    return ref, np.array([[o[k] for k in OUTCOMES] for o in rows])


def v2() -> None:
    ref, on = moon_grid()
    rv_ = [ref[k] for k in OUTCOMES]
    scale = robust_scale(on)
    tau = float(np.median(route_distance(on, rv_, scale)))
    v = pd.read_parquet(D / "route_validity.parquet")
    earth = v[v.group.isin(["passer", "passer_alt", "null", "classic"])].copy()
    ok = earth[list(OUTCOMES)].notna().all(axis=1)
    earth["D_route_v2"] = np.where(ok, route_distance(earth[list(OUTCOMES)].fillna(0).to_numpy(),
                                                      rv_, scale), np.nan)
    earth["reproduces_v2"] = earth["D_route_v2"] <= tau
    earth[["cell_id", "group", "dem", "D_route", "reproduces", "D_route_v2",
           "reproduces_v2"]].to_parquet(D / "route_v2.parquet", index=False)

    def share(grp):
        s = earth[earth.group.eq(grp) & earth.D_route_v2.notna()]
        return int(s.reproduces_v2.sum()), len(s)

    pa, nu, cl, alt = share("passer"), share("null"), share("classic"), share("passer_alt")
    nulls = earth[earth.group.eq("null") & earth.D_route_v2.notna()].copy()
    nulls["d_l1"] = rv.l1_distance(nulls)
    nn = nulls.dropna(subset=["d_l1"])
    rho = float(stats.spearmanr(nn.d_l1, nn.D_route_v2)[0])
    h1p, h1bp = rv.fisher(*pa, *nu), rv.fisher(*pa, *cl)
    pas = earth[earth.group.eq("passer")].set_index("cell_id")
    pal = earth[earth.group.eq("passer_alt")].set_index("cell_id")
    both = [c for c in pas.index if pas.loc[c, "reproduces_v2"]
            and c in pal.index and bool(pal.loc[c, "reproduces_v2"])]
    v1 = json.loads((D / "route_validity.json").read_text())
    res = {"prereg": "config/prereg_v2_mars.yaml (commit 67920dd)", "n_moon_native": len(on),
           "n_moon_native_v1": v1["n_moon_native"], "tau": round(tau, 4), "tau_v1": v1["tau"],
           "scale": dict(zip(OUTCOMES, np.round(scale, 5).tolist(), strict=True)),
           "accept_halfwidth": dict(zip(OUTCOMES, np.round(scale * tau, 4).tolist(), strict=True)),
           "passer": list(pa), "null": list(nu), "classic": list(cl),
           "passer_second_dem": list(alt),
           "passers_both_dems": both,
           "H1_p": round(h1p, 5), "H1_pass": h1p < 0.05, "H1b_p": round(h1bp, 5),
           "H1b_pass": h1bp < 0.05, "H2_rho": round(rho, 3), "H2_n": len(nn),
           "H2_pass": rho >= 0.30,
           "v1": {k: v1[k] for k in ("passer", "null", "classic", "H1_p", "H1b_p", "H2_rho")}}
    (D / "route_v2.json").write_text(json.dumps(res, indent=2))
    print(json.dumps(res, indent=1))


# ------------------------------------------------------------------------------------------ M1
def mars_windows() -> tuple[np.ndarray, list[np.ndarray]]:
    with rasterio.open(MARS) as ds:
        z = ds.read(1).astype(np.float64)
        tr = ds.transform
    z[z < -1e30] = np.nan
    x0, y0 = np.radians(TARGET[1]) * R_MARS, np.radians(TARGET[0]) * R_MARS
    h = int(round(2000 / abs(tr.a)))
    col, row = int(round((x0 - tr.c) / tr.a)), int(round((y0 - tr.f) / tr.e))
    target = aggregate_to_baseline(z[row - h:row + h, col - h:col + h], abs(tr.a), rv.RES)
    nb = []
    for r in range(h, z.shape[0] - h + 1, h):
        for c in range(h, z.shape[1] - h + 1, h):
            cx, cy = tr.c + c * tr.a, tr.f + r * tr.e
            if np.hypot(cx - x0, cy - y0) < 4000:
                continue
            w = z[r - h:r + h, c - h:c + h]
            if w.shape != (2 * h, 2 * h) or np.isnan(w).mean() > 0.05:
                continue
            nb.append(aggregate_to_baseline(w, abs(tr.a), rv.RES))
    return target, nb


def describe(dem: np.ndarray) -> dict:
    return {**{k: slope_stats(dem, rv.RES)[k] for k in SLOPE}, **route_outcomes(dem, rv.RES)}


def mars_classic() -> pd.DataFrame:
    st = pd.read_parquet(D / "site_stability.parquet")
    hb = st[st.group.eq("Classic analog") & st.dem.eq("GLO-30") & st.site.eq(HAUGHTON)]
    rows = [(r.cell_id, HAUGHTON, r.lat, r.lon) for r in hb.itertuples()]
    for name, (la, lo) in MARS_SITES.items():
        dlat = 4000 / 111_320
        dlon = dlat / np.cos(np.radians(la))
        for dy in (-1, 0, 1):
            for dx in (-1, 0, 1):
                rows.append((f"MARS_{name.split()[0]}:{dx:+d}{dy:+d}", name,
                             la + dy * dlat, lo + dx * dlon))
    return pd.DataFrame(rows, columns=["cell_id", "site", "lat", "lon"])


def m1() -> None:
    target, nb = mars_windows()
    t = describe(target)
    nbd = pd.DataFrame([describe(w) for w in nb])
    fam = {"slope": list(SLOPE), "route": list(OUTCOMES)}
    sc = {f: robust_scale(nbd[k].to_numpy()) for f, k in fam.items()}
    tv = {f: [t[k] for k in ks] for f, ks in fam.items()}
    tau = {f: float(np.median(route_distance(nbd[ks].to_numpy(), tv[f], sc[f])))
           for f, ks in fam.items()}

    v = pd.read_parquet(D / "route_validity.parquet")
    earth = v[v.group.isin(["null", "passer"])][["cell_id", "group", *OUTCOMES]].copy()
    g = pd.read_csv(D / "route_groups.csv").drop_duplicates("cell_id").set_index("cell_id")
    earth["lat"] = earth.cell_id.map(g.lat)
    earth["lon"] = earth.cell_id.map(g.lon)
    sl = []
    for r in earth.itertuples():
        try:
            s = slope_stats(rv.earth_footprint(r.lat, r.lon), rv.RES)
            sl.append({k: s[k] for k in SLOPE})
        except Exception:
            sl.append({k: np.nan for k in SLOPE})
    earth = pd.concat([earth.reset_index(drop=True), pd.DataFrame(sl)], axis=1)
    cls = []
    for r in mars_classic().itertuples():
        try:
            dem = rv.earth_footprint(r.lat, r.lon)
            o = describe(dem) if np.isnan(dem).mean() <= 0.05 else {}
        except Exception:
            o = {}
        cls.append({"cell_id": r.cell_id, "group": "classic_mars", "site": r.site,
                    "lat": r.lat, "lon": r.lon, **o})
    earth = pd.concat([earth, pd.DataFrame(cls)], ignore_index=True)
    for f, ks in fam.items():
        ok = earth[ks].notna().all(axis=1)
        earth[f"D_{f}"] = np.where(ok, route_distance(earth[ks].fillna(0).to_numpy(), tv[f],
                                                      sc[f]), np.nan)
    earth["match"] = (earth.D_slope <= tau["slope"]) & (earth.D_route <= tau["route"])
    ev = earth.dropna(subset=["D_slope", "D_route"])

    def share(grp):
        s = ev[ev.group.eq(grp)]
        return int(s.match.sum()), len(s)

    nu, cm, pa = share("null"), share("classic_mars"), share("passer")
    p = rv.fisher(*cm, *nu)
    hits = ev[ev.group.eq("null") & ev.match].copy()
    if len(hits):
        import access_screen as acs
        hits["country"] = acs.countries(hits).to_numpy()
    else:
        hits["country"] = []
    earth = earth.merge(hits[["cell_id", "country"]], on="cell_id", how="left")
    earth.to_parquet(D / "mars_m1.parquet", index=False)
    per_site = {s: [int(x.match.sum()), len(x)] for s, x in ev[ev.group.eq("classic_mars")]
                .groupby("site")}
    openm = hits[~hits.country.isin(CLOSED)].sort_values("D_route")
    res = {"prereg": "config/prereg_v2_mars.yaml (commit 67920dd)",
           "target": {"name": "Jezero western delta front", "lat": TARGET[0], "lon": TARGET[1],
                      **{k: round(float(t[k]), 4) for k in (*SLOPE, *OUTCOMES)}},
           "n_mars_neighbours": len(nb), "tau": {f: round(x, 4) for f, x in tau.items()},
           "null": list(nu), "classic_mars": list(cm), "moon_passers": list(pa),
           "per_site": per_site, "HM1_p": round(p, 5), "HM1_pass": p < 0.05,
           "null_route_only": int((ev.group.eq("null") & (ev.D_route <= tau["route"])).sum()),
           "null_slope_only": int((ev.group.eq("null") & (ev.D_slope <= tau["slope"])).sum()),
           "n_open_matches": len(openm),
           "countries": hits.country.value_counts().to_dict(),
           "open_matches": [{"cell_id": r.cell_id, "country": r.country,
                             "lat": round(r.lat, 4), "lon": round(r.lon, 4),
                             "D_slope": round(r.D_slope, 3), "D_route": round(r.D_route, 3),
                             "frac_gt8": round(r.frac_gt8, 3)} for r in openm.itertuples()]}
    (D / "mars_m1.json").write_text(json.dumps(res, indent=2, default=float))
    print(json.dumps(res, indent=1, default=float))


if __name__ == "__main__":
    which = sys.argv[1] if len(sys.argv) > 1 else "all"
    if which in ("all", "v2"):
        v2()
    if which in ("all", "m1"):
        m1()
