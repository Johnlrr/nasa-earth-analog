"""B5 — M1 Earth candidates: footprint list + EMIT median spectra + CRISM parameters.

Footprints (sample_role):
  control / decoy : config/controls.yaml entries with lens_id M1
  seed            : config/seeds_m1.yaml
  rank            : coarse tier on GEE - bare land (ESA WorldCover 60), EMIT coverage (|lat|<=52),
                    ranked by ASTER GED Ninomiya mafic index MI = e12/e13 (higher = more mafic),
                    thinned to >= 100 km apart
  null            : random bare-land footprints drawn INSIDE real EMIT scene footprints (PLAN: not
                    the whole +/-52 belt), used only as the null distribution (>= 50 usable)
Each footprint -> best EMIT scene, masked median spectrum (scripts/emit/emit_gee.py) -> resample ->
crism_params(swir) from the shared library. qa_flag: ok | low_valid (<50 px) | no_scene.

Output: data/derived/earth_M1.parquet, data/derived/earth_M1_spectra.parquet
        (checkpointed: rerun resumes, ``--fresh`` restarts)
"""

from __future__ import annotations

import argparse
import sys
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

import ee
import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
import emit_gee as eg  # noqa: E402

from similitude import discovery, io  # noqa: E402
from similitude.descriptors import spectral as sp  # noqa: E402

DERIVED = io.REPO_ROOT / "data" / "derived"
OUT = DERIVED / "earth_M1.parquet"
OUT_SPEC = DERIVED / "earth_M1_spectra.parquet"
MIN_VALID = 50
SEED = 20261114


def controls_and_seeds() -> list[dict]:
    items = []
    for c in io.load_controls():
        if c["lens_id"] != "M1":
            continue
        role = "decoy" if c["role"] == "decoy" else "control"
        items.append({"cell_id": f"ctl_{c['id']}", "name": c["name"], "lat": c["lat"],
                      "lon": c["lon"], "sample_role": role})
    for s in io.load_yaml(io.CONFIG_DIR / "seeds_m1.yaml")["seeds"]:
        items.append({"cell_id": f"seed_{s['id']}", "name": f"{s['name']} ({s['country']})",
                      "lat": s["lat"], "lon": s["lon"], "sample_role": "seed",
                      "seed_class": s["class"]})
    return items


def _bare_mask() -> ee.Image:
    wc = ee.ImageCollection("ESA/WorldCover/v200").first().select("Map")
    return wc.eq(60)


def rank_cells(n: int = 20, n_sample: int = 3000) -> list[dict]:
    """Coarse tier: most mafic bare land (ASTER GED MI) within EMIT coverage."""
    aster = ee.Image("NASA/ASTER_GED/AG100_003")
    mi = aster.select("emissivity_band12").divide(aster.select("emissivity_band13")).rename("mi")
    ndvi = aster.select("ndvi").multiply(0.01).rename("ndvi")
    img = mi.addBands(ndvi).updateMask(_bare_mask())
    region = ee.Geometry.Rectangle([-180, -52, 180, 52], None, False)
    fc = img.sample(region=region, scale=5000, numPixels=n_sample, seed=SEED, geometries=True,
                    tileScale=4)
    feats = fc.getInfo()["features"]
    rows = [{"lat": f["geometry"]["coordinates"][1], "lon": f["geometry"]["coordinates"][0],
             "mi": f["properties"].get("mi"), "ndvi": f["properties"].get("ndvi")}
            for f in feats]
    df = pd.DataFrame(rows).dropna()
    df = df[df["ndvi"] < 0.15].sort_values("mi", ascending=False)
    picked: list[dict] = []
    for r in df.itertuples():
        if all(discovery.haversine_km(r.lat, r.lon, p["lat"], p["lon"]) >= 100 for p in picked):
            k = len(picked)
            picked.append({"cell_id": f"rank_{k:03d}", "name": f"mafic rank {k}",
                           "lat": round(r.lat, 4), "lon": round(r.lon, 4), "sample_role": "rank",
                           "aster_mi": round(r.mi, 4)})
        if len(picked) >= n:
            break
    return picked


