"""B6 — X1 (ice under dry overburden), semi-quantitative, 10 km.

Earth side (GEE, one composite image, sampled at points):
  maat_c     ERA5-Land soil temperature level 3 (28-100 cm), mean 2014-2023 (permafrost proxy;
             MODIS clear-sky LST was tried first and biased high plateaus warm by 2-18 C)
  tdd        thawing degree-days of ERA5-Land soil level 1 (0-7 cm), monthly means x days, per year
  lst_maat_c MODIS MOD11A2 clear-sky (Day+Night)/2, 2023, kept for reference only
  ft_yr      diurnal freeze-thaw days/yr from MOD11A1 2023 (Day > 0 C and Night < 0 C), rescaled
             to 365 valid days
  p_mm, pet_mm TerraClimate 2014-2023 annual means -> ice.aridity_index (PET floor 500 mm/yr)
  ndvi_p90   MOD13A2 2023 90th percentile NDVI (gate: bare / polar desert)
  active layer = Stefan approximation from TDD (descriptors/ice.py)
Mars side: config/targets.yaml (Arcadia, SWIM) as reference + literature-coded Mars population.
Descriptors via similitude.descriptors.ice.ice_config for BOTH sides.

Footprints: control/decoy (controls.yaml X1), seed (seeds_x1.yaml), rank (cold land, MAAT < 1 C,
random 10 km sample), null (random land sample, |lat| < 80, stratified by latitude band).
Output: data/derived/earth_X1.parquet, data/derived/targets_X1.parquet
"""

from __future__ import annotations

import argparse
import os

import ee
import numpy as np
import pandas as pd

from similitude import discovery, io
from similitude.descriptors import ice

DERIVED = io.REPO_ROOT / "data" / "derived"
SCALE = 10000
SEED = 20261114
YEAR = ("2023-01-01", "2024-01-01")
SOURCE = ("ERA5-Land monthly 2014-2023, MODIS MOD11A1/MOD13A2 (2023), TerraClimate 2014-2023,"
          " via GEE")

#: Mars population for X1 Sigma (semi-quantitative, literature-coded; MAAT ~ Mars surface mean).
MARS_POPULATION = [
    # id, lat, lon, maat_c, ice_depth_m, note, source
    ("phoenix_site", 68.22, -125.75, -70.0, 0.05,
     "Ice table 5-18 cm under dry soil (Phoenix lander)", "https://doi.org/10.1126/science.1172339"),
    ("ice_exposing_craters_55n", 55.6, 150.6, -65.0, 0.5,
     "New impact craters exposing ice within ~1 m at 43-56 N",
     "https://doi.org/10.1126/science.1175307"),
    ("deuteronilus_lda", 40.0, 25.0, -60.0, 3.0,
     "Debris-covered glacial ice, overburden >~1 m (SHARAD)", "https://doi.org/10.1029/2008GL036379"),
    ("meridiani_equatorial", -1.95, -5.53, -60.0, 3.0,
     "No near-surface ice at the equator (ice unstable)", "https://swim.psi.edu/"),
    ("hellas_lda", -40.0, 105.0, -60.0, 3.0,
     "Lobate debris aprons: ice under metres of debris", "https://doi.org/10.1029/2008GL036379"),
]


