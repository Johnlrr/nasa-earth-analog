"""B2 — CTX image chips of the Mars M1 targets for the RGB/texture ablation branch (a).

Source: MRO CTX global mosaic (Caltech beta01, uncontrolled, 5 m), served by NASA Mars Trek through
the OnMars ArcGIS tile cache (template found in Mars Trek WMTS capabilities for layer
``CTX_beta01_uncontrolled_5m_Caltech``). Level 11 = 1.7166e-4 deg/px ~ 10.2 m/px on Mars, i.e. the
common 10 m resolution PLAN A8 requires for the RGB branch.

Output: data/raw/mars/ctx_chips/<target_id>.png (+ .json metadata), footprint = lens M1 footprint.
"""

from __future__ import annotations

import io as _io
import json
import math

import numpy as np
import requests
from PIL import Image, ImageFile

from similitude import io

ImageFile.LOAD_TRUNCATED_IMAGES = True  # some cached tiles are partially written

TILE_URL = "https://astro.arcgis.com/arcgis/rest/services/OnMars/CTX/MapServer/tile/{z}/{row}/{col}"
LEVEL = 11
RES_DEG = 0.000171661376953125  # level 11
TILE = 512
MARS_KM_PER_DEG = 2 * math.pi * 3396.19 / 360.0
OUT = io.REPO_ROOT / "data" / "raw" / "mars" / "ctx_chips"


def fetch_tile(row: int, col: int) -> np.ndarray:
    r = requests.get(TILE_URL.format(z=LEVEL, row=row, col=col), timeout=60,
                     headers={"User-Agent": "similitude-hackathon/0.1"})
    if r.status_code != 200 or not r.content:
        return np.zeros((TILE, TILE), dtype=np.uint8)  # no coverage -> counted in zero_frac
    return np.asarray(Image.open(_io.BytesIO(r.content)).convert("L"))


def chip(lat: float, lon: float, size_km: float) -> np.ndarray:
    half_lat = size_km / 2 / MARS_KM_PER_DEG
    half_lon = half_lat / max(math.cos(math.radians(lat)), 1e-6)
    x0, x1 = (lon - half_lon + 180) / RES_DEG, (lon + half_lon + 180) / RES_DEG
    y0, y1 = (90 - (lat + half_lat)) / RES_DEG, (90 - (lat - half_lat)) / RES_DEG
    c0, c1 = int(x0 // TILE), int(x1 // TILE)
    r0, r1 = int(y0 // TILE), int(y1 // TILE)
    mosaic = np.zeros(((r1 - r0 + 1) * TILE, (c1 - c0 + 1) * TILE), dtype=np.uint8)
    for row in range(r0, r1 + 1):
        for col in range(c0, c1 + 1):
            t = fetch_tile(row, col)
            mosaic[(row - r0) * TILE:(row - r0) * TILE + t.shape[0],
                   (col - c0) * TILE:(col - c0) * TILE + t.shape[1]] = t
    ys, xs = int(y0 - r0 * TILE), int(x0 - c0 * TILE)
    ye, xe = int(y1 - r0 * TILE), int(x1 - c0 * TILE)
    img = mosaic[ys:ye, xs:xe]
    # resample longitude axis so pixels are square in metres (~10 m)
    n = img.shape[0]
    return np.asarray(Image.fromarray(img).resize((n, n), Image.BILINEAR))


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    lens = io.load_lenses()["M1"]
    targets = io.load_targets()
    for tid in lens["targets"]:
        t = targets[tid]
        img = chip(t["lat"], t["lon"], lens["footprint_km"])
        Image.fromarray(img).save(OUT / f"{tid}.png")
        meta = {"target_id": tid, "lat": t["lat"], "lon": t["lon"], "size_km": lens["footprint_km"],
                "pixels": img.shape[0], "m_per_px": lens["footprint_km"] * 1000 / img.shape[0],
                "source": "MRO CTX global mosaic beta01 (Caltech), NASA Mars Trek / OnMars tiles",
                "level": LEVEL, "mean_dn": float(img.mean()), "zero_frac": float((img == 0).mean())}
        (OUT / f"{tid}.json").write_text(json.dumps(meta, indent=1), encoding="utf-8")
        print(tid, img.shape, f"{meta['m_per_px']:.1f} m/px", f"zero={meta['zero_frac']:.2f}")


if __name__ == "__main__":
    main()
