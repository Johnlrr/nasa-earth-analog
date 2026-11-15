# ruff: noqa: E501
"""Complete the comparison assets of the web app for every footprint it can show.

For every Earth cell the expedition UI can open (candidates.geojson: lens cells and each site's
best cell per lens/target):
  - a 4 km Sentinel-2 true-colour image (local-summer median 2022-2024, 10 m; GEE computePixels)
    -> web/media/expedition/footprints/<cell>.jpg, listed in web/footprint-images.js;
  - for the Moon terrain lenses (L1, L2) a 4 km Copernicus GLO-30 elevation grid (central 4 km of
    the cached 10 km chip, every 2nd 30 m sample) -> web/terrain-data.js ("earth:<cell>").
And for each Moon target used by a lens, the central 4 km of its PGDA 78 5 m DEM sampled every
10th pixel (50 m), as done for Connecting Ridge -> "target:<id>".
Existing entries are kept. Pictures and grids are display aids; they never enter a score.
Usage: EE_PROJECT=<project> python scripts/web_assets.py
"""

from __future__ import annotations

import hashlib
import json
import os
import sys
from pathlib import Path

import numpy as np
import pandas as pd

from similitude import io

sys.path.insert(0, str(io.REPO_ROOT / "scripts"))
from access.lead_images import s2_jpg  # noqa: E402
from gee.chip_dem import get_chip  # noqa: E402

ROOT = io.REPO_ROOT
WEB = ROOT / "web"
IMG_JS, DEM_JS = WEB / "footprint-images.js", WEB / "terrain-data.js"
IMG_DIR = WEB / "media" / "expedition" / "footprints"
DERIVED = ROOT / "data" / "derived"
TERRAIN_LENSES = {"L1", "L2"}
MOON_TIF = {"connecting_ridge": ROOT / ".taste-skill" / "source" / "connecting-ridge.tif",
            "shackleton_rim": ROOT / ".taste-skill" / "source" / "shackleton-wall.tif"}
MOON_NAME = {"connecting_ridge": "Connecting Ridge", "shackleton_rim": "Shackleton inner wall"}


def load_js(path: Path, var: str) -> dict:
    if not path.exists():
        return {}
    s = path.read_text(encoding="utf-8")
    return json.loads(s[s.index("{"):s.rstrip().rstrip(";").rindex("}") + 1])


def save_js(path: Path, var: str, obj: dict) -> None:
    path.write_text(f"window.{var} = " + json.dumps(obj, ensure_ascii=False, separators=(",", ":")) + ";\n",
                    encoding="utf-8")


def coords() -> dict[str, tuple[float, float]]:
    out: dict[str, tuple[float, float]] = {}
    for f in ["earth_L1.parquet", "earth_L1_null2.parquet", "earth_L2.parquet", "earth_X1.parquet",
              "earth_M1.parquet", "site_cells.parquet", "access_screen.parquet"]:
        p = DERIVED / f
        if p.exists():
            d = pd.read_parquet(p)
            if {"cell_id", "lat", "lon"} <= set(d.columns):
                for r in d[["cell_id", "lat", "lon"]].dropna().itertuples(index=False):
                    out.setdefault(str(r.cell_id), (float(r.lat), float(r.lon)))
    return out


def wanted() -> list[dict]:
    g = json.loads((WEB / "data" / "candidates.geojson").read_text(encoding="utf-8"))
    look = coords()
    rows = []
    for f in g["features"]:
        p = f["properties"]
        if p.get("feature_type") == "site":
            for r in p.get("field", []):
                c = r.get("best_cell")
                if c and c in look:
                    rows.append({"cell": c, "lat": look[c][0], "lon": look[c][1], "lens": r["lens"],
                                 "target": r.get("target"), "name": p["name"]})
            continue
        cell = p["id"].split("-", 1)[1]
        lon, lat = f["geometry"]["coordinates"][:2]
        for lens, ls in (p.get("lens_scores") or {}).items():
            rows.append({"cell": cell, "lat": float(lat), "lon": float(lon), "lens": lens,
                         "target": ls.get("target"), "name": p.get("name") or cell})
    return rows


