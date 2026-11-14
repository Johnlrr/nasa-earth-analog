"""Flag cells inside exclusion zones (PLAN A2). Adds ``in_exclusion_buffer``; never drops rows.

Usage: python scripts/gee/flag_exclusion.py [in.csv] [out.csv]
(defaults: data/derived/tier1_terrain.csv in place)
"""

from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd
import yaml

ROOT = Path(__file__).resolve().parents[2]
ZONES = ROOT / "config" / "exclusion_zones.yaml"
EARTH_R_KM = 6371.0


def load_zones(path: Path = ZONES) -> list[dict]:
    return yaml.safe_load(path.read_text(encoding="utf-8"))["zones"]


def _haversine_km(lat1, lon1, lat2, lon2):
    p1, p2 = np.radians(lat1), np.radians(lat2)
    dphi = p2 - p1
    dlmb = np.radians(np.asarray(lon2) - np.asarray(lon1))
    a = np.sin(dphi / 2) ** 2 + np.cos(p1) * np.cos(p2) * np.sin(dlmb / 2) ** 2
    return 2 * EARTH_R_KM * np.arcsin(np.sqrt(a))


def flag(df: pd.DataFrame, zones: list[dict]) -> pd.DataFrame:
    """Return a copy of ``df`` with boolean ``in_exclusion_buffer`` and ``exclusion_zone``."""
    out = df.copy()
    lat = out["lat"].to_numpy(dtype=float)
    lon = out["lon"].to_numpy(dtype=float)
    hit = np.zeros(len(out), dtype=bool)
    name = np.array([""] * len(out), dtype=object)
    for z in zones:
        if "lat_max" in z:
            m = lat <= z["lat_max"]
        elif "bbox" in z:
            x0, y0, x1, y1 = z["bbox"]
            m = (lon >= x0) & (lon <= x1) & (lat >= y0) & (lat <= y1)
        else:
            m = _haversine_km(lat, lon, z["lat"], z["lon"]) <= z["radius_km"]
        name[m & ~hit] = z["name"]
        hit |= m
    out["in_exclusion_buffer"] = hit
    out["exclusion_zone"] = name
    return out


def main() -> None:
    src = Path(sys.argv[1]) if len(sys.argv) > 1 else ROOT / "data/derived/tier1_terrain.csv"
    dst = Path(sys.argv[2]) if len(sys.argv) > 2 else src
    df = flag(pd.read_csv(src), load_zones())
    df.to_csv(dst, index=False)
    print(f"{int(df.in_exclusion_buffer.sum())} / {len(df)} cells flagged -> {dst}")


if __name__ == "__main__":
    main()
