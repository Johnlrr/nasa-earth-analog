"""R1 (pre-registered, config/prereg_rover_r1.yaml): does the 30 m planner's detour predict where
Perseverance actually detoured in Jezero crater?

Inputs : data/external/m20/M20_traverse.json (NASA/JPL MMGIS, public), the Jezero CTX DTM
         (see scripts/v2_mars.py for the download command).
Outputs: data/derived/rover_r1_legs.parquet, rover_r1_drives.parquet, rover_r1.json
Usage  : python scripts/rover_r1.py
"""
from __future__ import annotations

import json

import numpy as np
import pandas as pd
import rasterio
from scipy import ndimage, stats
from scipy.sparse.csgraph import dijkstra

from similitude import io
from similitude.descriptors.terrain import aggregate_to_baseline, slope_stats
from similitude.route import _edges, _graph

D = io.REPO_ROOT / "data" / "derived"
TRACK = io.REPO_ROOT / "data" / "external" / "m20" / "M20_traverse.json"
WAYPTS = io.REPO_ROOT / "data" / "external" / "m20" / "M20_waypoints.json"
DTM = io.REPO_ROOT / "data" / "raw" / "mars" / "dtm" / "JEZ_ctx_B_soc_008_DTM_20m.tif"
R = 3396190.0
RES_IN, RES = 20.0, 30.0
MARGIN = 1000.0
NAN_MAX = 0.05


def gc(lon1, lat1, lon2, lat2):
    """Great-circle ground distance (m) on the Mars sphere; vectorised."""
    p1, p2 = np.radians(lat1), np.radians(lat2)
    dl, dp = np.radians(lon2 - lon1), p2 - p1
    a = np.sin(dp / 2) ** 2 + np.cos(p1) * np.cos(p2) * np.sin(dl / 2) ** 2
    return 2 * R * np.arcsin(np.sqrt(a))


class Dtm:
    def __init__(self) -> None:
        with rasterio.open(DTM) as ds:
            self.z = ds.read(1).astype(np.float64)
            self.tr = ds.transform
        self.z[self.z < -1e30] = np.nan

    def window(self, lon: np.ndarray, lat: np.ndarray, margin: float):
        """Square-cell 30 m DEM covering the points plus a ground margin.

        Returns (dem30, to_cell) where to_cell(lon, lat) gives (row, col) in dem30.
        """
        lat_c = float(np.mean([lat.min(), lat.max()]))
        cphi = np.cos(np.radians(lat_c))
        x = np.radians(lon) * R          # DTM x (equirectangular, standard parallel 0)
        y = np.radians(lat) * R
        x_w = x.min() - margin / cphi
        y_top = y.max() + margin
        w_m = (x.max() - x.min()) * cphi + 2 * margin   # ground metres
        h_m = (y.max() - y.min()) + 2 * margin
        nc, nr = int(np.ceil(w_m / RES_IN)) + 1, int(np.ceil(h_m / RES_IN)) + 1
        e = np.arange(nc) * RES_IN
        nd = np.arange(nr) * RES_IN
        ee, nn = np.meshgrid(e, nd)
        col = (x_w + ee / cphi - self.tr.c) / self.tr.a - 0.5
        row = (y_top - nn - self.tr.f) / self.tr.e - 0.5
        dem20 = ndimage.map_coordinates(self.z, [row, col], order=1, cval=np.nan)
        dem30 = aggregate_to_baseline(dem20, RES_IN, RES)

        def to_cell(lo, la):
            u = ((np.radians(lo) * R - x_w) * cphi) / RES_IN       # column in dem20
            v = (y_top - np.radians(la) * R) / RES_IN               # row in dem20
            ci = np.rint(u * (dem30.shape[1] - 1) / (nc - 1)).astype(int)
            ri = np.rint(v * (dem30.shape[0] - 1) / (nr - 1)).astype(int)
            return ri, ci

        return dem20, dem30, to_cell


def track() -> pd.DataFrame:
    feats = json.loads(TRACK.read_text(encoding="utf-8"))["features"]
    feats = sorted(feats, key=lambda f: f["properties"]["SCLK_START"])
    pts = []
    for f in feats:
        for c in f["geometry"]["coordinates"]:
            pts.append((c[0], c[1], f["properties"]["sol"]))
    t = pd.DataFrame(pts, columns=["lon", "lat", "sol"])
    keep = np.r_[True, (t.lon.diff().ne(0) | t.lat.diff().ne(0)).to_numpy()[1:]]
    return t[keep].reset_index(drop=True), feats


