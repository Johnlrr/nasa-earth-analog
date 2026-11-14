"""Spectral descriptors: CRISM summary parameters, same code for Mars and Earth spectra (B1).

Owner: Linh (B). Single source of truth for every spectral formula ("same formula, both worlds"):
MICA type spectra (Mars, MRO CRISM) and EMIT L2A surface reflectance (Earth) are both resampled to
``COMMON_WL_NM`` and pass through exactly the same functions below.

Formulas follow Viviano-Beck et al. 2014 (JGR Planets 119:1403, doi:10.1002/2014JE004627), Table 2.
Two constraints force documented substitutions, applied the SAME way to both sides:

* Earth's atmosphere hides 1340-1460 nm and 1790-1960 nm in EMIT (water vapour). Those channels are
  removed from ``COMMON_WL_NM``; any anchor inside them is moved to the nearest clean channel.
* EMIT stops at ~2500 nm (and is noisy above ~2450 nm). The common grid stops at 2490 nm; anchors
  beyond it are moved or the companion band is evaluated against a one-sided (flat) continuum.

Every anchor is read as the mean of three channels (anchor and +/- 10 nm) on the common grid,
skipping channels that fall in a masked gap. ``PARAM_TABLE`` lists original and used anchors.
Band depths compare SHAPE, not absolute level, so ratioed I/F (MICA) and surface reflectance (EMIT)
are comparable only through these parameters and the continuum-removed SAM - never by raw values.
"""

from __future__ import annotations

import numpy as np

# --------------------------------------------------------------------------------------------
# Common wavelength grid
# --------------------------------------------------------------------------------------------
GRID_MIN_NM = 400.0
GRID_MAX_NM = 2490.0
GRID_STEP_NM = 10.0
#: Masked atmospheric gaps (inclusive), removed from the grid on both worlds.
GAPS_NM: tuple[tuple[float, float], ...] = ((1340.0, 1460.0), (1790.0, 1960.0))
#: Half width of the 3-channel anchor window.
KERNEL_HALF_NM = 10.0


def _in_gap(lam: float) -> bool:
    return any(lo <= lam <= hi for lo, hi in GAPS_NM)


_full = np.arange(GRID_MIN_NM, GRID_MAX_NM + GRID_STEP_NM / 2, GRID_STEP_NM)
COMMON_WL_NM: np.ndarray = np.array([w for w in _full if not _in_gap(w)], dtype=float)
COMMON_WL_NM.setflags(write=False)

