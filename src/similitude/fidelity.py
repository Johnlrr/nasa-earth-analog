from __future__ import annotations

import math
from dataclasses import dataclass

import numpy as np
import pandas as pd
import scipy.special
import scipy.stats


@dataclass
class Metric:
    mean: np.ndarray  # (K,)
    cov_inv: np.ndarray  # (K,K)
    scale: np.ndarray  # (K,)
    mode: str  # "full" | "pca" | "diag"


def fit_population(
    X_pop: np.ndarray,
    min_scale: np.ndarray,
    mode: str = "auto",
) -> Metric:
    X = X_pop[~np.any(np.isnan(X_pop), axis=1)]
    n, K = X.shape
    mean = np.mean(X, axis=0)
    std = np.std(X, axis=0, ddof=1)
    scale = np.maximum(std, min_scale)

    if mode == "auto":
        resolved = "full" if n >= 5 * K else "diag"
    else:
        resolved = mode

    if resolved == "full":
        # Build correlation matrix; degenerate columns (std < 1e-12) → zero row/col, diag=1
        R = np.eye(K)
        active = std >= 1e-12
        if np.any(active):
            X_norm = np.zeros_like(X)
            X_norm[:, active] = (X[:, active] - mean[active]) / std[active]
            R_sub = np.atleast_2d(np.corrcoef(X_norm[:, active].T))
            idx = np.where(active)[0]
            for i, ai in enumerate(idx):
                for j, aj in enumerate(idx):
                    R[ai, aj] = R_sub[i, j]

        D = np.diag(scale)
        Sigma = D @ R @ D

        # Check condition; fall back to pca if ill-conditioned
        cond = np.linalg.cond(Sigma)
        if cond > 1e8:
            cov_inv = np.linalg.pinv(Sigma, rcond=1e-8)
            resolved = "pca"
        else:
            cov_inv = np.linalg.inv(Sigma)
    else:
        # diag: Σ⁻¹ = diag(1/D²)
        cov_inv = np.diag(1.0 / (scale**2))
        resolved = "diag"

    return Metric(mean=mean, cov_inv=cov_inv, scale=scale, mode=resolved)


def mahalanobis_d(E: np.ndarray, t: np.ndarray, m: Metric) -> np.ndarray:
    E = np.atleast_2d(E)
    diff = E - t  # (N, K)
    # rows with any NaN → NaN
    has_nan = np.any(np.isnan(diff), axis=1)
    diff_safe = np.where(np.isnan(diff), 0.0, diff)
    # d² = diff @ cov_inv @ diff.T diag
    d2 = np.einsum("ni,ij,nj->n", diff_safe, m.cov_inv, diff_safe)
    d = np.sqrt(np.maximum(d2, 0.0))
    d[has_nan] = np.nan
    return d


def sigma_dissimilarity(E: np.ndarray, t: np.ndarray, m: Metric) -> tuple[np.ndarray, np.ndarray]:
    E = np.atleast_2d(E)
    K = m.cov_inv.shape[0]
    d = mahalanobis_d(E, t, m)

    chi_K = scipy.stats.chi(K)
    chi_1 = scipy.stats.chi(1)

    sigma = np.empty_like(d)
    capped = np.zeros(len(d), dtype=bool)

    for i, di in enumerate(d):
        if np.isnan(di):
            sigma[i] = np.nan
            continue
        # sf of chi_K at d → isf of chi_1
        sf_val = chi_K.sf(di)
        if sf_val > 0.0:
            p = sf_val
            s = chi_1.isf(p)
            if np.isfinite(s):
                sigma[i] = s
            else:
                # isf returned inf even though sf > 0; treat as underflow
                sigma[i] = _sigma_tail_approx(-2 * _chi_logsf(di, K))
                capped[i] = True
        else:
            # underflow: use logsf
            p_log = _chi_logsf(di, K)  # log(sf), negative
            L = -2 * p_log
            # tail approximation: σ ≈ sqrt(L - ln L + ln(2/π))
            sigma[i] = _sigma_tail_approx(L)
            capped[i] = True

    return sigma, capped


def _chi_logsf(d: float, K: int) -> float:
    """log P(chi_K > d), finite for large d.

    scipy returns -inf once sf underflows (d >~ 40 for K = 14). Fall back to the
    asymptotic expansion of the regularised upper incomplete gamma function:
    log Q(s, x) ~ (s-1) log x - x - lgamma(s) + log(1 + (s-1)/x), s = K/2, x = d^2/2
    (relative error < 0.05 % already at d = 10, K = 14).
    """
    val = scipy.stats.chi(K).logsf(d)
    if np.isfinite(val):
        return float(val)
    s, x = K / 2.0, d * d / 2.0
    return float((s - 1) * np.log(x) - x - scipy.special.gammaln(s) + np.log1p((s - 1) / x))


