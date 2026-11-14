"""Ice-configuration descriptors for lens X1 (semi-quantitative, B6). Owner: Linh (B).

X1 compares a CONFIGURATION, not absolute temperatures: "ground ice within drill reach, under a
dry, cold overburden, with little thaw activity". Absolute ice temperature never matches (Mars
mid-latitude ground ~210 K vs Earth permafrost near 270 K) and is reported in the Transfer Ledger.
The same function encodes Earth cells (MODIS LST, TerraClimate) and Mars targets (SWIM, landers):

    permafrost_flag  1 if MAAT <= -2 C, 0 if MAAT >= 0 C, linear in between
    ice_depth_ratio  depth to ice / DRILL_REACH_M (1 m drill of a Mars Life Explorer-class mission),
                     capped at ICE_RATIO_CAP; no permafrost -> cap (ice out of reach)
    aridity_p_pet    precipitation / potential evapotranspiration, capped at 2
    ft_cycles_yr     diurnal freeze-thaw cycles per year at the surface (liquid water activity)

Every output is bounded, so Sigma-based scoring never sees unbounded values.
"""

from __future__ import annotations

import math

DRILL_REACH_M = 1.0
ICE_RATIO_CAP = 3.0
ARIDITY_CAP = 2.0
#: Stefan-equation coefficient for dry mineral soil, m / (C day)^0.5 (thaw depth = E sqrt(TDD)).
STEFAN_E = 0.03


#: PET floor (mm/yr) for the aridity ratio. Plain P/PET breaks in polar deserts (PET -> 0 makes a
#: 150 mm/yr polar desert look "humid"); the floor keeps absolute dryness visible. Mars: P = 0.
PET_FLOOR_MM = 500.0


def aridity_index(p_mm: float, pet_mm: float, pet_floor_mm: float = PET_FLOOR_MM) -> float:
    """Precipitation / max(PET, floor). Used for Earth cells; Mars targets have P = 0."""
    if p_mm is None or pet_mm is None or not (math.isfinite(p_mm) and math.isfinite(pet_mm)):
        return math.nan
    return max(p_mm, 0.0) / max(pet_mm, pet_floor_mm)


def stefan_active_layer(thawing_degree_days: float, e: float = STEFAN_E) -> float:
    """Approximate thaw (active-layer) depth in metres from thawing degree-days (C day)."""
    if thawing_degree_days is None or not math.isfinite(thawing_degree_days):
        return math.nan
    return e * math.sqrt(max(thawing_degree_days, 0.0))


def _num(x) -> float:
    return float(x) if x is not None and math.isfinite(float(x)) else math.nan


def ice_config(maat_c, active_layer_m, aridity_p_pet, freeze_thaw_per_yr) -> dict[str, float]:
    """Encode the ice-under-dry-overburden configuration (keys = X1 descriptors)."""
    maat = _num(maat_c)
    alt = _num(active_layer_m)
    ar = _num(aridity_p_pet)
    ft = _num(freeze_thaw_per_yr)

    if math.isnan(maat):
        flag = math.nan
    else:
        flag = min(max(-maat / 2.0, 0.0), 1.0)

    if math.isnan(flag):
        ratio = math.nan
    elif flag == 0.0:
        ratio = ICE_RATIO_CAP
    elif math.isnan(alt):
        ratio = math.nan
    else:
        ratio = min(max(alt, 0.0) / DRILL_REACH_M, ICE_RATIO_CAP)

    return {
        "permafrost_flag": flag,
        "ice_depth_ratio": ratio,
        "aridity_p_pet": math.nan if math.isnan(ar) else min(max(ar, 0.0), ARIDITY_CAP),
        "ft_cycles_yr": math.nan if math.isnan(ft) else max(ft, 0.0),
    }