# --------------------------------------------------------------------------------------------
# Parameter table: original (Viviano-Beck 2014) vs used anchors
# --------------------------------------------------------------------------------------------
# kind: "bd"      -> 1 - R(c) / (a R(s) + b R(lg))                 anchors = (s, c, lg)
#       "shoulder"-> R(c) / (a R(s) + b R(lg))                     anchors = (s, c, lg)
#       "sindex"  -> 1 - (a R(s) + b R(lg)) / R(c)                 anchors = (s, c, lg)
#       "rb"      -> sum w_i (RC_i - R_i)/|RC_i|, RC = line through two continuum anchors
#       "d2300"   -> 1 - (CR2290+CR2320+CR2330)/(CR2120+CR2170+CR2210), CR = R / line(cont)
#       "min"     -> min of two band depths (each "bd" or "bd1" one-sided)
PARAM_TABLE: dict[str, dict] = {
    # ---------------- VNIR (subset "all" only) ----------------
    "BD530": {"vb14": "BD530_2", "kind": "bd", "group": "vnir",
              "original_nm": (440, 530, 614), "used_nm": (440, 530, 614),
              "meaning": "Fe3+ oxides (crystalline ferric)"},
    "SH600": {"vb14": "SH600_2", "kind": "shoulder", "group": "vnir",
              "original_nm": (533, 600, 716), "used_nm": (533, 600, 716),
              "meaning": "select ferric minerals shoulder"},
    "SH770": {"vb14": "SH770", "kind": "shoulder", "group": "vnir",
              "original_nm": (716, 775, 860), "used_nm": (716, 775, 860),
              "meaning": "ferric minerals, esp. jarosite / olivine shoulder"},
    "BD860": {"vb14": "BD860_2", "kind": "bd", "group": "vnir",
              "original_nm": (755, 860, 977), "used_nm": (755, 860, 977),
              "meaning": "hematite"},
    "BD920": {"vb14": "BD920_2", "kind": "bd", "group": "vnir",
              "original_nm": (807, 920, 984), "used_nm": (807, 920, 984),
              "meaning": "Fe-bearing minerals (low-Ca pyroxene, jarosite)"},
    # ---------------- SWIR (subset "swir", M1 default) ----------------
    "OLINDEX": {"vb14": "OLINDEX3", "kind": "rb", "group": "swir",
                "centers_nm": (1210, 1250, 1263, 1276, 1330), "weights": (0.1, 0.1, 0.2, 0.2, 0.4),
                "original_nm": (1750, 1862), "used_nm": (1750, 2150),
                "substitution": "continuum anchor 1862 nm (in 1790-1960 gap) -> 2150 nm",
                "meaning": "olivine (broad 1 um band)"},
    "LCPINDEX": {"vb14": "LCPINDEX2", "kind": "rb", "group": "swir",
                 "centers_nm": (1690, 1750), "weights": (0.5, 0.5),
                 "original_nm": (1560, 2450), "used_nm": (1560, 2450),
                 "original_centers_nm": (1690, 1750, 1810, 1870),
                 "substitution": "band centres 1810, 1870 nm (in gap) dropped; weights"
                                 " 0.2/0.2/0.3/0.3"
                                 " -> 0.5/0.5 on the remaining 1690, 1750 nm",
                 "meaning": "low-Ca pyroxene (2 um band flank only)"},
    "HCPINDEX": {"vb14": "HCPINDEX2", "kind": "rb", "group": "swir",
                 "centers_nm": (2120, 2140, 2230, 2250, 2430, 2460),
                 "weights": (0.1, 0.1, 0.15, 0.3, 0.2, 0.15),
                 "original_nm": (1690, 2530), "used_nm": (1690, 2490),
                 "substitution": "continuum anchor 2530 nm (beyond EMIT) -> 2490 nm",
                 "meaning": "high-Ca pyroxene"},
    "BD1300": {"vb14": "BD1300", "kind": "bd", "group": "swir",
               "original_nm": (1080, 1320, 1750), "used_nm": (1080, 1320, 1750),
               "meaning": "Fe2+ substitution in plagioclase"},
    "BD1750": {"vb14": "BD1750_2", "kind": "bd", "group": "swir",
               "original_nm": (1690, 1750, 1815), "used_nm": (1690, 1750, 1780),
               "substitution": "long anchor 1815 nm (in gap) -> 1780 nm; unreliable on EMIT"
                               " (fill from ~1765 nm), excluded from M1",
               "meaning": "alunite, gypsum"},
    "BD2100": {"vb14": "BD2100_2", "kind": "bd", "group": "swir",
               "original_nm": (1930, 2132, 2250), "used_nm": (1990, 2132, 2250),
               "substitution": "short anchor 1930 nm (in gap) -> 1990 nm (1970 nm still carries"
                               " EMIT water-vapour residual; CRISM CO2 residuals near 2000-2060 nm"
                               " may bias this one parameter)",
               "meaning": "monohydrated sulfates"},
    "BD2165": {"vb14": "BD2165", "kind": "bd", "group": "swir",
               "original_nm": (2120, 2165, 2230), "used_nm": (2120, 2165, 2230),
               "meaning": "kaolinite-group"},
    "BD2190": {"vb14": "BD2190", "kind": "bd", "group": "swir",
               "original_nm": (2120, 2185, 2250), "used_nm": (2120, 2185, 2250),
               "meaning": "beidellite, allophane"},
    "BD2210": {"vb14": "BD2210_2", "kind": "bd", "group": "swir",
               "original_nm": (2165, 2210, 2290), "used_nm": (2165, 2210, 2290),
               "meaning": "Al-OH minerals (montmorillonite, kaolinite)"},
    "BD2230": {"vb14": "BD2230", "kind": "bd", "group": "swir",
               "original_nm": (2210, 2235, 2252), "used_nm": (2210, 2235, 2252),
               "meaning": "hydroxylated ferric sulfate"},
    "BD2250": {"vb14": "BD2250", "kind": "bd", "group": "swir",
               "original_nm": (2120, 2245, 2340), "used_nm": (2120, 2245, 2340),
               "meaning": "opal, Al-OH/Fe-OH"},
    "BD2265": {"vb14": "BD2265", "kind": "bd", "group": "swir",
               "original_nm": (2210, 2265, 2340), "used_nm": (2210, 2265, 2340),
               "meaning": "jarosite, gibbsite"},
    "BD2290": {"vb14": "BD2290", "kind": "bd", "group": "swir",
               "original_nm": (2250, 2290, 2350), "used_nm": (2250, 2290, 2350),
               "meaning": "Mg/Fe-OH minerals, CO2 ice"},
    "D2300": {"vb14": "D2300", "kind": "d2300", "group": "swir",
              "original_nm": (1815, 2530), "used_nm": (1700, 2490),
              "substitution": "continuum anchors 1815 nm (gap; EMIT fill from ~1765 nm) -> 1700 nm,"
                              " 2530 nm (beyond EMIT) -> 2490 nm",
              "meaning": "Mg/Fe-OH (smectite, serpentine) and carbonate 2.3 um drop"},
    "BD2355": {"vb14": "BD2355", "kind": "bd", "group": "swir",
               "original_nm": (2300, 2355, 2450), "used_nm": (2300, 2355, 2450),
               "meaning": "chlorite, prehnite, pumpellyite"},
    "SINDEX": {"vb14": "SINDEX2", "kind": "sindex", "group": "swir",
               "original_nm": (2120, 2290, 2400), "used_nm": (2120, 2290, 2400),
               "meaning": "hydrated sulfates (convexity at 2.29 um)"},
    "MIN2250": {"vb14": "MIN2250", "kind": "min", "group": "swir",
                "parts": (("bd", (2165, 2210, 2290)), ("bd", (2210, 2265, 2340))),
                "original_nm": ((2165, 2210, 2290), (2210, 2265, 2340)),
                "used_nm": ((2165, 2210, 2290), (2210, 2265, 2340)),
                "meaning": "opal / doublet near 2.21-2.26 um"},
    "MIN2295_2480": {"vb14": "MIN2295_2480", "kind": "min", "group": "swir",
                     "parts": (("bd", (2165, 2295, 2364)), ("bd1", (2364, 2480))),
                     "original_nm": ((2165, 2295, 2364), (2364, 2480, 2570)),
                     "used_nm": ((2165, 2295, 2364), (2364, 2480)),
                     "substitution": "BD2480 long anchor 2570 nm (beyond EMIT) dropped: one-sided"
                                     " continuum 1 - R2480/R2364 (assumes flat continuum)",
                     "meaning": "Mg carbonate (2.30 + 2.50 um doublet)"},
    "MIN2345_2537": {"vb14": "MIN2345_2537", "kind": "min", "group": "swir",
                     "parts": (("bd", (2250, 2345, 2430)), ("bd1", (2430, 2490))),
                     "original_nm": ((2250, 2345, 2430), (2430, 2537, 2602)),
                     "used_nm": ((2250, 2345, 2430), (2430, 2490)),
                     "substitution": "BD2537 (beyond EMIT) -> one-sided 1 - R2490/R2430 on the"
                                     " short-wavelength flank of the 2.54 um band",
                     "meaning": "Ca/Fe carbonate (2.34 + 2.54 um doublet)"},
}