def _sigma_tail_approx(L: float) -> float:
    # From sf_χ1(σ) ≈ 2φ(σ)/σ, solve L = -2 log(sf) = σ² + log(σ²) - log(2/π)
    # Approximation: σ ≈ sqrt(L - ln L + ln(2/π))
    if L <= 0:
        return 0.0
    ln_L = math.log(L) if L > 0 else 0.0
    val = L - ln_L + math.log(2.0 / math.pi)
    return math.sqrt(max(val, 0.0))


def limiting_factor(E: np.ndarray, t: np.ndarray, m: Metric, names: list[str]) -> list[str]:
    E = np.atleast_2d(E)
    diff = E - t  # (N, K)
    # normalized deviation per descriptor
    norm_dev = np.abs(diff / m.scale)  # (N, K)
    idx = np.argmax(norm_dev, axis=1)
    return [names[i] for i in idx]


def score_lens(
    earth: pd.DataFrame,
    targets: pd.DataFrame,
    lens: dict,
) -> pd.DataFrame:
    lens_id = lens["id"]
    desc_names: list[str] = lens["descriptors"]
    min_scale_cfg: dict = lens["min_scale"]

    is_l2 = lens_id == "L2"
    shadow_names = [n for n in desc_names if n.startswith("shadow_")] if is_l2 else []

    reference_targets = targets[targets["is_reference"].astype(bool)]
    population_targets = targets[~targets["is_reference"].astype(bool)]

    rows = []

    for _, trow in reference_targets.iterrows():
        target_id = trow["target_id"]

        # Build min_scale vector for this target
        t_vec = np.array([trow[d] for d in desc_names], dtype=float)
        min_scale_vec = np.array(
            [_resolve_min_scale(min_scale_cfg.get(d, 1e-6), trow.get(d, 0.0)) for d in desc_names],
            dtype=float,
        )

        # Population X from non-reference targets
        X_pop = population_targets[desc_names].values.astype(float)

        metric = fit_population(X_pop, min_scale_vec)

        # Score all earth rows
        E_mat = earth[desc_names].values.astype(float)

        d_arr = mahalanobis_d(E_mat, t_vec, metric)
        sigma_arr, capped_arr = sigma_dissimilarity(E_mat, t_vec, metric)
        lf_list = limiting_factor(E_mat, t_vec, metric, desc_names)

        # Percentile: fraction of null rows with d > each row's d
        null_mask = earth["sample_role"] == "null"
        n_null = null_mask.sum()
        if n_null < 30:
            percentile_arr = np.full(len(earth), np.nan)
        else:
            d_null = d_arr[null_mask.values]
            percentile_arr = np.array(
                [100.0 * np.mean(d_null > di) if not np.isnan(di) else np.nan for di in d_arr]
            )

        # no_analog: check among rank/seed/control/decoy/null rows
        scoring_roles = {"rank", "seed", "control", "decoy", "null"}
        scoring_mask = earth["sample_role"].isin(scoring_roles).values
        sigma_scoring = sigma_arr[scoring_mask]
        valid_sigma = sigma_scoring[~np.isnan(sigma_scoring)]
        no_analog = bool(len(valid_sigma) > 0 and np.min(valid_sigma) > 2.0)

        # L2 shadow columns
        if is_l2 and shadow_names:
            sh_min_scale = np.array(
                [
                    _resolve_min_scale(min_scale_cfg.get(d, 1e-6), trow.get(d, 0.0))
                    for d in shadow_names
                ],
                dtype=float,
            )
            t_sh = np.array([trow[d] for d in shadow_names], dtype=float)
            X_pop_sh = population_targets[shadow_names].values.astype(float)
            metric_sh = fit_population(X_pop_sh, sh_min_scale)
            E_sh = earth[shadow_names].values.astype(float)
            d_sh = mahalanobis_d(E_sh, t_sh, metric_sh)
            sigma_sh, _ = sigma_dissimilarity(E_sh, t_sh, metric_sh)

        for i, erow in enumerate(earth.itertuples(index=False)):
            cell_id = erow.cell_id
            rec = {
                "cell_id": cell_id,
                "lens_id": lens_id,
                "target_id": target_id,
                "d": d_arr[i],
                "sigma": sigma_arr[i],
                "sigma_capped": bool(capped_arr[i]),
                "metric_mode": metric.mode,
                "percentile": percentile_arr[i] if not np.isnan(percentile_arr[i]) else None,
                "limiting_factor": lf_list[i],
                "no_analog": no_analog,
                "feature_set": "twin_formula",
            }
            if is_l2 and shadow_names:
                rec["d_shadow"] = d_sh[i]
                rec["sigma_shadow"] = sigma_sh[i]
            rows.append(rec)

    return pd.DataFrame(rows)


def _resolve_min_scale(cfg_val, target_val: float) -> float:
    if isinstance(cfg_val, str) and cfg_val == "10%target":
        return max(0.1 * abs(float(target_val)), 1e-6)
    return float(cfg_val)
