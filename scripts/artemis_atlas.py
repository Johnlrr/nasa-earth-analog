"""Artemis atlas (exploratory, Deviations 36): the V1 traverse test and the low-Sun calendar for
the open-country leads of every PGDA 78 south-pole region.

Same planner, outcomes, distance and threshold rule as the pre-registered V1 (config/
prereg_route_v1.yaml), applied per region: the region's reference footprint (published, or the
medoid used by scripts/l1_regions.py) against its own lunar neighbours. Connecting Ridge is the
registered test and is read from route_validity.parquet, not recomputed. Leads are those of
scripts/access/access_screen.py (robust on GLO-30); second-DEM chips come from the cross-DEM cache.

Outputs: data/derived/artemis_atlas.parquet, data/derived/artemis_atlas.json; adds route and
window fields to the leads of the other regions in web/data/access.json.
Usage  : python scripts/artemis_atlas.py   (after route_validity.py and build_lighting_windows.py)
"""
from __future__ import annotations

import json
import sys

import numpy as np
import pandas as pd
import rasterio
from pyproj import CRS, Transformer

from similitude import io
from similitude.descriptors.astro import low_sun_windows
from similitude.descriptors.terrain import aggregate_to_baseline
from similitude.route import OUTCOMES, robust_scale, route_distance, route_outcomes

sys.path.insert(0, str(io.REPO_ROOT / "scripts"))
import cross_dem as cd  # noqa: E402
import l1_regions as lr  # noqa: E402
import route_validity as rv  # noqa: E402

D = io.REPO_ROOT / "data" / "derived"
PGDA = io.REPO_ROOT / "data" / "raw" / "moon" / "pgda78"
SITE_OF = {"connecting_ridge": "Site01", "shackleton_rim": "Site04", "nobile_rim_1": "Site06",
           "peak_near_shackleton": "Site07", "de_gerlache_rim": "Site11",
           "malapert_massif": "Site23"}
CLOSED = {"China", "Russia"}


def lunar_windows(target: str) -> tuple[str, list[tuple[str, np.ndarray]]]:
    ref_id = lr.context()["refs"][target]
    t = pd.read_parquet(D / "targets_L1.parquet")
    t = t[t["target_id"].eq(target)]
    with rasterio.open(PGDA / f"{SITE_OF[target]}_final_adj_5mpp_surf.tif") as ds:
        z = ds.read(1).astype(np.float64)
        if ds.nodata is not None:
            z[z == ds.nodata] = np.nan
        tr, crs = ds.transform, CRS.from_wkt(ds.crs.to_wkt())
    half = int(round(rv.FOOT_M / 2 / abs(tr.a)))
    to_xy = Transformer.from_crs(crs.geodetic_crs, crs, always_xy=True)
    xy = {}
    out = []
    for r in t.itertuples():
        x, y = to_xy.transform(r.lon, r.lat)
        xy[r.footprint_id] = (x, y)
    rx, ry = xy[ref_id]
    for r in t.itertuples():
        x, y = xy[r.footprint_id]
        if r.footprint_id != ref_id and np.hypot(x - rx, y - ry) < rv.SAME_AS_REF_M:
            continue
        col, row = int(round((x - tr.c) / tr.a)), int(round((y - tr.f) / tr.e))
        w = z[row - half:row + half, col - half:col + half]
        if w.shape == (2 * half, 2 * half):
            out.append((r.footprint_id, aggregate_to_baseline(w, 5.0, rv.RES)))
    return ref_id, out


