"""Discovery: exclusion flags, hidden-analog filter, NMS and candidates.geojson export (B9).

Owner: Linh (B). Only this module FILTERS on ``in_exclusion_buffer`` (PLAN A2/B9); upstream
tables just carry the flag.
"""

from __future__ import annotations

import math
from pathlib import Path

import numpy as np
import pandas as pd

from similitude import io

EARTH_R_KM = 6371.0088

#: Fallback = verbatim copy of Bao's ``config/exclusion_zones.yaml`` (origin/bao/terrain-engine
#: 982b862), used only until that file is merged into this branch, so both sides flag identically.
DEFAULT_EXCLUSION_ZONES: tuple[dict, ...] = (
    {"name": "Antarctica", "lat_max": -60.0},
    {"name": "Atacama", "lat": -24.5, "lon": -69.3, "radius_km": 350},
    {"name": "Iceland", "bbox": [-25.0, 63.0, -13.0, 67.0]},
    {"name": "Hawaii", "bbox": [-161.0, 18.5, -154.0, 22.5]},
    {"name": "Lake Salda", "lat": 37.55, "lon": 29.68, "radius_km": 30},
    {"name": "Pilot Valley", "lat": 40.85, "lon": -113.95, "radius_km": 30},
    {"name": "Lava Beds", "lat": 41.71, "lon": -121.51, "radius_km": 30},
)


def haversine_km(lat1, lon1, lat2, lon2):
    """Great-circle distance in km (numpy-broadcastable)."""
    p1, p2 = np.radians(lat1), np.radians(lat2)
    dphi = p2 - p1
    dlmb = np.radians(np.asarray(lon2) - np.asarray(lon1))
    a = np.sin(dphi / 2) ** 2 + np.cos(p1) * np.cos(p2) * np.sin(dlmb / 2) ** 2
    return 2 * EARTH_R_KM * np.arcsin(np.sqrt(np.clip(a, 0.0, 1.0)))


def load_exclusion_zones() -> list[dict]:
    path = Path(io.CONFIG_DIR) / "exclusion_zones.yaml"
    if path.exists():
        raw = io.load_yaml(path)
        return list(raw["zones"] if isinstance(raw, dict) else raw)
    return [dict(z) for z in DEFAULT_EXCLUSION_ZONES]


def _in_zone(lat: float, lon: float, z: dict) -> bool:
    if "lat_max" in z:
        return lat <= z["lat_max"]
    if "bbox" in z:
        x0, y0, x1, y1 = z["bbox"]
        return x0 <= lon <= x1 and y0 <= lat <= y1
    return bool(haversine_km(lat, lon, z["lat"], z["lon"]) <= z["radius_km"])


def exclusion_flag(lat: float, lon: float, zones=None) -> tuple[bool, str | None]:
    """(in_buffer, zone name), same rules as Bao's scripts/gee/flag_exclusion.py."""
    for z in zones if zones is not None else load_exclusion_zones():
        if _in_zone(lat, lon, z):
            return True, z["name"]
    return False, None


def footprint_box(lat: float, lon: float, km: float) -> tuple[float, float, float, float]:
    """(lon_min, lat_min, lon_max, lat_max) of a square footprint, for display only."""
    dlat = km / 2 / 111.32
    dlon = dlat / max(math.cos(math.radians(lat)), 1e-6)
    return lon - dlon, lat - dlat, lon + dlon, lat + dlat


# ============================================================================================
# Hidden-analog selection (B9)
# ============================================================================================
#: Hidden = high fidelity AND low attention (DESIGN 2.2(6)).
PERCENTILE_MIN = 90.0
SIGMA_MAX_NO_PCT = 1.0  # PLAN B9: lens without percentile -> sigma <= 1
ATTENTION_MAX = 10
CANDIDATE_ROLES = ("rank", "seed")

