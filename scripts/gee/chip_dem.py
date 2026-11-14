"""
Fetch a DEM chip from Copernicus GLO-30 (AWS open data, no account needed).

Source: Copernicus DEM GLO-30 COG tiles on AWS
  s3://copernicus-dem-30m (public, anonymous access via /vsicurl/)
  URL pattern:
    https://copernicus-dem-30m.s3.amazonaws.com/
    Copernicus_DSM_COG_10_{NS}{lat:02d}_00_{EW}{lon:03d}_00_DEM/
    Copernicus_DSM_COG_10_{NS}{lat:02d}_00_{EW}{lon:03d}_00_DEM.tif

NOTE: GLO-30 is a DSM (Digital Surface Model), not a bare-earth DTM.
Vegetation and buildings contribute to elevation. Apply a bare-earth mask
(e.g. ESA WorldCover land-use filter) downstream to mitigate DSM bias.

Usage:
    dem, meta = get_chip(lat=75.38, lon=-89.68, chip_m=10_000, res_m=30.0)
"""

from __future__ import annotations

import json
import logging
import math
from pathlib import Path

import numpy as np
import rasterio
from rasterio.crs import CRS
from rasterio.merge import merge
from rasterio.warp import Resampling, reproject

log = logging.getLogger(__name__)

_BASE_URL = (
    "https://copernicus-dem-30m.s3.amazonaws.com/"
    "Copernicus_DSM_COG_10_{ns}{lat:02d}_00_{ew}{lon:03d}_00_DEM/"
    "Copernicus_DSM_COG_10_{ns}{lat:02d}_00_{ew}{lon:03d}_00_DEM.tif"
)


def _tile_name(tile_lat: int, tile_lon: int) -> str:
    """Return the GLO-30 tile identifier string for the given 1° cell.

    tile_lat / tile_lon are the integer floor of the cell's lower-left corner.
    E.g. lat=75.38, lon=-89.68 → floor lat=75, floor lon=-90 → 'N75_00_W090_00'.
    """
    ns = "N" if tile_lat >= 0 else "S"
    ew = "E" if tile_lon >= 0 else "W"
    return f"{ns}{abs(tile_lat):02d}_00_{ew}{abs(tile_lon):03d}_00"


def _tile_url(tile_lat: int, tile_lon: int) -> str:
    ns = "N" if tile_lat >= 0 else "S"
    ew = "E" if tile_lon >= 0 else "W"
    return _BASE_URL.format(
        ns=ns,
        lat=abs(tile_lat),
        ew=ew,
        lon=abs(tile_lon),
    )


def _utm_epsg(lat: float, lon: float) -> int:
    """Return EPSG code for the local UTM zone containing (lat, lon)."""
    zone = int((lon + 180) / 6) % 60 + 1
    if lat >= 0:
        return 32600 + zone  # WGS84 / UTM north
    else:
        return 32700 + zone  # WGS84 / UTM south


def _intersecting_tiles(lat: float, lon: float, chip_m: float, pad_deg: float = 0.02):
    """Return list of (tile_lat, tile_lon) 1° cells that intersect the chip bbox.

    The geographic bounding box is approximated from the chip size (in metres)
    using 111 km/° latitude. A pad of pad_deg degrees is added on every side.
    """
    deg_per_m_lat = 1.0 / 111_000.0
    deg_per_m_lon = 1.0 / (111_000.0 * max(math.cos(math.radians(lat)), 1e-6))

    half_lat = (chip_m / 2.0) * deg_per_m_lat + pad_deg
    half_lon = (chip_m / 2.0) * deg_per_m_lon + pad_deg

    lat_min = lat - half_lat
    lat_max = lat + half_lat
    lon_min = lon - half_lon
    lon_max = lon + half_lon

    tile_lat_min = math.floor(lat_min)
    tile_lat_max = math.floor(lat_max)
    tile_lon_min = math.floor(lon_min)
    tile_lon_max = math.floor(lon_max)

    tiles = []
    for tl in range(tile_lat_min, tile_lat_max + 1):
        for tlon in range(tile_lon_min, tile_lon_max + 1):
            tiles.append((tl, tlon))
    return tiles


