"""PLAN item A7: Low-Sun Navigation lens (L2) tables for Earth and Moon.

Same formulas on both bodies (``similitude.descriptors``):
- terrain shadow fractions ``shadow_e2/e5/e7`` are reused from the L1 tables (identical chips,
  identical function, 3 km buffer rule);
- sun-geometry descriptors ``lowsun_frac_daylight`` and ``lowsun_az_coverage`` come from
  ``low_sun_hours`` with the body's obliquity (Earth 23.44 deg, Moon 1.54 deg).

Earth only: ``snow_free_frac`` = fraction of valid 2023 MODIS MOD10A1 observations with
NDSI snow cover < 10 within the 4 km footprint (via Google Earth Engine). It is a gate/context
column, not a fidelity descriptor (snow does not exist on the Moon).

Outputs: data/derived/earth_L2.parquet, data/derived/targets_L2.parquet
"""

from __future__ import annotations

import os
import sys
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from similitude.descriptors.astro import low_sun_hours  # noqa: E402

DERIVED = ROOT / "data" / "derived"
EARTH_OBLIQUITY = 23.44
MOON_OBLIQUITY = 1.54
ASTRO_COLS = ["lowsun_frac_daylight", "lowsun_az_coverage", "lowsun_frac_time"]


def add_astro(df: pd.DataFrame, obliquity: float) -> pd.DataFrame:
    out = df.copy()
    rows = [low_sun_hours(float(lat), 7.0, obliquity) for lat in out["lat"]]
    for c in ASTRO_COLS:
        out[c] = [r[c] for r in rows]
    return out


def snow_free_fraction(df: pd.DataFrame) -> pd.Series:
    import ee

    ee.Initialize(project=os.environ.get("EE_PROJECT", "similitude-ee"))
    col = ee.ImageCollection("MODIS/061/MOD10A1").filterDate("2023-01-01", "2024-01-01")

    def snow_free(img: ee.Image) -> ee.Image:
        ndsi = img.select("NDSI_Snow_Cover")
        return ndsi.lt(10).updateMask(ndsi.lte(100)).rename("snow_free")

    frac = col.map(snow_free).mean()
    feats = [
        ee.Feature(
            ee.Geometry.Point([float(r.lon), float(r.lat)]).buffer(2000), {"cell_id": r.cell_id}
        )
        for r in df.itertuples()
    ]
    out = []
    for i in range(0, len(feats), 200):
        fc = frac.reduceRegions(
            collection=ee.FeatureCollection(feats[i : i + 200]),
            reducer=ee.Reducer.mean(),
            scale=500,
        )
        out.append(ee.data.computeFeatures({"expression": fc, "fileFormat": "PANDAS_DATAFRAME"}))
    res = pd.concat(out, ignore_index=True).set_index("cell_id")["mean"]
    return df["cell_id"].map(res)


def main() -> None:
    earth = pd.read_parquet(DERIVED / "earth_L1.parquet")
    earth = add_astro(earth, EARTH_OBLIQUITY)
    earth["snow_free_frac"] = snow_free_fraction(earth).astype(float)
    earth["lens_id"] = "L2"
    earth.to_parquet(DERIVED / "earth_L2.parquet", index=False)

    targets = pd.read_parquet(DERIVED / "targets_L1.parquet")
    targets = add_astro(targets, MOON_OBLIQUITY)
    targets["lens_id"] = "L2"
    targets.to_parquet(DERIVED / "targets_L2.parquet", index=False)

    print(f"earth_L2: {len(earth)} rows; targets_L2: {len(targets)} rows")
    print(targets[targets.is_reference][["target_id", "lat"] + ASTRO_COLS].to_string(index=False))
    cols = ["name", "lat"] + ASTRO_COLS + ["snow_free_frac"]
    named = earth[earth.sample_role.isin(["control", "seed", "decoy"])]
    print(named[cols].round(3).to_string(index=False))
    print("snow_free_frac missing:", int(earth.snow_free_frac.isna().sum()))


if __name__ == "__main__":
    main()