#: Computed but NOT used as M1 descriptors: in recent EMIT scenes the -0.01 fill starts ~1765 nm,
#: so the 1.75 um band has no right shoulder on Earth (spike B3, 14/11).
EXCLUDED_FROM_M1: tuple[str, ...] = ("BD1750",)

SWIR_PARAMS: tuple[str, ...] = tuple(k for k, v in PARAM_TABLE.items() if v["group"] == "swir")
VNIR_PARAMS: tuple[str, ...] = tuple(k for k, v in PARAM_TABLE.items() if v["group"] == "vnir")


# --------------------------------------------------------------------------------------------
# Resampling
# --------------------------------------------------------------------------------------------
def _resample_1d(wl: np.ndarray, r: np.ndarray) -> np.ndarray:
    ok = np.isfinite(wl) & np.isfinite(r) & (r > 0.0)  # EMIT bad bands are filled with -0.01
    wl, r = wl[ok], r[ok]
    out = np.full(COMMON_WL_NM.shape, np.nan)
    if wl.size == 0:
        return out
    order = np.argsort(wl)
    wl, r = wl[order], r[order]
    half = GRID_STEP_NM / 2
    for i, lam in enumerate(COMMON_WL_NM):
        in_bin = (wl >= lam - half) & (wl < lam + half)
        if in_bin.any():
            out[i] = float(np.mean(r[in_bin]))
            continue
        j = int(np.searchsorted(wl, lam))
        if 0 < j < wl.size and (wl[j] - wl[j - 1]) <= 1.5 * GRID_STEP_NM:
            t = (lam - wl[j - 1]) / (wl[j] - wl[j - 1])
            out[i] = float(r[j - 1] + t * (r[j] - r[j - 1]))
    return out


