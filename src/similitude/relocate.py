"""Footprint relocation rule (PLAN A14, review G1 1.2).

A pre-registered point whose footprint is mostly water (or has no DEM) does not
measure the terrain it names: Lake Salda, Karakul and Mistastin were given as
lake-centre coordinates. One rule, applied to every point, never chosen by hand:

    if the footprint has < ``threshold`` valid land, move the centre to the
    nearest position whose footprint has >= ``threshold`` valid land.

"Valid land" = not permanent water (ESA WorldCover class 80) and DEM present.
The rule works on a boolean mask on a regular grid so it is testable without
network access; ``scripts/relocate_controls.py`` builds the mask from GEE.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
from scipy.ndimage import uniform_filter

THRESHOLD = 0.5


@dataclass
class Relocation:
    moved: bool
    frac_before: float
    frac_after: float
    d_row: int  # pixel offset of the new centre (rows grow southwards)
    d_col: int  # pixel offset (cols grow eastwards)
    shift_m: float
    found: bool  # False when no position in the search area reaches the threshold


def footprint_fraction(mask: np.ndarray, footprint_px: int) -> np.ndarray:
    """Fraction of valid pixels in a square footprint centred on each pixel.

    Pixels outside the mask array count as invalid, so a footprint that runs
    off the search area cannot pass the threshold by accident.
    """
    m = np.asarray(mask, dtype=float)
    return uniform_filter(m, size=int(footprint_px), mode="constant", cval=0.0)


def relocate(
    mask: np.ndarray,
    footprint_px: int,
    res_m: float,
    centre: tuple[int, int] | None = None,
    threshold: float = THRESHOLD,
) -> Relocation:
    """Apply the relocation rule on ``mask`` (True = valid land).

    ``centre`` defaults to the array centre (the original coordinate). Ties in
    distance are broken by the higher valid fraction, then by row/col order.
    """
    mask = np.asarray(mask, dtype=bool)
    if centre is None:
        centre = (mask.shape[0] // 2, mask.shape[1] // 2)
    r0, c0 = centre
    frac = footprint_fraction(mask, footprint_px)
    before = float(frac[r0, c0])
    if before >= threshold:
        return Relocation(False, before, before, 0, 0, 0.0, True)

    ok = frac >= threshold
    if not ok.any():
        return Relocation(False, before, before, 0, 0, 0.0, False)
    rows, cols = np.nonzero(ok)
    dist2 = (rows - r0) ** 2 + (cols - c0) ** 2
    order = np.lexsort((cols, rows, -frac[rows, cols], dist2))
    r, c = int(rows[order[0]]), int(cols[order[0]])
    shift = float(np.hypot(r - r0, c - c0) * res_m)
    return Relocation(True, before, float(frac[r, c]), r - r0, c - c0, shift, True)
