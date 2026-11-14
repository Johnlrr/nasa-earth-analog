"""EMIT L2A on Google Earth Engine: median footprint spectrum (shared by B3 spike and B5).

Collection ``NASA/EMIT/L2A/RFL`` (Bao checked 13:00: ~249k scenes, 08/2022-08/2026, 579 bands =
285 reflectance + 285 uncertainty + flags). Per footprint we:
  1. take every EMIT scene intersecting a square footprint (side ``km``),
  2. mask pixels: ``aggregate_flag`` (cloud/cirrus/water/spacecraft, dilated), reflectance fill,
     NDVI > ndvi_max (vegetation), NDWI > 0 or NIR < 0.08 (water / wet ground: Lake Salda),
  3. keep the scene with the MOST valid pixels inside the footprint (no mixing of illumination),
  4. return the per-band median reflectance of the valid pixels + QA counts.
No formula lives here: CRISM parameters are computed later by ``similitude.descriptors.spectral``.
"""

from __future__ import annotations

import os
import time

import ee
import numpy as np

COLLECTION = "NASA/EMIT/L2A/RFL"
N_BANDS = 285
RFL_BANDS = [f"reflectance_{i}" for i in range(N_BANDS)]
EMIT_SCALE_M = 60
_WL: np.ndarray | None = None


def init(project: str | None = None) -> None:
    ee.Initialize(project=project or os.environ.get("EE_PROJECT", "nasa-hackthon-kl"))


def wavelengths() -> np.ndarray:
    global _WL
    if _WL is None:
        first = ee.ImageCollection(COLLECTION).first()
        _WL = np.array(first.get("reflectance_wavelengths").getInfo(), dtype=float)
    return _WL


def _band(nm: float) -> str:
    return RFL_BANDS[int(np.argmin(np.abs(wavelengths() - nm)))]


def footprint_geom(lat: float, lon: float, km: float) -> ee.Geometry:
    return ee.Geometry.Point([lon, lat]).buffer(km * 500.0).bounds()


def _valid_mask(img: ee.Image, ndvi_max: float) -> ee.Image:
    red, nir, green = img.select(_band(660)), img.select(_band(860)), img.select(_band(560))
    ndvi = nir.subtract(red).divide(nir.add(red))
    ndwi = green.subtract(nir).divide(green.add(nir))
    return (img.select("aggregate_flag").eq(0)
            .And(red.gt(0)).And(nir.gt(0.08))
            .And(ndvi.lt(ndvi_max))
            .And(ndwi.lt(0)))


def best_scene(lat: float, lon: float, km: float = 5.0, ndvi_max: float = 0.15,
               max_scenes: int = 40) -> tuple[ee.Image | None, dict]:
    """The EMIT scene with the MOST valid pixels in the footprint (B5 rule, B14a scene_rule).

    Returns (image or None, meta: n_valid, n_total, scene_id, date, n_scenes).
    """
    geom = footprint_geom(lat, lon, km)
    col = ee.ImageCollection(COLLECTION).filterBounds(geom).limit(max_scenes)
    n_scenes = col.size().getInfo()
    meta = {"n_valid": 0, "n_total": 0, "scene_id": None, "date": None, "n_scenes": n_scenes}
    if n_scenes == 0:
        return None, meta

    def count(img):
        m = _valid_mask(img, ndvi_max)
        n = m.selfMask().reduceRegion(ee.Reducer.count(), geom, EMIT_SCALE_M, maxPixels=1e8)
        tot = img.select("aggregate_flag").reduceRegion(ee.Reducer.count(), geom, EMIT_SCALE_M,
                                                         maxPixels=1e8)
        return img.set({"n_valid": n.values().get(0), "n_total": tot.values().get(0)})

    best = ee.Image(col.map(count).sort("n_valid", False).first())
    info = best.toDictionary(["n_valid", "n_total", "system:index", "system:time_start"]).getInfo()
    meta.update(n_valid=int(info.get("n_valid") or 0), n_total=int(info.get("n_total") or 0),
                scene_id=info.get("system:index"))
    if info.get("system:time_start"):
        meta["date"] = time.strftime("%Y-%m-%d", time.gmtime(info["system:time_start"] / 1000))
    return best, meta


#: EMIT L2A grid on GEE (EPSG:4326, checked on scene EMIT_L2A_RFL_001_20230221T093744).
EMIT_DEG = 0.000542232520256367


def footprint_pixels(img: ee.Image, lat: float, lon: float, km: float,
                     ndvi_max: float = 0.15) -> dict:
    """All EMIT pixels of a footprint from one scene via ``computePixels`` (B13).

    Returns dict(refl (H, W, 285) float32 with NaN where invalid, valid (H, W) bool,
    deg (pixel size in degrees), lat0, lon0 (upper-left corner)). Validity = ``_valid_mask``.
    """
    half_lat = km / 2 / 111.32
    half_lon = half_lat / max(np.cos(np.radians(lat)), 1e-6)
    w = int(np.ceil(2 * half_lon / EMIT_DEG))
    h = int(np.ceil(2 * half_lat / EMIT_DEG))
    lon0, lat0 = lon - half_lon, lat + half_lat
    expr = (img.select(RFL_BANDS).toFloat()
            .addBands(_valid_mask(img, ndvi_max).unmask(0).toFloat().rename("valid")))
    arr = ee.data.computePixels({
        "expression": expr,
        "fileFormat": "NUMPY_NDARRAY",
        "grid": {"dimensions": {"width": w, "height": h},
                 "affineTransform": {"scaleX": EMIT_DEG, "shearX": 0, "translateX": lon0,
                                     "shearY": 0, "scaleY": -EMIT_DEG, "translateY": lat0},
                 "crsCode": "EPSG:4326"},
    })
    refl = np.stack([arr[b] for b in RFL_BANDS], axis=-1).astype(np.float32)
    valid = arr["valid"] > 0.5
    refl[~valid] = np.nan
    return {"refl": refl, "valid": valid, "deg": EMIT_DEG, "lat0": lat0, "lon0": lon0}


def footprint_spectrum(lat: float, lon: float, km: float = 5.0, ndvi_max: float = 0.15,
                       max_scenes: int = 40) -> dict:
    """Median EMIT spectrum of the best scene over a footprint.

    Returns dict(wl, refl (np.ndarray, NaN where no data), n_valid, n_total, scene_id, date,
    n_scenes, seconds). ``n_valid`` = valid 60 m pixels used; flag footprints with < 50.
    """
    t0 = time.time()
    geom = footprint_geom(lat, lon, km)
    best, meta = best_scene(lat, lon, km, ndvi_max, max_scenes)
    out = {"wl": wavelengths(), "refl": np.full(N_BANDS, np.nan), "seconds": 0.0, **meta}
    if best is not None and out["n_valid"] > 0:
        masked = best.select(RFL_BANDS).updateMask(_valid_mask(best, ndvi_max))
        med = masked.reduceRegion(ee.Reducer.median(), geom, EMIT_SCALE_M, maxPixels=1e8,
                                  bestEffort=False).getInfo()
        out["refl"] = np.array([med.get(b) if med.get(b) is not None else np.nan
                                for b in RFL_BANDS], dtype=float)
    out["seconds"] = time.time() - t0
    return out
