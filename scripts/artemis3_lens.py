"""A3: the Artemis III candidate landing regions as targets of the terrain lens
(pre-registered, config/prereg_artemis3.yaml).

Only the five regions with a NASA PGDA Product 78 DEM under the same name are run; NASA publishes no
numeric centres for the nine regions, so none is guessed. Per region: reference = medoid 4 km window
(slope family), neighbours and thresholds by the V2 rule, Earth = 1,000 random bare-land cells and
the 54 classic-site footprints of route_validity.parquet (GLO-30).

Download the DEMs once (5 m surface and NASA slope raster):
  https://pgda.gsfc.nasa.gov/data/LOLA_5mpp/<SITE>/<SITE>_final_adj_5mpp_{surf,slp}.tif
  with <SITE> in Haworth, Site23, Site06, DM2, Site20, into data/raw/moon/pgda78/.

Outputs: data/derived/artemis3_lens.json, artemis3_lens.parquet
Usage  : EE_PROJECT=<project> python scripts/artemis3_lens.py [check|run]
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
from similitude.descriptors.astro import low_sun_windows
from similitude.descriptors.terrain import aggregate_to_baseline, slope_stats
from similitude.route import OUTCOMES, robust_scale, route_distance, route_outcomes

sys.path.insert(0, str(io.REPO_ROOT / "scripts"))
sys.path.insert(0, str(io.REPO_ROOT / "scripts" / "access"))
import route_validity as rv  # noqa: E402

D = io.REPO_ROOT / "data" / "derived"
PGDA = io.REPO_ROOT / "data" / "raw" / "moon" / "pgda78"
REGIONS = {"haworth": ("Haworth", "Haworth"),
           "malapert_massif": ("Site23", "Malapert Massif"),
           "nobile_rim_1": ("Site06", "Nobile Rim 1"),
           "nobile_rim_2": ("DM2", "Nobile Rim 2"),
           "mons_mouton_plateau": ("Site20", "Mons Mouton Plateau")}
NOT_RUN = {"mons_mouton": "no separate PGDA 78 DEM",
           "de_gerlache_rim_2": "two PGDA 78 DEMs named 'de Gerlache rim'; Rim 2 not identified",
           "peak_near_cabeus_b": "no PGDA 78 DEM", "slater_plain": "no PGDA 78 DEM"}
SLOPE = ("slope_p50", "slope_p90", "frac_gt8", "frac_gt15", "frac_gt20")
CLOSED = ("China", "Aksai Chin", "Russia")
PX, HALF, STEP = 5.0, 400, 200          # 5 m pixels, 4 km window, 1 km grid (as V2)
MIN_SEP_M = 4000.0
SELECTIVE_MAX = 0.10


def load(code: str) -> tuple[np.ndarray, object, CRS]:
    with rasterio.open(PGDA / f"{code}_final_adj_5mpp_surf.tif") as ds:
        z = ds.read(1).astype(np.float64)
        if ds.nodata is not None:
            z[z == ds.nodata] = np.nan
        return z, ds.transform, CRS.from_wkt(ds.crs.to_wkt())


def grid(z: np.ndarray) -> list[tuple[int, int, np.ndarray]]:
    out = []
    for r in range(HALF, z.shape[0] - HALF + 1, STEP):
        for c in range(HALF, z.shape[1] - HALF + 1, STEP):
            w = z[r - HALF:r + HALF, c - HALF:c + HALF]
            if np.isnan(w).mean() > 0.05:
                continue
            out.append((r, c, aggregate_to_baseline(w, PX, rv.RES)))
    return out


def _routes(w: np.ndarray) -> list[float]:
    o = route_outcomes(w, rv.RES)
    return [float(o[k]) for k in OUTCOMES]


def routes(ws: list[np.ndarray]) -> np.ndarray:
    from concurrent.futures import ProcessPoolExecutor
    with ProcessPoolExecutor(max_workers=14) as ex:
        return np.array(list(ex.map(_routes, ws, chunksize=4)))


def slope_vec(dem30: np.ndarray) -> list[float]:
    s = slope_stats(dem30, rv.RES)
    return [float(s[k]) for k in SLOPE]


def nasa_check(code: str, z: np.ndarray) -> dict:
    with rasterio.open(PGDA / f"{code}_final_adj_5mpp_slp.tif") as ds:
        slp = ds.read(1).astype(np.float64)
    r, c = z.shape[0] // 2, z.shape[1] // 2
    d, s = z[r - HALF:r + HALF, c - HALF:c + HALF], slp[r - HALF:r + HALF, c - HALF:c + HALF]
    ours = slope_stats(d, PX)
    return {"slope_p50_ours_5m": round(float(ours["slope_p50"]), 4),
            "slope_p50_nasa": round(float(np.nanmedian(s)), 4),
            "abs_diff_p50": round(abs(float(ours["slope_p50"]) - float(np.nanmedian(s))), 4)}


def lens(z: np.ndarray) -> dict:
    """Medoid reference, V2-rule neighbours and thresholds on a 5 m DEM (prereg A3 / B)."""
    win = grid(z)
    S = np.array([slope_vec(w) for _, _, w in win])
    sc_all = robust_scale(S)
    tot = np.array([route_distance(S, S[i], sc_all).sum() for i in range(len(S))])
    m = int(np.argmin(tot))
    mr, mc, mdem = win[m]
    nb = [(r, c, w) for r, c, w in win if np.hypot(r - mr, c - mc) * PX >= MIN_SEP_M]
    ref = {**dict(zip(SLOPE, S[m], strict=True)), **route_outcomes(mdem, rv.RES)}
    ns = np.array([slope_vec(w) for _, _, w in nb])
    no = routes([w for _, _, w in nb])
    fam = {"slope": (ns, [ref[k] for k in SLOPE]), "route": (no, [ref[k] for k in OUTCOMES])}
    scale = {f: robust_scale(x) for f, (x, _) in fam.items()}
    tau = {f: float(np.median(route_distance(x, v, scale[f]))) for f, (x, v) in fam.items()}
    return {"n_windows": len(win), "n_neighbours": len(nb), "rc": (mr, mc), "ref": ref,
            "vec": {f: v for f, (_, v) in fam.items()}, "scale": scale, "tau": tau}


def lunar(code: str) -> dict:
    z, tr, crs = load(code)
    L = lens(z)
    mr, mc = L["rc"]
    ref = L["ref"]
    x, y = tr.c + mc * tr.a, tr.f + mr * tr.e
    lon, lat = Transformer.from_crs(crs, crs.geodetic_crs, always_xy=True).transform(x, y)
    return {"code": code, "n_windows": L["n_windows"], "n_neighbours": L["n_neighbours"],
            "reference": {"lat": round(float(lat), 4), "lon": round(float(lon), 4),
                          **{k: round(float(v), 4) for k, v in ref.items()}},
            "vec": L["vec"], "scale": L["scale"], "tau": L["tau"],
            "nasa_check": nasa_check(code, z)}


def check_site01() -> float:
    """Sanity check of the prereg: Site01, centre reference, route family -> V2 tau."""
    z, _, _ = load("Site01")
    r0, c0 = z.shape[0] // 2, z.shape[1] // 2
    ref = route_outcomes(aggregate_to_baseline(z[r0 - HALF:r0 + HALF, c0 - HALF:c0 + HALF], PX,
                                               rv.RES), rv.RES)
    nb = [w for r, c, w in grid(z) if np.hypot(r - r0, c - c0) * PX >= MIN_SEP_M]
    no = routes(nb)
    v = [ref[k] for k in OUTCOMES]
    return float(np.median(route_distance(no, v, robust_scale(no))))


def earth() -> pd.DataFrame:
    cache = D / "artemis3_earth_slope.parquet"
    v = pd.read_parquet(D / "route_validity.parquet")
    e = v[v.group.isin(["null", "classic"])][["cell_id", "group", *OUTCOMES]].copy()
    g = pd.read_csv(D / "route_groups.csv").drop_duplicates("cell_id").set_index("cell_id")
    e["lat"], e["lon"] = e.cell_id.map(g.lat), e.cell_id.map(g.lon)
    e["site"] = e.cell_id.map(g.site)
    if cache.exists():
        sl = pd.read_parquet(cache)
    else:
        rows = []
        for r in e.drop_duplicates("cell_id").itertuples():
            try:
                rows.append({"cell_id": r.cell_id,
                             **dict(zip(SLOPE, slope_vec(rv.earth_footprint(r.lat, r.lon)),
                                        strict=True))})
            except Exception:
                rows.append({"cell_id": r.cell_id, **{k: np.nan for k in SLOPE}})
        sl = pd.DataFrame(rows)
        sl.to_parquet(cache, index=False)
    return e.merge(sl, on="cell_id", how="left")


def ci(k: int, n: int) -> list[float]:
    c = stats.binomtest(k, n).proportion_ci(confidence_level=0.95, method="exact")
    return [round(float(c.low), 4), round(float(c.high), 4)]


def run() -> None:
    import access_screen as acs
    tau01 = check_site01()
    v2tau = json.loads((D / "route_v2.json").read_text())["tau"]
    print(f"sanity: Site01 route tau {tau01:.4f} vs V2 {v2tau}")
    if abs(tau01 - v2tau) > 1e-3:
        raise SystemExit("sanity check failed: generic window code does not reproduce V2")
    e = earth()
    country: dict[str, str | None] = {}
    rows, out = [], {}
    for rid, (code, name) in REGIONS.items():
        L = lunar(code)
        print(rid, L["n_windows"], L["n_neighbours"], L["tau"], L["nasa_check"])
        x = e.copy()
        x["region"] = rid
        for f, ks in (("slope", list(SLOPE)), ("route", list(OUTCOMES))):
            ok = x[ks].notna().all(axis=1)
            x[f"D_{f}"] = np.where(ok, route_distance(x[ks].fillna(0).to_numpy(), L["vec"][f],
                                                      L["scale"][f]), np.nan)
        x = x.dropna(subset=["D_slope", "D_route"])
        x["match"] = (x.D_slope <= L["tau"]["slope"]) & (x.D_route <= L["tau"]["route"])
        nu = x[x.group.eq("null")]
        cl = x[x.group.eq("classic")]
        hits = nu[nu.match]
        new = hits[~hits.cell_id.isin(country)]
        if len(new):
            country.update(dict(zip(new.cell_id, acs.countries(new).to_numpy(), strict=True)))
        x["country"] = x.cell_id.map(country)
        rows.append(x)
        k_n, n_n, k_c, n_c = int(nu.match.sum()), len(nu), int(cl.match.sum()), len(cl)
        p = rv.fisher(k_c, n_c, k_n, n_n)
        op = x[x.group.eq("null") & x.match & x.country.notna() & ~x.country.isin(CLOSED)]
        op = op.sort_values("D_route")
        out[rid] = {
            "name": name, "pgda": code, "n_windows": L["n_windows"],
            "n_neighbours": L["n_neighbours"], "reference": L["reference"],
            "tau": {f: round(t, 4) for f, t in L["tau"].items()}, "nasa_check": L["nasa_check"],
            "null": [k_n, n_n], "null_share": round(k_n / n_n, 4), "null_ci": ci(k_n, n_n),
            "classic": [k_c, n_c], "classic_p": round(p, 5),
            "classic_p_bonferroni": round(min(1.0, p * len(REGIONS)), 5),
            "classic_per_site": {s: [int(t.match.sum()), len(t)]
                                 for s, t in cl.groupby("site")},
            "selective": k_n / n_n <= SELECTIVE_MAX, "earth_site_available": len(op) > 0,
            "n_open_matches": len(op),
            "open_matches": [{"cell_id": r.cell_id, "country": r.country,
                              "lat": round(r.lat, 4), "lon": round(r.lon, 4),
                              "D_slope": round(r.D_slope, 3), "D_route": round(r.D_route, 3),
                              "frac_gt8": round(r.frac_gt8, 3), "frac_gt20": round(r.frac_gt20, 3),
                              "low_sun_window_days":
                                  int(low_sun_windows(float(r.lat))["window_days"])}
                             for r in op.itertuples()]}
    pd.concat(rows, ignore_index=True).to_parquet(D / "artemis3_lens.parquet", index=False)
    res = {"prereg": "config/prereg_artemis3.yaml (commit 1e18662)",
           "sanity_site01_route_tau": round(tau01, 4), "v2_tau": v2tau,
           "regions": out, "not_run": NOT_RUN}
    (D / "artemis3_lens.json").write_text(json.dumps(res, indent=2, default=float))
    print(json.dumps({k: {kk: vv for kk, vv in r.items() if kk != "open_matches"}
                      for k, r in out.items()}, indent=1, default=float))


if __name__ == "__main__":
    if (sys.argv[1] if len(sys.argv) > 1 else "run") == "check":
        print(check_site01())
    else:
        run()
