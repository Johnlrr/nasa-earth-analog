"""Tier-1 global coarse terrain screen on Google Earth Engine (PLAN item A2).

For every 10 km cell (EPSG:3410, equal area) on inert land, compute coarse terrain
descriptors from Copernicus GLO-30 resampled to 90 m. These are used ONLY for a
preliminary ranking against the Moon targets (A3 computes the same four numbers on
PGDA DEMs). Every published fidelity number is computed later by the shared library
(``similitude.descriptors``) on 30 m chips (A6).

Modes
-----
--mode test    : synchronous sample of one bbox (``--bbox``), printed and saved to CSV.
--mode export  : start server-side ``Export.table.toAsset`` tasks, one per region.
--mode status  : print the state of the export tasks.
--mode collect : download finished assets and write ``data/derived/tier1_terrain.csv``.

Project id comes from the ``EE_PROJECT`` environment variable (required).
"""

from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path

import ee
import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
OUT_CSV = ROOT / "data" / "derived" / "tier1_terrain.csv"
RAW_DIR = ROOT / "data" / "raw" / "earth" / "tier1"

CELL_M = 10_000
SOURCE = "Copernicus GLO-30 (90 m) + ESA WorldCover v200 + MODIS MOD13A2 2023, via GEE"

# Inert-land thresholds (PLAN A2). Do not tune after seeing results.
INERT_FRAC_MIN = 0.5  # WorldCover 60 bare/sparse + 100 moss & lichen
BAD_FRAC_MAX = 0.1  # WorldCover 40 crop + 50 built + 80 water
NDVI_MAX = 0.25  # mean of 2023 annual-max NDVI over the cell

# Export regions (lon_min, lat_min, lon_max, lat_max); land between 60S and 84N.
REGIONS = {
    "n_america": (-170, 5, -50, 84),
    "s_america": (-82, -56, -34, 13),
    "africa": (-20, -36, 52, 38),
    "europe": (-25, 34, 45, 72),
    "w_asia": (25, 5, 75, 56),
    "n_asia": (45, 45, 180, 82),
    "e_asia": (75, -11, 150, 50),
    "oceania": (110, -48, 180, -10),
    "arctic_is": (-75, 72, 45, 84),
}


def init() -> str:
    project = os.environ["EE_PROJECT"]
    ee.Initialize(project=project)
    return project


def _layers() -> tuple[ee.Image, ee.Image]:
    """Return (screen, terrain) images in native projections (no forced reprojection)."""
    wc = ee.ImageCollection("ESA/WorldCover/v200").first().select("Map")
    inert = wc.eq(60).Or(wc.eq(100)).rename("inert_frac")
    bad = wc.eq(40).Or(wc.eq(50)).Or(wc.eq(80)).rename("bad_frac")
    ndvi_col = (
        ee.ImageCollection("MODIS/061/MOD13A2")
        .filterDate("2023-01-01", "2024-01-01")
        .select("NDVI")
    )
    ndvi = ndvi_col.max().multiply(0.0001).rename("ndvi_max")
    screen = ee.Image.cat([inert, bad, ndvi])

    col = ee.ImageCollection("COPERNICUS/DEM/GLO30").select("DEM")
    # mosaic() drops the native projection: restore it, then mean-aggregate to a 90 m
    # geographic grid so slope is computed at the 90 m baseline (ee.Terrain.slope uses
    # true geodesic pixel size in geographic grids).
    dem = col.mosaic().setDefaultProjection(col.first().projection())
    dem = dem.reduceResolution(ee.Reducer.mean(), maxPixels=256).reproject(
        ee.Projection("EPSG:4326").atScale(90)
    )
    slope = ee.Terrain.slope(dem)
    terrain = ee.Image.cat(
        [
            slope.rename("slope"),
            slope.gt(8).rename("gt8"),
            slope.gt(20).rename("gt20"),
            dem.rename("elev"),
        ]
    )
    return screen, terrain


