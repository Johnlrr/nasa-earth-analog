# ruff: noqa: E501
"""Pictures of each stable open-country lead, so an engineer can look at the ground first.

For every usable lead footprint (holds with both DEMs, snow/ice <= 0.2) (web/data/access.json), two 4 km images:
  - <cell>_s2.jpg    Sentinel-2 true colour (median of low-cloud local-summer scenes, 2022-2024), 10 m;
  - <cell>_slope.png slope classes <8, 8-20, >20 deg from the same Copernicus GLO-30 chip and the
                     same gradient formula as similitude.descriptors.terrain.slope_stats (30 m).
The image paths are written back into access.json. A visual aid, not a descriptor.
Usage: EE_PROJECT=<project> python scripts/access/lead_images.py [--max 30]
"""

from __future__ import annotations

import argparse
import json
import os
import sys

import numpy as np

from similitude import io

sys.path.insert(0, str(io.REPO_ROOT / "scripts"))
from gee.chip_dem import _utm_epsg, get_chip  # noqa: E402

WEB = io.REPO_ROOT / "web"
ACCESS = WEB / "data" / "access.json"
OUT = WEB / "figures" / "leads"
FOOT_M, RES_M = 4000.0, 30.0
CLASS_RGB = np.array([[111, 191, 143], [226, 168, 92], [229, 122, 104]], dtype=np.uint8)  # <8, 8-20, >20


def slope_png(lat: float, lon: float, path) -> dict:
    from PIL import Image

    dem, _ = get_chip(lat, lon, chip_m=10_000, res_m=RES_M)
    dzdy, dzdx = np.gradient(dem, RES_M)
    slope = np.degrees(np.arctan(np.hypot(dzdx, dzdy)))
    c, h = dem.shape[0] // 2, int(FOOT_M / RES_M / 2)
    s = slope[c - h:c + h, c - h:c + h]
    cls = np.digitize(s, [8.0, 20.0])
    rgb = CLASS_RGB[np.clip(cls, 0, 2)]
    rgb[np.isnan(s)] = (40, 40, 40)
    Image.fromarray(rgb).resize((400, 400), Image.NEAREST).save(path)
    v = s[~np.isnan(s)]
    return {"lt8": float(np.mean(v < 8)), "8to20": float(np.mean((v >= 8) & (v <= 20))),
            "gt20": float(np.mean(v > 20))}


def s2_jpg(ee, lat: float, lon: float, path) -> None:
    from pyproj import Transformer

    epsg = _utm_epsg(lat, lon)
    x, y = Transformer.from_crs(4326, epsg, always_xy=True).transform(lon, lat)
    pt = ee.Geometry.Point(lon, lat)
    col = (ee.ImageCollection("COPERNICUS/S2_SR_HARMONIZED").filterBounds(pt)
           .filterDate("2022-01-01", "2024-12-31").filter(ee.Filter.lt("CLOUDY_PIXEL_PERCENTAGE", 15))
           # local summer only (July-September north, January-March south): seasonal snow hides the ground
           .filter(ee.Filter.calendarRange(7, 9, "month") if lat > 0 else ee.Filter.calendarRange(1, 3, "month")))
    img = col.median().select(["B4", "B3", "B2"]).visualize(min=0, max=3000, gamma=1.2)
    n = 400
    raw = ee.data.computePixels({
        "expression": img, "fileFormat": "JPEG",
        "grid": {"dimensions": {"width": n, "height": n}, "crsCode": f"EPSG:{epsg}",
                 "affineTransform": {"scaleX": FOOT_M / n, "shearX": 0, "translateX": x - FOOT_M / 2,
                                     "shearY": 0, "scaleY": -FOOT_M / n, "translateY": y + FOOT_M / 2}}})
    path.write_bytes(raw)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--max", type=int, default=30)
    a = ap.parse_args()
    import ee
    ee.Initialize(project=os.environ["EE_PROJECT"])
    doc = json.loads(ACCESS.read_text(encoding="utf-8"))
    OUT.mkdir(parents=True, exist_ok=True)
    done: dict[str, dict] = {}
    for reg in doc["regions"]:
        for lead in reg["leads"]:
            if not lead.get("usable"):
                continue
            cid = lead["cell_id"]
            if cid not in done and len(done) < a.max:
                try:
                    shares = slope_png(lead["lat"], lead["lon"], OUT / f"{cid}_slope.png")
                    s2_jpg(ee, lead["lat"], lead["lon"], OUT / f"{cid}_s2.jpg")
                    done[cid] = {"s2": f"figures/leads/{cid}_s2.jpg",
                                 "slope": f"figures/leads/{cid}_slope.png", "slope_classes": shares}
                    print(f"  {cid}: <8 {shares['lt8']:.2f}  8-20 {shares['8to20']:.2f}  >20 {shares['gt20']:.2f}")
                except Exception as exc:
                    print(f"  {cid}: {type(exc).__name__} {str(exc)[:100]}")
                    done[cid] = {}
            if done.get(cid):
                lead["images"] = done[cid]
    ACCESS.write_text(json.dumps(doc, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"{sum(1 for v in done.values() if v)} leads with images -> {OUT.relative_to(io.REPO_ROOT)}")


if __name__ == "__main__":
    main()
