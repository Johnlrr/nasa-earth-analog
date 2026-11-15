"""Slope-limited traverse planner outcomes on a DEM footprint (pre-registration V1).

The rule is fixed in ``config/prereg_route_v1.yaml``: an 8-connected grid, an edge is passable
when its along-edge grade is at most the limit, edge cost is metric length. Outcomes are read
from shortest paths between random sources and every destination 1.0-2.5 km away.

This simulates a planner on the DEM grid. It is not a rover or EVA result and resolves nothing
smaller than the grid cell.
"""

from __future__ import annotations

import numpy as np
from scipy.sparse import coo_matrix
from scipy.sparse.csgraph import dijkstra

SEED = 20261115
LIMITS = (6.0, 8.0, 10.0)
N_SRC = 24
D_MIN, D_MAX = 1000.0, 2500.0
NAN_MAX = 0.05
OUTCOMES = ("reach_6", "reach_8", "detour_8", "detour_10", "climb_10")

_STEPS = ((0, 1), (1, 0), (1, 1), (1, -1))


def _edges(dem: np.ndarray, res_m: float) -> tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
    """All undirected 8-neighbour edges: (node a, node b, length m, grade deg; NaN if no data)."""
    n, m = dem.shape
    idx = np.arange(n * m).reshape(n, m)
    a_all, b_all, d_all, g_all = [], [], [], []
    for dy, dx in _STEPS:
        if dx >= 0:
            a = idx[: n - dy, : m - dx]
            b = idx[dy:, dx:]
        else:
            a = idx[: n - dy, -dx:]
            b = idx[dy:, : m + dx]
        a, b = a.ravel(), b.ravel()
        length = res_m * float(np.hypot(dy, dx))
        dz = dem.ravel()[b] - dem.ravel()[a]
        a_all.append(a)
        b_all.append(b)
        d_all.append(np.full(a.size, length))
        g_all.append(np.degrees(np.arctan(np.abs(dz) / length)))
    return (np.concatenate(a_all), np.concatenate(b_all), np.concatenate(d_all),
            np.concatenate(g_all))


def _graph(n_nodes: int, a, b, d, g, limit: float):
    ok = np.isfinite(g) & (g <= limit)
    rows = np.concatenate([a[ok], b[ok]])
    cols = np.concatenate([b[ok], a[ok]])
    w = np.concatenate([d[ok], d[ok]])
    return coo_matrix((w, (rows, cols)), shape=(n_nodes, n_nodes)).tocsr()


def _ascent_along_tree(pred: np.ndarray, z: np.ndarray) -> np.ndarray:
    """Cumulative ascent from the source to every node along a shortest-path tree.

    ``pred`` is one row of dijkstra predecessors (-9999 for the source and unreached nodes).
    Pointer doubling: O(N log depth), no Python loop over nodes.
    """
    has = pred >= 0
    p = np.where(has, pred, np.arange(pred.size))
    acc = np.where(has, np.maximum(z - z[p], 0.0), 0.0)
    acc = np.nan_to_num(acc)
    for _ in range(32):
        if np.all(p == p[p]):
            break
        acc = acc + np.where(p != np.arange(p.size), acc[p], 0.0)
        p = p[p]
    return acc


def route_outcomes(dem: np.ndarray, res_m: float, limits=LIMITS, n_src: int = N_SRC,
                   seed: int = SEED) -> dict[str, float]:
    """Pre-registered outcome vector of one footprint (see module docstring)."""
    dem = np.asarray(dem, dtype=np.float64)
    nan_frac = float(np.isnan(dem).mean())
    out: dict[str, float] = {"nan_frac": nan_frac}
    if nan_frac > NAN_MAX:
        return out | {k: np.nan for k in OUTCOMES}
    n, m = dem.shape
    valid = np.flatnonzero(np.isfinite(dem.ravel()))
    rng = np.random.default_rng(seed)
    src = rng.choice(valid, size=min(n_src, valid.size), replace=False)
    yy, xx = np.divmod(np.arange(n * m), m)
    a, b, d, g = _edges(dem, res_m)
    z = dem.ravel()
    for lim in limits:
        G = _graph(n * m, a, b, d, g, lim)
        want_pred = lim == 10.0
        res = dijkstra(G, directed=False, indices=src, return_predecessors=want_pred)
        dist, pred = (res if want_pred else (res, None))
        reach, detour, climb = [], [], []
        for k, s in enumerate(src):
            sy, sx = divmod(int(s), m)
            e = res_m * np.hypot(yy - sy, xx - sx)
            sel = (e >= D_MIN) & (e <= D_MAX) & np.isfinite(z)
            p = dist[k, sel]
            fin = np.isfinite(p)
            reach.append(fin)
            detour.append(p[fin] / e[sel][fin])
            if want_pred:
                asc = _ascent_along_tree(pred[k], z)[sel][fin]
                climb.append(asc / (p[fin] / 1000.0))
        tag = f"{lim:g}"
        r = np.concatenate(reach)
        dt = np.concatenate(detour)
        out[f"reach_{tag}"] = float(r.mean()) if r.size else np.nan
        out[f"detour_{tag}"] = float(np.median(dt)) if dt.size else np.nan
        if want_pred:
            c = np.concatenate(climb)
            out[f"climb_{tag}"] = float(np.median(c)) if c.size else np.nan
    return {k: out[k] for k in ("nan_frac", *OUTCOMES)}


def route_distance(o: np.ndarray, o_ref: np.ndarray, scale: np.ndarray) -> np.ndarray:
    """D_route = mean_k |o_k - o_ref_k| / scale_k (rows of ``o`` are footprints)."""
    o = np.atleast_2d(np.asarray(o, float))
    return np.nanmean(np.abs(o - np.asarray(o_ref, float)) / np.asarray(scale, float), axis=1)


def robust_scale(o_native: np.ndarray) -> np.ndarray:
    """Per-outcome MAD over the lunar native footprints; std if a MAD is zero (rule fixed
    before any Earth run, see validation report §7d)."""
    o = np.asarray(o_native, float)
    med = np.nanmedian(o, axis=0)
    mad = np.nanmedian(np.abs(o - med), axis=0) * 1.4826
    sd = np.nanstd(o, axis=0)
    out = np.where(mad > 0, mad, sd)
    return np.where(out > 0, out, 1.0)