def _fetch_tile_window(url: str, bbox_wgs84: tuple[float, float, float, float]):
    """Open a GLO-30 tile via /vsicurl/ and read only the window covering bbox_wgs84.

    Returns (data, transform, nodata) or None if the tile is missing (HTTP 404 / ocean).
    bbox_wgs84 = (west, south, east, north) in geographic degrees.
    """
    vsicurl_url = f"/vsicurl/{url}"
    try:
        with rasterio.open(vsicurl_url) as src:
            west, south, east, north = bbox_wgs84
            # rasterio window from bounds
            win = src.window(west, south, east, north)
            win = win.intersection(rasterio.windows.Window(0, 0, src.width, src.height))
            if win.width <= 0 or win.height <= 0:
                return None
            data = src.read(1, window=win, masked=True).astype(np.float64)
            data = (
                np.where(data.mask, np.nan, data.data)
                if np.ma.is_masked(data)
                else data.astype(np.float64)
            )
            win_transform = src.window_transform(win)
            return data, win_transform, src.crs, src.nodata
    except Exception as exc:
        msg = str(exc).lower()
        if "404" in msg or "not found" in msg or "no such file" in msg:
            log.debug("Tile not found (ocean/missing): %s", url)
            return None
        raise


def get_chip(
    lat: float,
    lon: float,
    chip_m: float = 10_000,
    res_m: float = 30.0,
    cache_dir: str = "data/raw/earth/chips",
) -> tuple[np.ndarray, dict]:
    """Fetch a DEM chip centred on (lat, lon) from Copernicus GLO-30 (AWS).

    Parameters
    ----------
    lat, lon : centre of the chip in decimal degrees (WGS84).
    chip_m   : chip side length in metres. Default 10 000.
    res_m    : output pixel size in metres. Default 30.
    cache_dir: directory for .npy / .json cache files.

    Returns
    -------
    dem  : 2-D float64 array, shape (n, n) where n = round(chip_m / res_m).
           nodata pixels are NaN.
    meta : dict with keys:
        crs        – rasterio CRS of the output (UTM local)
        tiles      – list of tile identifiers that were used
        nodata_frac – fraction of output pixels that are NaN
        source     – data source description
        chip_m, res_m, lat, lon
    """
    cache_path = Path(cache_dir)
    cache_key = f"{lat:.4f}_{lon:.4f}_{int(chip_m)}"
    npy_file = cache_path / f"{cache_key}.npy"
    json_file = cache_path / f"{cache_key}.json"

    if npy_file.exists() and json_file.exists():
        dem = np.load(npy_file)
        with open(json_file) as f:
            meta = json.load(f)
        log.info("Cache hit: %s", cache_key)
        return dem, meta

    # --- determine tiles needed ---
    tiles = _intersecting_tiles(lat, lon, chip_m)

    # --- geographic bbox for window read ---
    deg_per_m_lat = 1.0 / 111_000.0
    deg_per_m_lon = 1.0 / (111_000.0 * max(math.cos(math.radians(lat)), 1e-6))
    half_lat = (chip_m / 2.0) * deg_per_m_lat + 0.02
    half_lon = (chip_m / 2.0) * deg_per_m_lon + 0.02
    bbox_wgs84 = (lon - half_lon, lat - half_lat, lon + half_lon, lat + half_lat)

    # --- fetch tile windows ---
    datasets = []
    tile_names_used = []
    for tl, tlon in tiles:
        url = _tile_url(tl, tlon)
        result = _fetch_tile_window(url, bbox_wgs84)
        if result is None:
            continue
        data, transform, crs, nodata = result
        tile_names_used.append(_tile_name(tl, tlon))
        # write to in-memory rasterio dataset via MemoryFile
        import rasterio.io

        memfile = rasterio.io.MemoryFile()
        with memfile.open(
            driver="GTiff",
            height=data.shape[0],
            width=data.shape[1],
            count=1,
            dtype=np.float64,
            crs=crs,
            transform=transform,
            nodata=np.nan,
        ) as dst:
            dst.write(data, 1)
        datasets.append(memfile.open())

    if not datasets:
        n = int(round(chip_m / res_m))
        dem = np.full((n, n), np.nan)
        meta = {
            "crs": None,
            "tiles": [],
            "nodata_frac": 1.0,
            "source": "Copernicus GLO-30 (AWS open data)",
            "chip_m": chip_m,
            "res_m": res_m,
            "lat": lat,
            "lon": lon,
            "note": "No tiles found (all ocean or missing)",
        }
        return dem, meta

    # --- merge ---
    if len(datasets) == 1:
        merged_data = datasets[0].read(1)
        merged_transform = datasets[0].transform
        src_crs = datasets[0].crs
    else:
        merged_data, merged_transform = merge(datasets)
        merged_data = merged_data[0]
        src_crs = datasets[0].crs

    # Replace nodata with NaN
    merged_data = merged_data.astype(np.float64)
    # GLO-30 nodata is typically very large negative (e.g. -32768)
    merged_data[merged_data < -1000] = np.nan

    for ds in datasets:
        ds.close()

    # --- reproject to local UTM ---
    epsg = _utm_epsg(lat, lon)
    dst_crs = CRS.from_epsg(epsg)

    n = int(round(chip_m / res_m))

    # Compute UTM centre
    from pyproj import Transformer

    transformer = Transformer.from_crs("EPSG:4326", dst_crs, always_xy=True)
    cx_utm, cy_utm = transformer.transform(lon, lat)

    # Build output transform: upper-left corner such that centre = (cx_utm, cy_utm)
    half_px = (n / 2.0) * res_m
    dst_transform = rasterio.transform.from_origin(cx_utm - half_px, cy_utm + half_px, res_m, res_m)

    dst_array = np.full((n, n), np.nan, dtype=np.float64)

    reproject(
        source=merged_data,
        destination=dst_array,
        src_transform=merged_transform,
        src_crs=src_crs,
        dst_transform=dst_transform,
        dst_crs=dst_crs,
        resampling=Resampling.bilinear,
        src_nodata=np.nan,
        dst_nodata=np.nan,
    )

    nodata_frac = float(np.isnan(dst_array).mean())

    meta = {
        "crs": dst_crs.to_string(),
        "epsg": epsg,
        "tiles": tile_names_used,
        "nodata_frac": nodata_frac,
        "source": "Copernicus GLO-30 (AWS open data)",
        "chip_m": chip_m,
        "res_m": res_m,
        "lat": lat,
        "lon": lon,
    }

    # --- cache ---
    cache_path.mkdir(parents=True, exist_ok=True)
    np.save(npy_file, dst_array)
    with open(json_file, "w") as f:
        json.dump(meta, f, indent=2)
    log.info("Cached chip %s, nodata_frac=%.3f, tiles=%s", cache_key, nodata_frac, tile_names_used)

    return dst_array, meta


if __name__ == "__main__":
    import argparse

    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
    parser = argparse.ArgumentParser(description="Fetch a GLO-30 DEM chip.")
    parser.add_argument("lat", type=float)
    parser.add_argument("lon", type=float)
    parser.add_argument("--chip-m", type=float, default=10_000)
    parser.add_argument("--res-m", type=float, default=30.0)
    parser.add_argument("--cache-dir", default="data/raw/earth/chips")
    args = parser.parse_args()

    dem, meta = get_chip(args.lat, args.lon, args.chip_m, args.res_m, args.cache_dir)
    print(f"Shape: {dem.shape}, nodata_frac={meta['nodata_frac']:.3f}")
    print(f"Tiles: {meta['tiles']}")
    print(f"CRS: {meta.get('epsg')}")