TEST_HERE = {
    "L1": [{"tech": "Rover / LTV traverse and EVA route tests over matched slope-roughness"
                    " statistics",
            "nasa_gap": "ESDMD #0805 Autonomous Surface Mobility and Navigation"},
           {"tech": "Landing hazard-detection sensor (lidar, camera) trials over real slope"
                    " distributions",
            "nasa_gap": "ESDMD #1101 Lunar Precision Landing and Hazard Avoidance"}],
    "L2": [{"tech": "Low-sun navigation and hazard cameras under long shadows",
            "nasa_gap": "ESDMD #0805 Autonomous Surface Mobility and Navigation"}],
    "M1": [{"tech": "Rover VSWIR spectrometer and mineral-mapping calibration on the same"
                    " alteration minerals", "nasa_gap": None},
           {"tech": "Sampling / caching and biosignature-preservation protocols in"
                    " water-altered rock", "nasa_gap": None}],
    "X1": [{"tech": "1 m ice drill, ground-penetrating radar and neutron spectrometer tests on"
                    " shallow ground ice under dry overburden",
            "nasa_gap": "ESDMD #0603 Water Recovery from Lunar Regolith/Ice"}],
}

PROCESS_TITLE = {
    ("M1", "ophiolite"): "Where olivine-rich mantle rock is altering to serpentine and carbonate",
    ("M1", "basalt"): "Where fresh basalt weathers under a hyper-arid sky",
    ("M1", "evaporite"): "Where evaporating brines lay down salts and sulfates",
    ("M1", "acid_sulfate"): "Where acid waters leave jarosite behind",
    ("M1", "clay"): "Where water-lain clays are exposed",
    ("M1", None): "Where a bare mafic surface carries Mars-like alteration-mineral band depths",
    ("X1", None): "Where ground ice survives under a dry, cold overburden",
    ("L1", None): "Where slopes and roughness match the lunar south-pole landing zones",
    ("L2", None): "Where the Sun skims the horizon over bare ground",
}

DATA_SOURCES = {
    "M1": ["NASA EMIT L2A surface reflectance (NASA/EMIT/L2A/RFL, Google Earth Engine)",
           "MRO CRISM MICA type spectra (PDS MROCR_8001, Viviano-Beck et al. 2014)",
           "ASTER GED AG100 (NASA/JPL), ESA WorldCover"],
    "X1": ["ERA5-Land monthly (Copernicus C3S)", "MODIS MOD11A1 / MOD13A2 (NASA LP DAAC)",
           "TerraClimate", "SWIM subsurface water-ice maps (Mars)",
           "Phoenix / MRO literature (DOIs in targets_X1.parquet)"],
    "L1": ["Copernicus GLO-30 DEM", "NASA PGDA Product 78 (LOLA south-pole DEM)"],
    "L2": ["Copernicus GLO-30 DEM", "NASA PGDA Product 78", "MODIS snow cover"],
}


def gate_mask(earth: pd.DataFrame, lens: dict) -> pd.Series:
    """Cell passes qa and the lens-specific physical gates."""
    m = earth["qa_flag"].eq("ok")
    gates = lens.get("gates", {})
    if "permafrost_min" in gates and "permafrost_flag" in earth:
        m &= earth["permafrost_flag"].fillna(0) >= gates["permafrost_min"]
    if "lat_abs_max" in gates:
        m &= earth["lat"].abs() <= gates["lat_abs_max"]
    return m


def best_target(fid: pd.DataFrame) -> pd.DataFrame:
    """One row per (cell_id, lens_id): the target with the smallest raw d."""
    return (fid.sort_values("d").drop_duplicates(["cell_id", "lens_id"], keep="first")
            .reset_index(drop=True))


def nms(df: pd.DataFrame, footprint_km: float, score: str = "d") -> pd.DataFrame:
    """Greedy non-max suppression: keep best-scoring cells >= footprint_km apart."""
    kept: list[pd.Series] = []
    for _, r in df.sort_values(score).iterrows():
        if all(haversine_km(r["lat"], r["lon"], k["lat"], k["lon"]) >= footprint_km
               for k in kept):
            kept.append(r)
    return pd.DataFrame(kept).reset_index(drop=True) if kept else df.iloc[0:0]


def passes_fidelity(row) -> bool:
    pct = _clean(row.get("percentile"))
    if pct is not None:
        return float(pct) >= PERCENTILE_MIN
    return float(row["sigma"]) <= SIGMA_MAX_NO_PCT