def legs(t: pd.DataFrame, leg_m: float) -> list[tuple[int, int]]:
    out, s = [], 0
    lon, lat = t.lon.to_numpy(), t.lat.to_numpy()
    for i in range(1, len(t)):
        if gc(lon[s], lat[s], lon[i], lat[i]) >= leg_m:
            out.append((s, i))
            s = i
    return out


def planner_detour(dtm: Dtm, lon, lat, limit: float) -> tuple[float, float]:
    _, dem, to_cell = dtm.window(lon, lat, MARGIN)
    nanf = float(np.isnan(dem).mean())
    if nanf > NAN_MAX:
        return np.nan, nanf
    r, c = to_cell(np.array([lon[0], lon[-1]]), np.array([lat[0], lat[-1]]))
    n, m = dem.shape
    a, b, d, g = _edges(dem, RES)
    gr = _graph(n * m, a, b, d, g, limit)
    src, dst = r[0] * m + c[0], r[1] * m + c[1]
    dist = dijkstra(gr, directed=False, indices=src)[dst]
    straight = gc(lon[0], lat[0], lon[-1], lat[-1])
    return (float(dist / straight) if np.isfinite(dist) else np.inf), nanf


def run_legs(dtm: Dtm, t: pd.DataFrame, leg_m: float, limit: float) -> pd.DataFrame:
    rows = []
    lon, lat = t.lon.to_numpy(), t.lat.to_numpy()
    for k, (s, e) in enumerate(legs(t, leg_m)):
        lo, la = lon[s:e + 1], lat[s:e + 1]
        path = float(gc(lo[:-1], la[:-1], lo[1:], la[1:]).sum())
        straight = float(gc(lo[0], la[0], lo[-1], la[-1]))
        pred, nanf = planner_detour(dtm, lo, la, limit)
        rows.append({"leg": k, "sol_start": int(t.sol[s]), "sol_end": int(t.sol[e]),
                     "lon0": lo[0], "lat0": la[0], "lon1": lo[-1], "lat1": la[-1],
                     "path_m": path, "straight_m": straight, "actual_detour": path / straight,
                     "predicted_detour": pred, "nan_frac": nanf})
    return pd.DataFrame(rows)


def spearman(x, y, alternative="greater"):
    x = np.where(np.isinf(x), 1e9, x)
    ok = np.isfinite(x) & np.isfinite(y)
    r = stats.spearmanr(x[ok], y[ok], alternative=alternative)
    return float(r.statistic), float(r.pvalue), int(ok.sum())


def slope_map(dem: np.ndarray, res: float) -> np.ndarray:
    dzdy, dzdx = np.gradient(dem, res)          # same formula as slope_stats
    return np.degrees(np.arctan(np.hypot(dzdx, dzdy)))


def r1b(dtm: Dtm) -> dict:
    """R1b (addendum): 30 m orbital slope at each waypoint vs the rover's measured tilt."""
    w = json.loads(WAYPTS.read_text(encoding="utf-8"))["features"]
    wp = pd.DataFrame([{"site": f["properties"]["site"], "lon": f["properties"]["lon"],
                        "lat": f["properties"]["lat"], "tilt": f["properties"].get("tilt")}
                       for f in w])
    n_all = len(wp)
    wp = wp[pd.to_numeric(wp.tilt, errors="coerce").ge(0)].copy()
    wp["tilt"] = wp.tilt.astype(float)
    lo, la = wp.lon.to_numpy(), wp.lat.to_numpy()
    dem20, dem30, to_cell = dtm.window(lo, la, MARGIN)
    ri, ci = to_cell(lo, la)
    wp["slope_30m"] = slope_map(dem30, RES)[ri, ci]
    lat_c = float(np.mean([la.min(), la.max()]))
    cphi = np.cos(np.radians(lat_c))
    x_w = (np.radians(lo) * R).min() - MARGIN / cphi
    y_top = (np.radians(la) * R).max() + MARGIN
    u = np.rint(((np.radians(lo) * R - x_w) * cphi) / RES_IN).astype(int)
    v = np.rint((y_top - np.radians(la) * R) / RES_IN).astype(int)
    wp["slope_20m"] = slope_map(dem20, RES_IN)[v, u]
    wp.to_parquet(D / "rover_r1b_waypoints.parquet", index=False)
    rho, p, n = spearman(wp.slope_30m.to_numpy(), wp.tilt.to_numpy())
    r20, p20, n20 = spearman(wp.slope_20m.to_numpy(), wp.tilt.to_numpy())
    site = wp.groupby("site")[["slope_30m", "tilt"]].median()
    rs, ps, ns = spearman(site.slope_30m.to_numpy(), site.tilt.to_numpy())
    return {"n_waypoints": n, "dropped": n_all - len(wp), "rho": round(rho, 3),
            "p_one_sided": round(p, 8), "pass": bool(rho >= 0.30 and p < 0.05),
            "tilt_median": round(float(wp.tilt.median()), 2),
            "slope_30m_median": round(float(wp.slope_30m.median()), 2),
            "sensitivity": {"slope_20m": {"rho": round(r20, 3), "p": round(p20, 8), "n": n20},
                            "per_site": {"rho": round(rs, 3), "p": round(ps, 8), "n": ns}}}


