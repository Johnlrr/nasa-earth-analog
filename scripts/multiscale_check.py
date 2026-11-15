"""Does the 30 m ridge match of the Baffin lead hold at rover scale? (exploratory, Deviations 34)

Rule, written and committed before the first run: at each scale s in {5, 10, 30} m, the lead
"holds at s" if its frac_gt8 and frac_gt20 both lie within [min, max] of the ridge and its lunar
neighbours at the same scale (PGDA 78 Site01 5 m DEM, aggregated). Route outcomes (same planner
as V1) are reported at 10 m and 30 m beside the ridge's, without a pass rule.

Earth side: ArcticDEM v4 2 m mosaic (PGC, via Earth Engine), averaged to 5 m, 4 km footprint
centred on the lead, local UTM. Only leads north of 60 N have ArcticDEM.

Outputs: data/derived/multiscale.json
Usage  : EE_PROJECT=<project> python scripts/multiscale_check.py
"""
from __future__ import annotations

import io as _io
import json
import os
import sys

import numpy as np
import pandas as pd
from pyproj import Transformer

from similitude import io
from similitude.descriptors.terrain import aggregate_to_baseline, slope_stats
from similitude.route import route_outcomes

sys.path.insert(0, str(io.REPO_ROOT / "scripts"))
import cross_dem as cd  # noqa: E402
import route_validity as rv  # noqa: E402

DERIVED = io.REPO_ROOT / "data" / "derived"
CACHE = io.REPO_ROOT / "data" / "raw" / "earth" / "chips_hr"
LEADS = {"E10K_660_-632": "Baffin Island"}
FOOT_M = 4000.0
SCALES = (5.0, 10.0, 30.0)


def arcticdem_5m(lat: float, lon: float) -> np.ndarray:
    path = CACHE / f"ArcticDEMv4_5m_{lat:.4f}_{lon:.4f}.npy"
    if path.exists():
        return np.load(path)
    import ee

    ee.Initialize(project=os.environ["EE_PROJECT"])
    epsg = cd._utm_epsg(lat, lon)
    x, y = Transformer.from_crs(4326, epsg, always_xy=True).transform(lon, lat)
    n = int(round(FOOT_M / 5.0))
    img = (ee.Image("UMN/PGC/ArcticDEM/V4/2m_mosaic").select("elevation")
           .reduceResolution(ee.Reducer.mean(), bestEffort=True, maxPixels=64))
    raw = ee.data.computePixels({
        "expression": img.toFloat(), "fileFormat": "NPY",
        "grid": {"dimensions": {"width": n, "height": n}, "crsCode": f"EPSG:{epsg}",
                 "affineTransform": {"scaleX": 5.0, "shearX": 0, "translateX": x - FOOT_M / 2,
                                     "shearY": 0, "scaleY": -5.0, "translateY": y + FOOT_M / 2}}})
    dem = np.load(_io.BytesIO(raw))["elevation"].astype(np.float64)
    dem[~np.isfinite(dem) | (dem < -1000)] = np.nan
    CACHE.mkdir(parents=True, exist_ok=True)
    np.save(path, dem)
    return dem


def moon_5m() -> list[tuple[str, np.ndarray]]:
    """Ridge and its lunar neighbours as 4 km windows at 5 m (same windows as V1)."""
    import rasterio
    from pyproj import CRS

    with rasterio.open(rv.MOON) as ds:
        z = ds.read(1).astype(np.float64)
        if ds.nodata is not None:
            z[z == ds.nodata] = np.nan
        tr, crs = ds.transform, CRS.from_wkt(ds.crs.to_wkt())
    half = int(round(FOOT_M / 2 / abs(tr.a)))
    c = z.shape[0] // 2, z.shape[1] // 2
    out = [("connecting_ridge_ref", z[c[0] - half:c[0] + half, c[1] - half:c[1] + half])]
    t = pd.read_parquet(DERIVED / "targets_L1.parquet")
    pop = t[t["target_id"].eq(rv.TARGET) & ~t["is_reference"].astype(bool)]
    to_xy = Transformer.from_crs(crs.geodetic_crs, crs, always_xy=True)
    cx, cy = tr.c + c[1] * tr.a, tr.f + c[0] * tr.e
    for r in pop.itertuples():
        x, y = to_xy.transform(r.lon, r.lat)
        if np.hypot(x - cx, y - cy) < rv.SAME_AS_REF_M:
            continue
        col, row = int(round((x - tr.c) / tr.a)), int(round((y - tr.f) / tr.e))
        w = z[row - half:row + half, col - half:col + half]
        if w.shape == (2 * half, 2 * half):
            out.append((r.footprint_id, w))
    return out


def at(dem5: np.ndarray, s: float) -> np.ndarray:
    return dem5 if s == 5.0 else aggregate_to_baseline(dem5, 5.0, s)


def main() -> None:
    moon = moon_5m()
    acc = pd.read_parquet(DERIVED / "access_leads.parquet").drop_duplicates("cell_id")
    acc = acc.set_index("cell_id")
    res: dict = {"rule": __doc__.split("\n\n")[1].replace("\n", " "), "scales_m": SCALES,
                 "moon": {}, "leads": {}}
    for s in SCALES:
        st = [slope_stats(at(d, s), s) for _, d in moon]
        res["moon"][f"{s:g}"] = {
            "ridge": {k: round(st[0][k], 4) for k in ("frac_gt8", "frac_gt20", "slope_p50")},
            "range_frac_gt8": [round(min(x["frac_gt8"] for x in st), 4),
                               round(max(x["frac_gt8"] for x in st), 4)],
            "range_frac_gt20": [round(min(x["frac_gt20"] for x in st), 4),
                                round(max(x["frac_gt20"] for x in st), 4)],
        }
    ridge5 = moon[0][1]
    res["moon"]["routes"] = {f"{s:g}": route_outcomes(at(ridge5, s), s) for s in (10.0, 30.0)}
    for cid, name in LEADS.items():
        lat, lon = float(acc.loc[cid, "lat"]), float(acc.loc[cid, "lon"])
        d5 = arcticdem_5m(lat, lon)
        lead = {"name": name, "lat": lat, "lon": lon, "nan_frac": float(np.isnan(d5).mean()),
                "scales": {}}
        for s in SCALES:
            st = slope_stats(at(d5, s), s)
            m = res["moon"][f"{s:g}"]
            holds = (m["range_frac_gt8"][0] <= st["frac_gt8"] <= m["range_frac_gt8"][1]
                     and m["range_frac_gt20"][0] <= st["frac_gt20"] <= m["range_frac_gt20"][1])
            lead["scales"][f"{s:g}"] = {**{k: round(st[k], 4) for k in
                                           ("frac_gt8", "frac_gt20", "slope_p50")},
                                        "holds": bool(holds)}
        lead["routes"] = {f"{s:g}": route_outcomes(at(d5, s), s) for s in (10.0, 30.0)}
        res["leads"][cid] = lead
    (DERIVED / "multiscale.json").write_text(json.dumps(res, indent=2, default=float))
    print(json.dumps(res, indent=1, default=float))


if __name__ == "__main__":
    main()