def null_cells(n: int = 70, n_scenes: int = 1400, per_scene: int = 8) -> list[dict]:
    """Random bare-land footprints drawn inside random real EMIT scenes.

    Client-side: random scene footprints -> random points inside each polygon (shapely) ->
    one WorldCover lookup for all points -> first bare point per scene (server-side map over
    scenes exceeded the GEE user memory limit).
    """
    from shapely.geometry import Point, shape

    rng = np.random.default_rng(SEED)
    # random acquisition days (date filters are indexed; sorting 249k scenes is not)
    start = np.datetime64("2022-09-01")
    days = sorted(set(rng.integers(0, 1400, size=n_scenes // 2).tolist()))
    ids, fps = [], []
    for i in range(0, len(days), 40):
        cols = [ee.ImageCollection(eg.COLLECTION)
                .filterDate(str(start + d), str(start + d + 1)).limit(2) for d in days[i:i + 40]]
        merged = cols[0]
        for c in cols[1:]:
            merged = merged.merge(c)
        ids += merged.aggregate_array("system:index").getInfo()
        fps += merged.aggregate_array("system:footprint").getInfo()
    cand = []
    for sid, fp in zip(ids, fps, strict=True):
        poly = shape({"type": "Polygon", "coordinates": [fp["coordinates"]]})
        if not poly.is_valid or poly.area == 0:
            continue
        x0, y0, x1, y1 = poly.bounds
        got = 0
        for _ in range(per_scene * 20):
            x, y = rng.uniform(x0, x1), rng.uniform(y0, y1)
            if abs(y) <= 52 and poly.contains(Point(x, y)):
                cand.append({"scene": sid, "lon": float(x), "lat": float(y)})
                got += 1
                if got >= per_scene:
                    break
    wc = ee.ImageCollection("ESA/WorldCover/v200").first().select("Map").rename("wc")
    rows = []
    for i in range(0, len(cand), 500):
        fc = ee.FeatureCollection([ee.Feature(ee.Geometry.Point([c["lon"], c["lat"]]),
                                              {"k": i + j}) for j, c in enumerate(cand[i:i + 500])])
        res = wc.reduceRegions(fc, ee.Reducer.mode(), scale=100).getInfo()["features"]
        rows += [(f["properties"]["k"], f["properties"].get("mode")) for f in res]
    bare = {k for k, m in rows if m == 60}
    out, used = [], set()
    for k, c in enumerate(cand):
        if k in bare and c["scene"] not in used:
            used.add(c["scene"])
            out.append({"cell_id": f"null_{len(out):03d}", "name": "null sample",
                        "lat": round(c["lat"], 4), "lon": round(c["lon"], 4),
                        "sample_role": "null", "null_scene": c["scene"]})
            if len(out) >= n:
                break
    return out


def extract(cell: dict, km: float, desc: list[str]) -> tuple[dict, dict]:
    r = eg.footprint_spectrum(cell["lat"], cell["lon"], km=km)
    common = sp.resample(r["wl"], r["refl"])
    params = sp.crism_params(common, subset="swir")
    if r["n_scenes"] == 0:
        qa = "no_scene"
    elif r["n_valid"] < MIN_VALID:
        qa = "low_valid"
    else:
        qa = "ok"
    flag, zone = discovery.exclusion_flag(cell["lat"], cell["lon"])
    row = {**cell, "footprint_km": km, "lens_id": "M1", "tier": 2, "L_m": 60.0,
           "source": f"NASA EMIT L2A RFL {r['scene_id']} ({r['date']}) via GEE",
           "qa_flag": qa, "n_valid": r["n_valid"], "n_total": r["n_total"],
           "n_scenes": r["n_scenes"], "scene_id": r["scene_id"], "date": r["date"],
           "in_exclusion_buffer": flag, "exclusion_zone": zone,
           **{d: params[d] for d in desc}, **{k: v for k, v in params.items() if k not in desc}}
    spec = {"cell_id": cell["cell_id"], **{f"r{int(w)}": v for w, v in
                                           zip(sp.COMMON_WL_NM, common, strict=True)}}
    return row, spec


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--fresh", action="store_true")
    ap.add_argument("--n-rank", type=int, default=20)
    ap.add_argument("--n-null", type=int, default=70)
    ap.add_argument("--workers", type=int, default=6)
    args = ap.parse_args()
    eg.init()
    lens = io.load_lenses()["M1"]
    desc = lens["descriptors"]
    km = float(lens["footprint_km"])

    cells_path = DERIVED / "earth_M1_cells.csv"
    if cells_path.exists() and not args.fresh:
        cells = pd.read_csv(cells_path).to_dict("records")
    else:
        cells = controls_and_seeds()
        print(f"controls+seeds: {len(cells)}")
        cells += rank_cells(args.n_rank)
        print(f"+ rank: {len(cells)}")
        cells += null_cells(args.n_null)
        print(f"+ null: {len(cells)}")
        pd.DataFrame(cells).to_csv(cells_path, index=False)

    done_rows, done_spec = [], []
    if OUT.exists() and not args.fresh:
        prev = pd.read_parquet(OUT)
        done_rows = prev.to_dict("records")
        done_spec = pd.read_parquet(OUT_SPEC).to_dict("records")
    done_ids = {r["cell_id"] for r in done_rows}
    todo = [c for c in cells if c["cell_id"] not in done_ids]
    print(f"{len(todo)} footprints to extract ({len(done_ids)} already done)")

    with ThreadPoolExecutor(max_workers=args.workers) as pool:
        futs = {pool.submit(extract, {k: v for k, v in c.items()
                                      if not (isinstance(v, float) and np.isnan(v))}, km, desc):
                c["cell_id"] for c in todo}
        for i, fut in enumerate(as_completed(futs), 1):
            cid = futs[fut]
            try:
                row, spec = fut.result()
            except Exception as e:  # keep going; record failure
                print(f"  ! {cid}: {e}")
                continue
            done_rows.append(row)
            done_spec.append(spec)
            if i % 10 == 0 or i == len(todo):
                pd.DataFrame(done_rows).to_parquet(OUT, index=False)
                pd.DataFrame(done_spec).to_parquet(OUT_SPEC, index=False)
                print(f"  {i}/{len(todo)} checkpoint")
    df = pd.DataFrame(done_rows)
    df.to_parquet(OUT, index=False)
    pd.DataFrame(done_spec).to_parquet(OUT_SPEC, index=False)
    print(df.groupby(["sample_role", "qa_flag"]).size().to_string())


if __name__ == "__main__":
    main()