def main() -> None:
    dtm = Dtm()
    t, feats = track()
    primary = run_legs(dtm, t, 1000.0, 10.0)
    primary.to_parquet(D / "rover_r1_legs.parquet", index=False)
    rho, p, n = spearman(primary.predicted_detour.to_numpy(), primary.actual_detour.to_numpy())
    sens = {}
    for leg_m, lim in ((1000.0, 8.0), (1000.0, 6.0), (500.0, 10.0), (2000.0, 10.0)):
        s = run_legs(dtm, t, leg_m, lim)
        r_, p_, n_ = spearman(s.predicted_detour.to_numpy(), s.actual_detour.to_numpy())
        sens[f"leg{int(leg_m)}_limit{int(lim)}"] = {"rho": round(r_, 3), "p": round(p_, 5),
                                                    "n": n_,
                                                    "unreachable": int(np.isinf(
                                                        s.predicted_detour).sum())}
    # R2: drive rate vs frac_gt8 in a 1 km square around the drive midpoint
    drows = []
    for f in feats:
        pr = f["properties"]
        dt = (pr.get("SCLK_END") or 0) - (pr.get("SCLK_START") or 0)
        if pr.get("length", 0) < 20 or dt <= 0:
            continue
        c = np.array(f["geometry"]["coordinates"])[:, :2]
        seg = gc(c[:-1, 0], c[:-1, 1], c[1:, 0], c[1:, 1])
        cum = np.r_[0, np.cumsum(seg)]
        i = int(np.searchsorted(cum, cum[-1] / 2))
        i = min(max(i, 0), len(c) - 1)
        _, dem, _ = dtm.window(np.array([c[i, 0]]), np.array([c[i, 1]]), 500.0)
        if np.isnan(dem).mean() > NAN_MAX:
            continue
        drows.append({"sol": pr["sol"], "length_m": pr["length"], "duration_s": dt,
                      "rate_m_per_h": pr["length"] / dt * 3600,
                      "frac_gt8": slope_stats(dem, RES)["frac_gt8"]})
    dr = pd.DataFrame(drows)
    dr.to_parquet(D / "rover_r1_drives.parquet", index=False)
    r2, p2, n2 = spearman(dr.frac_gt8.to_numpy(), dr.rate_m_per_h.to_numpy(), alternative="less")
    res = {"prereg": "config/prereg_rover_r1.yaml (commit 8798764)",
           "track_last_sol": int(t.sol.max()), "track_vertices": len(t),
           "R1": {"n_legs": n, "unreachable": int(np.isinf(primary.predicted_detour).sum()),
                  "skipped_nodata": int(primary.predicted_detour.isna().sum()),
                  "rho": round(rho, 3), "p_one_sided": round(p, 6),
                  "pass": bool(rho >= 0.30 and p < 0.05),
                  "actual_detour_median": round(float(primary.actual_detour.median()), 3),
                  "predicted_detour_median": round(float(
                      primary.predicted_detour.replace(np.inf, np.nan).median()), 3)},
           "R1_sensitivity": sens,
           "R2": {"n_drives": n2, "rho": round(r2, 3), "p_one_sided": round(p2, 6),
                  "pass": bool(r2 < 0 and p2 < 0.05)}}
    res["R1b"] = r1b(dtm)
    res["prereg_R1b"] = "config/prereg_rover_r1.yaml addendum (commit dabc895)"
    (D / "rover_r1.json").write_text(json.dumps(res, indent=2))
    print(json.dumps(res, indent=1))


if __name__ == "__main__":
    main()