def earth_grid(lat: float, lon: float, name: str) -> dict:
    dem, meta = get_chip(lat, lon, chip_m=10_000, res_m=30.0)
    c, h = dem.shape[0] // 2, int(round(2000 / 30.0))
    sub = dem[c - h:c + h + 1:2, c - h:c + h + 1:2]
    grid = [[None if not np.isfinite(v) else round(float(v), 1) for v in row] for row in sub]
    return {"name": name, "grid": grid, "step_m": 60.0, "native_m": 30.0, "extent_m": float(len(grid) - 1) * 60.0,
            "source": "Copernicus GLO-30 (AWS open data)", "datum": "Earth vertical datum (EGM2008); elevations relative within the window",
            "kind": "earth", "lat": round(lat, 4), "lon": round(lon, 4)}


def moon_grid(tid: str) -> dict | None:
    path = MOON_TIF.get(tid)
    if not path or not path.exists() or path.stat().st_size < 40_000_000:  # PGDA 78 site rasters are ~41 MB
        return None
    import rasterio

    with rasterio.open(path) as ds:
        a = ds.read(1).astype("float64")
        nod = ds.nodata
    if nod is not None:
        a[a == nod] = np.nan
    cy, cx = a.shape[0] // 2, a.shape[1] // 2
    sub = a[cy - 400:cy + 401:10, cx - 400:cx + 401:10]
    return {"name": MOON_NAME[tid], "grid": [[None if not np.isfinite(v) else round(float(v), 2) for v in row] for row in sub],
            "step_m": 50, "native_m": 5, "extent_m": 4000, "source": "NASA / GSFC / LRO / LOLA / PGDA 78",
            "datum": "Source lunar elevation datum; not comparable to Earth sea level", "kind": "target",
            "sha256": hashlib.sha256(path.read_bytes()).hexdigest()}


def main() -> None:
    import ee

    ee.Initialize(project=os.environ["EE_PROJECT"])
    imgs, dems = load_js(IMG_JS, "SimilitudeFootprintImages"), load_js(DEM_JS, "SimilitudeTerrainData")
    IMG_DIR.mkdir(parents=True, exist_ok=True)
    rows = wanted()
    done_img, done_dem = 0, 0
    for r in {x["cell"]: x for x in rows}.values():
        cell = r["cell"]
        if cell not in imgs:
            out = IMG_DIR / f"{cell}.jpg"
            try:
                if not out.exists():
                    s2_jpg(ee, r["lat"], r["lon"], out)
                imgs[cell] = {"src": f"media/expedition/footprints/{cell}.jpg", "name": r["name"],
                              "credit": "Copernicus Sentinel-2 / Google Earth Engine",
                              "note": "4 km footprint, local-summer median 2022-2024 (10 m). Context only; not used in the score.",
                              "center_lon_lat": [round(r["lon"], 4), round(r["lat"], 4)]}
                done_img += 1
            except Exception as exc:
                print(f"  image {cell}: {type(exc).__name__} {str(exc)[:90]}")
    for r in rows:
        key = "earth:" + r["cell"]
        if r["lens"] in TERRAIN_LENSES and key not in dems:
            try:
                dems[key] = earth_grid(r["lat"], r["lon"], r["name"])
                done_dem += 1
            except Exception as exc:
                print(f"  dem {r['cell']}: {type(exc).__name__} {str(exc)[:90]}")
        tk = "target:" + str(r["target"])
        if r["lens"] in TERRAIN_LENSES and tk not in dems:
            g = moon_grid(str(r["target"]))
            if g:
                dems[tk] = g
    save_js(IMG_JS, "SimilitudeFootprintImages", imgs)
    save_js(DEM_JS, "SimilitudeTerrainData", dems)
    need_img = {x["cell"] for x in rows}
    need_dem = {x["cell"] for x in rows if x["lens"] in TERRAIN_LENSES}
    print(f"images: +{done_img}, missing {sorted(need_img - set(imgs))}")
    print(f"earth grids: +{done_dem}, missing {sorted(c for c in need_dem if 'earth:' + c not in dems)}")
    print(f"targets: {sorted(k for k in dems if k.startswith('target:'))}")


if __name__ == "__main__":
    main()