def composite() -> ee.Image:
    def k_to_c(img, band):
        return img.select(band).multiply(0.02).subtract(273.15)

    a2 = ee.ImageCollection("MODIS/061/MOD11A2").filterDate(*YEAR)

    def tmean(img):
        return k_to_c(img, "LST_Day_1km").add(k_to_c(img, "LST_Night_1km")).divide(2).rename("t")

    lst_maat = a2.map(tmean).mean().rename("lst_maat_c")

    era = ee.ImageCollection("ECMWF/ERA5_LAND/MONTHLY_AGGR").filterDate("2014-01-01", "2024-01-01")
    maat = era.select("soil_temperature_level_3").mean().subtract(273.15).rename("maat_c")
    tdd = (era.select("soil_temperature_level_1")
           .map(lambda i: i.subtract(273.15).max(0).multiply(30.44)).sum().divide(10)
           .rename("tdd"))

    a1 = ee.ImageCollection("MODIS/061/MOD11A1").filterDate(*YEAR)

    def ft(img):
        day = k_to_c(img, "LST_Day_1km")
        night = k_to_c(img, "LST_Night_1km")
        both = day.mask().And(night.mask())
        return (day.gt(0).And(night.lt(0)).unmask(0).updateMask(both).rename("ft")
                .addBands(both.rename("nv")))

    f = a1.map(ft)
    ft_yr = (f.select("ft").sum().divide(f.select("nv").sum().max(1)).multiply(365)
             .rename("ft_yr"))

    tc = ee.ImageCollection("IDAHO_EPSCOR/TERRACLIMATE").filterDate("2014-01-01", "2024-01-01")
    p_mm = tc.select("pr").sum().divide(10).rename("p_mm")
    pet_mm = tc.select("pet").sum().multiply(0.1).divide(10).rename("pet_mm")
    ndvi = (ee.ImageCollection("MODIS/061/MOD13A2").filterDate(*YEAR).select("NDVI")
            .reduce(ee.Reducer.percentile([90])).multiply(0.0001).rename("ndvi_p90"))
    return maat.addBands([tdd, ft_yr, p_mm, pet_mm, ndvi, lst_maat])


def sample_points(img: ee.Image, points: list[dict]) -> pd.DataFrame:
    rows = []
    for i in range(0, len(points), 150):
        chunk = points[i:i + 150]
        fc = ee.FeatureCollection([
            ee.Feature(ee.Geometry.Point([p["lon"], p["lat"]]), {"cell_id": p["cell_id"]})
            for p in chunk])
        res = img.reduceRegions(fc, ee.Reducer.mean(), scale=SCALE, tileScale=4).getInfo()
        for f in res["features"]:
            rows.append(f["properties"])
    return pd.DataFrame(rows)


def random_points(img: ee.Image, region: ee.Geometry, n: int, mask: ee.Image,
                  prefix: str, role: str, seed: int) -> list[dict]:
    fc = mask.selfMask().rename("m").sample(region=region, scale=SCALE, numPixels=n * 4,
                                            seed=seed, geometries=True, tileScale=4).limit(n)
    out = []
    for f in fc.getInfo()["features"]:
        lon, lat = f["geometry"]["coordinates"]
        out.append({"cell_id": f"{prefix}_{len(out):04d}", "name": f"{role} sample",
                    "lat": round(lat, 4), "lon": round(lon, 4), "sample_role": role})
    return out


