"""PROVISIONAL scorer for Linh's lenses (M1, X1) until Bao's ``similitude.fidelity`` (A5) and
``scripts/run_all.py`` (A8) are merged. Lets B9 / web / slides run end-to-end on real data now.

Follows the PLAN contract for fidelity exactly (so A5 should reproduce these numbers in diag mode):
  * per-dimension scale D = max(std of target-body population, min_scale from lenses.yaml)
  * mode: full if n_pop >= 5*K else diag (M1: 29 < 90, X1: 5 < 20 -> diag)
  * d = Mahalanobis distance (raw), ranking / percentile / NMS on d
  * sigma = chi(1).isf(chi(K).sf(d)); if sf underflows -> logsf branch and sigma_capped = True
  * percentile of a cell = % of null cells (sample_role=null, qa ok) with d LARGER than the cell;
    null when the null sample < 30
  * limiting_factor = descriptor with the largest |z|; no_analog = best sigma over all cells > 2
If ``data/derived/fidelity.parquet`` from A8 exists, discovery uses it instead of this output.

Output: data/derived/fidelity_provisional.parquet (+ descriptor z-scores in fidelity_z_provisional)
"""

from __future__ import annotations

import numpy as np
import pandas as pd
from scipy import stats

from similitude import io

DERIVED = io.REPO_ROOT / "data" / "derived"
NULL_FLOOR = 30


def sigma_from_d(d: np.ndarray, k: int) -> tuple[np.ndarray, np.ndarray]:
    sf = stats.chi(k).sf(d)
    sigma = stats.chi(1).isf(sf)
    capped = ~np.isfinite(sigma) | (sf <= 0)
    if capped.any():
        # logsf branch: sigma for the largest representable tail, reported as "> X sigma"
        logsf = stats.chi(k).logsf(d[capped])
        sigma_cap = np.sqrt(np.maximum(-2.0 * logsf, 0.0))  # Gaussian tail approximation
        sigma = sigma.copy()
        sigma[capped] = sigma_cap
    return sigma, capped


def score(lens_id: str) -> tuple[pd.DataFrame, pd.DataFrame]:
    lens = io.load_lenses()[lens_id]
    desc = lens["descriptors"]
    earth = pd.read_parquet(DERIVED / f"earth_{lens_id}.parquet")
    tg = pd.read_parquet(DERIVED / f"targets_{lens_id}.parquet")
    pop = tg.loc[~tg["is_reference"], desc].to_numpy(float)
    refs = tg[tg["is_reference"]]
    k = len(desc)
    mode = "full" if len(pop) >= 5 * k else "diag"
    ok = earth["qa_flag"].eq("ok") & earth[desc].notna().all(axis=1)
    E = earth.loc[ok, desc].to_numpy(float)
    meta = earth.loc[ok].reset_index(drop=True)
    out, zs = [], []
    for _, t in refs.iterrows():
        tv = t[desc].to_numpy(float)
        min_scale = np.array([io.min_scale_for(lens, d_, tv[i]) for i, d_ in enumerate(desc)])
        std = np.nanstd(pop, axis=0, ddof=1) if len(pop) > 1 else np.zeros(k)
        scale = np.maximum(np.nan_to_num(std), min_scale)
        z = (E - tv) / scale
        if mode == "full":
            R = np.corrcoef(pop, rowvar=False)
            R = np.nan_to_num(R)
            np.fill_diagonal(R, 1.0)
            Rinv = np.linalg.pinv(R)
            d = np.sqrt(np.einsum("ij,jk,ik->i", z, Rinv, z))
        else:
            d = np.sqrt(np.sum(z ** 2, axis=1))
        sigma, capped = sigma_from_d(d, k)
        null_mask = meta["sample_role"].eq("null").to_numpy()
        null_d = d[null_mask]
        if null_mask.sum() >= NULL_FLOOR:
            pct = np.array([100.0 * np.mean(null_d > x) for x in d])
        else:
            pct = np.full(len(d), np.nan)
        lim = [desc[int(np.argmax(np.abs(row)))] for row in z]
        no_analog = bool(np.nanmin(sigma) > 2.0)
        for i in range(len(meta)):
            out.append({"cell_id": meta.loc[i, "cell_id"], "lens_id": lens_id,
                        "target_id": t["target_id"], "d": float(d[i]), "sigma": float(sigma[i]),
                        "sigma_capped": bool(capped[i]), "metric_mode": mode,
                        "percentile": None if np.isnan(pct[i]) else float(pct[i]),
                        "n_null": int(null_mask.sum()), "limiting_factor": lim[i],
                        "no_analog": no_analog, "feature_set": "twin_formula",
                        "provisional": True})
            zs.append({"cell_id": meta.loc[i, "cell_id"], "lens_id": lens_id,
                       "target_id": t["target_id"],
                       **{f"z_{d_}": float(z[i, j]) for j, d_ in enumerate(desc)}})
    return pd.DataFrame(out), pd.DataFrame(zs)


def main() -> None:
    fids, zs = [], []
    for lens_id in ("M1", "X1"):
        f, z = score(lens_id)
        fids.append(f)
        zs.append(z)
        best = f.sort_values("d").groupby("target_id").head(3)
        print(f"[{lens_id}] best per target:\n"
              + best[["target_id", "cell_id", "d", "sigma", "percentile", "limiting_factor"]]
              .round(2).to_string(index=False))
    pd.concat(fids).to_parquet(DERIVED / "fidelity_provisional.parquet", index=False)
    pd.concat(zs).to_parquet(DERIVED / "fidelity_z_provisional.parquet", index=False)


if __name__ == "__main__":
    main()