def attention_key(row) -> str:
    """Seeds/controls use their config id; other cells use the cell id."""
    cid = str(row["cell_id"])
    for prefix in ("seed_", "ctl_"):
        if cid.startswith(prefix):
            return cid[len(prefix):]
    return cid


def select_hidden(fid_best: pd.DataFrame, earth: pd.DataFrame, attention: dict, lens: dict,
                  per_lens: int = 5) -> pd.DataFrame:
    """Hidden-analog candidates of one lens.

    Steps: role in rank/seed -> gates -> in_exclusion_buffer False (the ONLY place the flag
    filters) -> fidelity threshold -> attention <= ATTENTION_MAX (unknown kept) -> NMS by
    footprint -> top ``per_lens``.
    """
    e = earth[gate_mask(earth, lens)]
    e = e[e["sample_role"].isin(CANDIDATE_ROLES) & ~e["in_exclusion_buffer"].astype(bool)]
    m = fid_best.merge(e, on="cell_id", how="inner", suffixes=("", "_earth"))
    if m.empty:
        return m
    m = m[m.apply(passes_fidelity, axis=1)]
    if m.empty:
        return m
    m = m.assign(attention_n=[attention.get(attention_key(r)) for _, r in m.iterrows()])
    m = m[m["attention_n"].isna() | (m["attention_n"] <= ATTENTION_MAX)]
    m = nms(m, float(lens["footprint_km"]))
    return m.head(per_lens)


def evidence_status(lens_id: str, role: str) -> str:
    if role == "decoy":
        return "hypothesis"
    if role == "control":
        return "literature-only"
    return "engine-semiquant" if lens_id in io.SEMIQUANT_LENSES else "engine-confirmed"


def cannot_test(lens_id: str) -> list[str]:
    """'Cannot test here' lines from the lens ledger (Transfer Ledger, B7)."""
    lens = io.load_lenses()[lens_id]
    ledger = io.load_yaml(io.REPO_ROOT / lens["ledger"])
    out = []
    for it in ledger["items"]:
        if lens_id not in it.get("applies_to", []):
            continue
        t, e = it.get("target") or {}, it.get("earth") or {}
        if t.get("value") is not None and e.get("value") is not None:
            out.append(f"{it['quantity']}: {t['value']} {t.get('unit', '')} vs Earth "
                       f"{e['value']} {e.get('unit', '')}".strip())
        else:
            out.append(it["quantity"])
    return out


def _clean(v):
    if v is None:
        return None
    try:
        f = float(v)
    except (TypeError, ValueError):
        return v
    return None if math.isnan(f) else f


def _round(v, n: int = 4):
    v = _clean(v)
    return None if v is None else round(float(v), n)


def lens_score(row, lens: dict, z_row=None, target_row=None, earth_row=None) -> dict:
    """Contract ``lens_score`` object from a fidelity row (+ optional descriptor detail)."""
    pct = _clean(row.get("percentile"))
    out = {"target": str(row["target_id"]), "d": round(float(row["d"]), 3),
           "sigma": round(float(row["sigma"]), 3), "sigma_capped": bool(row["sigma_capped"]),
           "percentile": None if pct is None else round(float(pct), 1),
           "limiting_factor": str(row["limiting_factor"]), "no_analog": bool(row["no_analog"]),
           "metric_mode": str(row.get("metric_mode", "diag"))}
    if _clean(row.get("n_null")) is not None:
        out["n_null"] = int(row["n_null"])
    for k in ("d_shadow", "sigma_shadow"):
        if _clean(row.get(k)) is not None:
            out[k] = round(float(row[k]), 3)
    if z_row is not None and target_row is not None and earth_row is not None:
        out["descriptors"] = {
            d: {"earth": _round(earth_row.get(d)), "target": _round(target_row.get(d)),
                "z": _round(z_row.get(f"z_{d}"), 2)}
            for d in lens["descriptors"]}
    return out


def feature(props: dict) -> dict:
    return {"type": "Feature",
            "geometry": {"type": "Point", "coordinates": [props["lon"], props["lat"]]},
            "properties": props}