def cells_for(bbox: tuple[float, float, float, float]) -> ee.FeatureCollection:
    """10 km equal-area cells in bbox that pass the inert-land screen, with coarse terrain."""
    region = ee.Geometry.Rectangle(list(bbox), proj="EPSG:4326", geodesic=False)
    grid = region.coveringGrid(ee.Projection("EPSG:3410").atScale(CELL_M))
    screen, terrain = _layers()

    # Stage 1 (cheap, 1 km): inert-land screen. Means are fractions of cell area.
    grid = screen.reduceRegions(
        collection=grid, reducer=ee.Reducer.mean(), scale=1000, tileScale=4
    )
    keep = grid.filter(
        ee.Filter.And(
            ee.Filter.gte("inert_frac", INERT_FRAC_MIN),
            ee.Filter.lt("bad_frac", BAD_FRAC_MAX),
            ee.Filter.lt("ndvi_max", NDVI_MAX),
        )
    )

    # Stage 2 (90 m): coarse terrain on surviving cells only.
    reducer = (
        ee.Reducer.mean()
        .combine(ee.Reducer.median(), sharedInputs=True)
        .combine(ee.Reducer.minMax(), sharedInputs=True)
    )
    keep = terrain.reduceRegions(collection=keep, reducer=reducer, scale=90, tileScale=4)

    def tidy(f: ee.Feature) -> ee.Feature:
        centre = f.geometry().centroid(maxError=10)
        c = centre.coordinates()
        return ee.Feature(
            centre,  # Export.table.toAsset requires a geometry
            {
                "lon": c.get(0),
                "lat": c.get(1),
                "slope_p50_90m": f.get("slope_median"),
                "frac_gt8_90m": f.get("gt8_mean"),
                "frac_gt20_90m": f.get("gt20_mean"),
                "relief_90m": ee.Number(f.get("elev_max")).subtract(f.get("elev_min")),
                "inert_frac": f.get("inert_frac"),
                "bad_frac": f.get("bad_frac"),
                "ndvi_max": f.get("ndvi_max"),
            },
        )

    # Drop cells with no DEM coverage BEFORE map(): null elev_max/min would make
    # ee.Number(null).subtract() fail the whole export.
    keep = keep.filter(ee.Filter.notNull(["slope_median", "elev_max", "elev_min"]))
    return keep.map(tidy)


def finalize(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    # Equal-area cell index from the cell centre (EPSG:3410, 10 km).
    from pyproj import Transformer

    tr = Transformer.from_crs("EPSG:4326", "EPSG:3410", always_xy=True)
    x, y = tr.transform(df["lon"].to_numpy(), df["lat"].to_numpy())
    df["cell_id"] = [
        f"E10K_{int(yy // CELL_M)}_{int(xx // CELL_M)}" for xx, yy in zip(x, y, strict=True)
    ]
    df["source"] = SOURCE
    cols = [
        "cell_id", "lat", "lon", "slope_p50_90m", "frac_gt8_90m", "frac_gt20_90m",
        "relief_90m", "inert_frac", "bad_frac", "ndvi_max", "source",
    ]
    df = df[cols].drop_duplicates("cell_id")
    return df


def mode_test(bbox: tuple[float, float, float, float], out: Path) -> None:
    fc = cells_for(bbox)
    df = ee.data.computeFeatures({"expression": fc, "fileFormat": "PANDAS_DATAFRAME"})
    if df.empty:
        print("No inert cells in bbox.")
        return
    df = finalize(df.drop(columns=[c for c in ("geo",) if c in df.columns]))
    out.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(out, index=False)
    print(f"{len(df)} cells -> {out}")
    print(df.head(10).to_string(index=False))


def asset_id(project: str, name: str) -> str:
    return f"projects/{project}/assets/tier1_terrain_{name}"


def mode_export(project: str, only: list[str] | None = None) -> None:
    for name, bbox in REGIONS.items():
        if only and name not in only:
            continue
        task = ee.batch.Export.table.toAsset(
            collection=cells_for(bbox),
            description=f"tier1_terrain_{name}",
            assetId=asset_id(project, name),
        )
        task.start()
        print(f"started {name}: {task.id}")


def mode_status() -> None:
    for t in ee.data.getTaskList()[:40]:
        if t.get("description", "").startswith("tier1_terrain_"):
            msg = t.get("error_message", "")
            print(f"{t['description']:28s} {t['state']:10s} {msg}")


def mode_collect(project: str) -> None:
    frames = []
    for name in REGIONS:
        aid = asset_id(project, name)
        try:
            fc = ee.FeatureCollection(aid)
            df = ee.data.computeFeatures({"expression": fc, "fileFormat": "PANDAS_DATAFRAME"})
        except ee.EEException as exc:
            print(f"{name}: not ready ({exc})")
            continue
        RAW_DIR.mkdir(parents=True, exist_ok=True)
        df.to_csv(RAW_DIR / f"tier1_{name}.csv", index=False)
        print(f"{name}: {len(df)} cells")
        frames.append(df)
    if not frames:
        sys.exit("No region ready.")
    df = finalize(pd.concat(frames, ignore_index=True))
    OUT_CSV.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(OUT_CSV, index=False)
    print(f"{len(df)} unique cells -> {OUT_CSV}")


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--mode", choices=["test", "export", "status", "collect"], default="test")
    ap.add_argument("--bbox", default="-95,72,-80,78", help="minlon,minlat,maxlon,maxlat")
    ap.add_argument("--out", default=str(RAW_DIR / "tier1_test.csv"))
    ap.add_argument("--regions", default="", help="comma list for --mode export")
    args = ap.parse_args()
    project = init()
    if args.mode == "test":
        bbox = tuple(float(v) for v in args.bbox.split(","))
        mode_test(bbox, Path(args.out))
    elif args.mode == "export":
        mode_export(project, [r for r in args.regions.split(",") if r] or None)
    elif args.mode == "status":
        mode_status()
    else:
        mode_collect(project)


if __name__ == "__main__":
    main()