def resample(wl_nm: np.ndarray, refl: np.ndarray) -> np.ndarray:
    """Resample a spectrum (or stack of spectra, bands on the last axis) onto ``COMMON_WL_NM``.

    Samples inside a +/-5 nm bin are averaged (EMIT ~7.4 nm, CRISM ~6.55 nm sampling); empty bins
    are linearly interpolated only between samples <= 15 nm apart. Non-finite and non-positive
    values are ignored (EMIT fills bad water-vapour bands with -0.01, PDS uses large constants).
    Points outside the input range stay NaN (no extrapolation).
    """
    wl = np.asarray(wl_nm, dtype=float)
    r = np.asarray(refl, dtype=float)
    if r.ndim == 1:
        return _resample_1d(wl, r)
    flat = r.reshape(-1, r.shape[-1])
    out = np.stack([_resample_1d(wl, row) for row in flat])
    return out.reshape(*r.shape[:-1], COMMON_WL_NM.size)


# --------------------------------------------------------------------------------------------
# Anchor reading
# --------------------------------------------------------------------------------------------
def _point(refl: np.ndarray, lam: float) -> float:
    """Reflectance at ``lam`` on the common grid; NaN if outside or in/next to a masked gap."""
    if lam < GRID_MIN_NM - 1e-9 or lam > GRID_MAX_NM + 1e-9 or _in_gap(lam):
        return np.nan
    j = int(np.searchsorted(COMMON_WL_NM, lam))
    if j < COMMON_WL_NM.size and abs(COMMON_WL_NM[j] - lam) < 1e-9:
        return float(refl[j])
    if j == 0 or j >= COMMON_WL_NM.size:
        return np.nan
    lo, hi = COMMON_WL_NM[j - 1], COMMON_WL_NM[j]
    if hi - lo > GRID_STEP_NM + 1e-9:  # neighbours straddle a gap
        return np.nan
    t = (lam - lo) / (hi - lo)
    return float(refl[j - 1] + t * (refl[j] - refl[j - 1]))


def anchor(refl: np.ndarray, lam: float) -> float:
    """Mean of the 3-channel window (lam - 10, lam, lam + 10 nm), skipping masked points."""
    vals = [_point(refl, lam + d) for d in (-KERNEL_HALF_NM, 0.0, KERNEL_HALF_NM)]
    vals = [v for v in vals if np.isfinite(v)]
    return float(np.mean(vals)) if vals else np.nan


def _lin(s: float, c: float, lg: float) -> tuple[float, float]:
    b = (c - s) / (lg - s)
    return 1.0 - b, b


def _bd(refl, s, c, lg) -> float:
    a, b = _lin(s, c, lg)
    cont = a * anchor(refl, s) + b * anchor(refl, lg)
    return 1.0 - anchor(refl, c) / cont


def _bd1(refl, s, c) -> float:
    """One-sided band depth against a flat continuum at ``s``."""
    return 1.0 - anchor(refl, c) / anchor(refl, s)


def _line(refl, s, lg):
    rs, rl = anchor(refl, s), anchor(refl, lg)
    slope = (rl - rs) / (lg - s)
    return lambda lam: rs + slope * (lam - s)