def main() -> None:
    acc = pd.read_parquet(D / "access_leads.parquet")
    acc = acc[acc["robust"].astype(bool)]
    rows, regions = [], []
    for target in SITE_OF:
        leads = acc[acc["target_id"].eq(target)]
        reg = {"target_id": target, "n_leads": len(leads)}
        if target == "connecting_ridge":
            v = pd.read_parquet(D / "route_validity.parquet")
            lw = pd.read_parquet(D / "lighting_windows.parquet").set_index("cell_id")
            for r in leads.itertuples():
                g = v[(v.cell_id == r.cell_id) & v.group.eq("passer")]
                a = v[(v.cell_id == r.cell_id) & v.group.eq("passer_alt")]
                rows.append({"target_id": target, "cell_id": r.cell_id, "country": r.country,
                             "lat": r.lat, "lon": r.lon,
                             "in_exclusion_buffer": bool(r.in_exclusion_buffer),
                             "slope_two_dems": bool(r.robust_alt),
                             "snow_ice_frac": float(r.snow_ice_frac),
                             "D_route": float(g.D_route.iloc[0]),
                             "routes": bool(g.reproduces.iloc[0]),
                             "routes_alt": bool(a.reproduces.iloc[0]) if len(a) else None,
                             "window_days": int(lw.loc[r.cell_id, "window_days"])})
            regions.append(reg)
            continue
        ref_id, moon = lunar_windows(target)
        o_ref = route_outcomes(dict(moon)[ref_id], rv.RES)
        nat = [(fid, route_outcomes(d, rv.RES)) for fid, d in moon if fid != ref_id]
        on = np.array([[o[k] for k in OUTCOMES] for _, o in nat])
        scale = robust_scale(on)
        ref_v = [o_ref[k] for k in OUTCOMES]
        tau = float(np.median(route_distance(on, ref_v, scale)))
        reg.update({"reference": ref_id, "n_native": len(nat), "tau": round(tau, 4),
                    "ref_reach_6": round(o_ref["reach_6"], 3)})
        for r in leads.itertuples():
            o = route_outcomes(rv.earth_footprint(r.lat, r.lon), rv.RES)
            d = float(route_distance([o[k] for k in OUTCOMES], ref_v, scale)[0])
            try:
                alt = cd.alt_chip(r.lat, r.lon, cd.source_for(r.lat))
                oa = route_outcomes(rv.centre(alt, int(rv.FOOT_M // rv.RES)), rv.RES)
                da = float(route_distance([oa[k] for k in OUTCOMES], ref_v, scale)[0])
                ra = bool(da <= tau)
            except Exception:
                ra = None
            rows.append({"target_id": target, "cell_id": r.cell_id, "country": r.country,
                         "lat": r.lat, "lon": r.lon,
                         "in_exclusion_buffer": bool(r.in_exclusion_buffer),
                         "slope_two_dems": bool(r.robust_alt),
                         "snow_ice_frac": float(r.snow_ice_frac), "D_route": d,
                         "routes": bool(d <= tau), "routes_alt": ra,
                         "window_days": int(low_sun_windows(float(r.lat))["window_days"])})
        regions.append(reg)
        print(target, reg)
    out = pd.DataFrame(rows)
    out["open"] = ~out["country"].isin(CLOSED)
    out["both"] = (out["slope_two_dems"] & out["routes"] & out["routes_alt"].fillna(False)
                   & out["open"] & ~out["in_exclusion_buffer"] & (out["snow_ice_frac"] <= 0.2))
    out.to_parquet(D / "artemis_atlas.parquet", index=False)
    for reg in regions:
        s = out[out.target_id.eq(reg["target_id"])]
        reg["n_slope_two_dems"] = int(s.slope_two_dems.sum())
        reg["n_routes_two_dems"] = int((s.routes & s.routes_alt.fillna(False)).sum())
        reg["n_all_tests"] = int(s.both.sum())
        reg["n_all_tests_window"] = int((s.both & (s.window_days > 0)).sum())
        reg["countries_all_tests"] = sorted(s[s.both].country.unique().tolist())
    summary = {"status": "exploratory (Deviations 36); V1 rule per region", "regions": regions,
               "regions_with_lead_all_tests": sum(r["n_all_tests"] > 0 for r in regions),
               "n_regions": len(regions)}
    (D / "artemis_atlas.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")
    web = io.REPO_ROOT / "web" / "data" / "access.json"
    aw = json.loads(web.read_text(encoding="utf-8"))
    by = out.set_index(["target_id", "cell_id"])
    for reg in aw["regions"]:
        if reg["id"] == "connecting_ridge":
            continue
        for lead in reg["leads"]:
            k = (reg["id"], lead["cell_id"])
            if k in by.index:
                r = by.loc[k]
                lead["route_reproduces"] = bool(r.routes)
                lead["route_reproduces_second_dem"] = (None if pd.isna(r.routes_alt)
                                                       else bool(r.routes_alt))
                lead["route_D"] = round(float(r.D_route), 3)
                lead["window_days"] = int(r.window_days)
                lead["window_from"] = None
                lead["window_to"] = None
    web.write_text(json.dumps(aw, indent=1, ensure_ascii=False), encoding="utf-8")
    print(json.dumps(summary, indent=1))


if __name__ == "__main__":
    main()
