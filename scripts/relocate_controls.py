"""A14: apply the relocation rule to pre-registered points that sit on lakes.

Valid-land mask from GEE: ESA WorldCover v200 != 80 (permanent water) AND
Copernicus GLO-30 DEM present, sampled at 60 m on a local UTM grid of
``SEARCH_KM`` around each point. Output: data/derived/relocations.csv with the
original and the relocated coordinate (both are reported downstream).

Usage:
  .venv/bin/python scripts/relocate_controls.py            # compute relocations.csv
  .venv/bin/python scripts/relocate_controls.py --apply-l1 # add *_reloc rows to earth_L1 and
                                                           # report L1 fidelity before/after
"""

from __future__ import annotations

import os
import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from similitude.relocate import relocate  # noqa: E402

RES_M = 60.0
SEARCH_KM = 40.0
OUT = ROOT / "data" / "derived" / "relocations.csv"
# Interface for B13 (Linh, scripts/emit/pixel_m1.py): point_id, lat, lon, reason
OUT_POINTS = ROOT / "data" / "derived" / "relocated_points.csv"

# (point id, lens, lat, lon, footprint_km). Coordinates are the pre-registered ones.
POINTS = [
    ("SEED_Karakul", "L1", 39.0, 73.5, 4),
    ("CTRL_Mistastin", "L1", 55.88, -63.31, 4),
    ("lake_salda", "M1", 37.55, 29.68, 5),
]


def _utm_epsg(lat: float, lon: float) -> int:
    zone = int((lon + 180) // 6) + 1
    return (32600 if lat >= 0 else 32700) + zone


def _mask(ee, lat: float, lon: float) -> np.ndarray:
    from pyproj import Transformer

    epsg = _utm_epsg(lat, lon)
    x0, y0 = Transformer.from_crs(4326, epsg, always_xy=True).transform(lon, lat)
    n = int(round(SEARCH_KM * 1000 / RES_M)) | 1  # odd -> the point is the centre pixel
    half = n * RES_M / 2
    wc = ee.ImageCollection("ESA/WorldCover/v200").first().select("Map")
    dem = ee.ImageCollection("COPERNICUS/DEM/GLO30").select("DEM").mosaic()
    valid = wc.neq(80).And(dem.mask().gt(0)).unmask(0).rename("valid").toByte()
    req = {
        "expression": valid,
        "fileFormat": "NUMPY_NDARRAY",
        "grid": {
            "dimensions": {"width": n, "height": n},
            "affineTransform": {
                "scaleX": RES_M, "shearX": 0, "translateX": x0 - half,
                "shearY": 0, "scaleY": -RES_M, "translateY": y0 + half,
            },
            "crsCode": f"EPSG:{epsg}",
        },
    }
    arr = ee.data.computePixels(req)
    return np.asarray(arr["valid"]).astype(bool), epsg, x0, y0


def apply_l1() -> None:
    """Add relocated L1 points as ``<id>_reloc`` rows (original rows are kept) and
    report fidelity vs the primary target for both coordinates."""
    sys.path.insert(0, str(ROOT / "scripts"))
    from build_earth_L1 import _process_row
    from run_all import load

    from similitude import io
    from similitude.fidelity import score_lens

    rel = pd.read_csv(OUT)
    path = ROOT / "data" / "derived" / "earth_L1.parquet"
    earth = pd.read_parquet(path)
    earth = earth[~earth["cell_id"].str.endswith("_reloc")]
    new = []
    for r in rel[(rel.lens_id == "L1") & rel.moved].itertuples():
        orig = earth[earth.cell_id == r.point_id].iloc[0].to_dict()
        row = _process_row({
            "cell_id": f"{r.point_id}_reloc", "lat": r.lat_new, "lon": r.lon_new,
            "sample_role": orig["sample_role"], "source": f"A14 relocation of {r.point_id}",
            "name": f"{orig.get('name', '')} (relocated)", "expected": orig.get("expected", ""),
        })
        new.append({**{k: orig.get(k) for k in earth.columns}, **row})
    earth = pd.concat([earth, pd.DataFrame(new)], ignore_index=True)
    earth.to_parquet(path, index=False)

    lens = io.load_lenses()["L1"]
    e, t = load("L1")
    fid = score_lens(e, t, lens)
    fid = fid[fid.target_id == lens["primary_target"]].set_index("cell_id")
    for col in ("d", "sigma", "percentile"):
        rel[f"{col}_orig"] = rel.point_id.map(fid[col])
        rel[f"{col}_new"] = (rel.point_id + "_reloc").map(fid[col])
    rel.to_csv(OUT, index=False)
    cols = ["point_id", "shift_km", "d_orig", "d_new", "sigma_orig", "sigma_new",
            "percentile_orig", "percentile_new"]
    print(rel[rel.lens_id == "L1"][cols].round(2).to_string(index=False))


def main() -> None:
    if "--points-only" in sys.argv:
        write_points(pd.read_csv(OUT))
        return
    if "--apply-l1" in sys.argv:
        apply_l1()
        return
    import ee
    from pyproj import Transformer

    ee.Initialize(project=os.environ.get("EE_PROJECT", "similitude-ee"))
    rows = []
    for pid, lens, lat, lon, fp_km in POINTS:
        mask, epsg, x0, y0 = _mask(ee, lat, lon)
        fp_px = int(round(fp_km * 1000 / RES_M))
        r = relocate(mask, footprint_px=fp_px, res_m=RES_M)
        x1, y1 = x0 + r.d_col * RES_M, y0 - r.d_row * RES_M
        lon1, lat1 = Transformer.from_crs(epsg, 4326, always_xy=True).transform(x1, y1)
        rows.append({
            "point_id": pid, "lens_id": lens, "footprint_km": fp_km,
            "lat_orig": lat, "lon_orig": lon,
            "lat_new": round(lat1, 5), "lon_new": round(lon1, 5),
            "moved": r.moved, "found": r.found,
            "valid_frac_orig": round(r.frac_before, 3),
            "valid_frac_new": round(r.frac_after, 3),
            "shift_km": round(r.shift_m / 1000, 2),
            "rule": "valid=WorldCover!=80 & GLO30 present; move if <0.5 to nearest footprint >=0.5",
        })
        print(f"{pid:16s} frac {r.frac_before:.2f} -> {r.frac_after:.2f}  "
              f"shift {r.shift_m / 1000:.2f} km  ({lat1:.4f}, {lon1:.4f})  found={r.found}")
    pd.DataFrame(rows).to_csv(OUT, index=False)
    write_points(pd.DataFrame(rows))
    print(f"wrote {OUT.relative_to(ROOT)}, {OUT_POINTS.relative_to(ROOT)}")


def write_points(rel: pd.DataFrame) -> None:
    moved = rel[rel["moved"].astype(bool)]
    pd.DataFrame({
        "point_id": moved["point_id"],
        "lat": moved["lat_new"],
        "lon": moved["lon_new"],
        "reason": [
            f"A14 rule: valid land {a:.2f} -> {b:.2f} of footprint, moved {k:.2f} km "
            "(WorldCover!=80 & GLO-30 present; nearest footprint >= 0.5)"
            for a, b, k in zip(moved["valid_frac_orig"], moved["valid_frac_new"], moved["shift_km"])
        ],
    }).to_csv(OUT_POINTS, index=False)


if __name__ == "__main__":
    main()