def _param(refl: np.ndarray, name: str) -> float:
    p = PARAM_TABLE[name]
    kind = p["kind"]
    if kind == "bd":
        return _bd(refl, *p["used_nm"])
    if kind == "shoulder":
        s, c, lg = p["used_nm"]
        a, b = _lin(s, c, lg)
        return anchor(refl, c) / (a * anchor(refl, s) + b * anchor(refl, lg))
    if kind == "sindex":
        s, c, lg = p["used_nm"]
        a, b = _lin(s, c, lg)
        return 1.0 - (a * anchor(refl, s) + b * anchor(refl, lg)) / anchor(refl, c)
    if kind == "rb":
        cont = _line(refl, *p["used_nm"])
        total = 0.0
        for lam, w in zip(p["centers_nm"], p["weights"], strict=True):
            rc = cont(lam)
            total += w * (rc - anchor(refl, lam)) / abs(rc)
        return total
    if kind == "d2300":
        cont = _line(refl, *p["used_nm"])

        def cr(lam):
            return anchor(refl, lam) / cont(lam)

        return 1.0 - (cr(2290) + cr(2320) + cr(2330)) / (cr(2120) + cr(2170) + cr(2210))
    if kind == "min":
        vals = []
        for part_kind, nm in p["parts"]:
            vals.append(_bd(refl, *nm) if part_kind == "bd" else _bd1(refl, *nm))
        return float(min(vals))
    raise ValueError(f"unknown kind {kind}")


def crism_params(refl: np.ndarray, subset: str = "swir") -> dict[str, float]:
    """CRISM summary parameters of one spectrum already on ``COMMON_WL_NM``.

    ``subset="swir"`` (M1 default): parameters whose anchors lie in 1000-2490 nm.
    ``subset="all"``: SWIR + VNIR (use only when the target spectrum has VNIR).
    """
    r = np.asarray(refl, dtype=float)
    if r.shape != COMMON_WL_NM.shape:
        raise ValueError(
            f"refl must be on COMMON_WL_NM ({COMMON_WL_NM.size} values), got {r.shape}"
        )
    if subset == "swir":
        names = SWIR_PARAMS
    elif subset == "all":
        names = VNIR_PARAMS + SWIR_PARAMS
    else:
        raise ValueError("subset must be 'swir' or 'all'")
    with np.errstate(divide="ignore", invalid="ignore"):
        return {n: float(_param(r, n)) for n in names}


# --------------------------------------------------------------------------------------------
# Spectral angle after continuum removal
# --------------------------------------------------------------------------------------------
def continuum_removed(wl: np.ndarray, r: np.ndarray) -> np.ndarray:
    """Divide by the upper convex hull (standard continuum removal)."""
    hull: list[int] = []
    for i in range(wl.size):
        while len(hull) >= 2:
            x1, y1 = wl[hull[-2]], r[hull[-2]]
            x2, y2 = wl[hull[-1]], r[hull[-1]]
            # remove hull[-1] if it lies below the segment hull[-2] -> i
            if (x2 - x1) * (r[i] - y1) - (y2 - y1) * (wl[i] - x1) >= 0:
                hull.pop()
            else:
                break
        hull.append(i)
    cont = np.interp(wl, wl[hull], r[hull])
    return r / cont


def sam(a: np.ndarray, b: np.ndarray, window_nm: tuple[float, float] = (2100.0, 2490.0)) -> float:
    """Spectral angle (radians) between two common-grid spectra after continuum removal.

    Starts at 2100 nm to avoid CRISM CO2 residuals (~1950-2080 nm). Scale-invariant.
    """
    a = np.asarray(a, dtype=float)
    b = np.asarray(b, dtype=float)
    sel = (COMMON_WL_NM >= window_nm[0]) & (COMMON_WL_NM <= window_nm[1])
    sel &= np.isfinite(a) & np.isfinite(b) & (a > 0) & (b > 0)
    if sel.sum() < 3:
        return np.nan
    wl = COMMON_WL_NM[sel]
    ca, cb = continuum_removed(wl, a[sel]), continuum_removed(wl, b[sel])
    cos = float(np.dot(ca, cb) / (np.linalg.norm(ca) * np.linalg.norm(cb)))
    return float(np.arccos(np.clip(cos, -1.0, 1.0)))