def earth_points(img: ee.Image, n_rank: int, n_null: int) -> list[dict]:
    pts = []
    for c in io.load_controls():
        if c["lens_id"] == "X1":
            pts.append({"cell_id": f"ctl_{c['id']}", "name": c["name"], "lat": c["lat"],
                        "lon": c["lon"],
                        "sample_role": "decoy" if c["role"] == "decoy" else "control"})
    for s in io.load_yaml(io.CONFIG_DIR / "seeds_x1.yaml")["seeds"]:
        pts.append({"cell_id": f"seed_{s['id']}", "name": f"{s['name']} ({s['country']})",
                    "lat": s["lat"], "lon": s["lon"], "sample_role": "seed"})
    land = ee.Image("MODIS/061/MCD12Q1/2022_01_01").select("LC_Type1").neq(17)
    cold = img.select("maat_c").lt(1).And(land)
    world = ee.Geometry.Rectangle([-180, -60, 180, 84], None, False)
    pts += random_points(img, world, n_rank, cold, "rank", "rank", SEED)
    # null: stratified by latitude band so the polar band is not swamped by the tropics
    bands = [(-60, -30), (-30, 0), (0, 30), (30, 50), (50, 65), (65, 84)]
    per = max(n_null // len(bands), 10)
    for j, (lo, hi) in enumerate(bands):
        reg = ee.Geometry.Rectangle([-180, lo, 180, hi], None, False)
        got = random_points(img, reg, per, land, f"null{j}", "null", SEED + j)
        pts += got
    return pts


def mars_targets() -> pd.DataFrame:
    t = io.load_targets()["arcadia_planitia"]
    cfg = t["configuration"]
    rows = [{"target_id": "arcadia_planitia", "body": "mars", "lens_id": "X1",
             "footprint_id": "arcadia_planitia", "is_reference": True, "lat": t["lat"],
             "lon": t["lon"], "L_m": float(SCALE), "source": t["source_note"],
             **ice.ice_config(cfg["maat_c"], cfg["ice_depth_m"], cfg["aridity_p_pet"],
                              cfg["freeze_thaw_per_yr"])}]
    for pid, lat, lon, maat, depth, note, src in MARS_POPULATION:
        rows.append({"target_id": "mars_ice_population", "body": "mars", "lens_id": "X1",
                     "footprint_id": pid, "is_reference": False, "lat": lat, "lon": lon,
                     "L_m": float(SCALE), "source": f"{note}; {src}",
                     **ice.ice_config(maat, depth, 0.0, 0)})
    return pd.DataFrame(rows)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--n-rank", type=int, default=1200)
    ap.add_argument("--n-null", type=int, default=300)
    args = ap.parse_args()
    ee.Initialize(project=os.environ.get("EE_PROJECT", "nasa-hackthon-kl"))
    DERIVED.mkdir(parents=True, exist_ok=True)
    mars_targets().to_parquet(DERIVED / "targets_X1.parquet", index=False)

    img = composite()
    pts = earth_points(img, args.n_rank, args.n_null)
    roles = pd.Series([p["sample_role"] for p in pts]).value_counts().to_dict()
    print(f"{len(pts)} points:", roles)
    vals = sample_points(img, pts)
    df = pd.DataFrame(pts).merge(vals, on="cell_id", how="left")

    desc = io.load_lenses()["X1"]["descriptors"]
    enc = []
    for r in df.itertuples():
        alt = ice.stefan_active_layer(getattr(r, "tdd", np.nan))
        ar = ice.aridity_index(getattr(r, "p_mm", np.nan), getattr(r, "pet_mm", np.nan))
        enc.append(ice.ice_config(getattr(r, "maat_c", np.nan), alt, ar,
                                  getattr(r, "ft_yr", np.nan)))
    df = pd.concat([df, pd.DataFrame(enc)[desc]], axis=1)
    df["active_layer_m"] = [ice.stefan_active_layer(x) for x in df.get("tdd", np.nan)]
    flags = [discovery.exclusion_flag(a, b) for a, b in zip(df["lat"], df["lon"], strict=True)]
    df["in_exclusion_buffer"] = [f[0] for f in flags]
    df["exclusion_zone"] = [f[1] for f in flags]
    df["footprint_km"] = 10.0
    df["lens_id"] = "X1"
    df["tier"] = 1
    df["L_m"] = float(SCALE)
    df["source"] = SOURCE
    complete = df[desc].notna().all(axis=1)
    vegetated = df.get("ndvi_p90", pd.Series(np.nan, index=df.index)) >= 0.3  # NaN -> not veg
    df["qa_flag"] = np.where(~complete, "missing_data", np.where(vegetated, "vegetated", "ok"))
    df.to_parquet(DERIVED / "earth_X1.parquet", index=False)
    print(df.groupby(["sample_role", "qa_flag"]).size().to_string())
    show = df[df["sample_role"].isin(["control", "decoy", "seed"])]
    cols = ["cell_id", "maat_c", "lst_maat_c", "tdd", "ft_yr", "p_mm", "pet_mm", "ndvi_p90", *desc,
            "qa_flag"]
    print(show[cols].round(3).to_string(index=False))


if __name__ == "__main__":
    main()
