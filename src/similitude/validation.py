"""Validation harness (PLAN A8): pre-registered controls, decoys, null distribution, sensitivity.

All checks read the expectations written BEFORE scoring (config/controls.yaml, frozen with the
13:45 contract). Nothing here changes a score; it only reports how the engine behaved.
"""

from __future__ import annotations

import numpy as np
import pandas as pd

from similitude.fidelity import score_lens

#: A pre-registered expectation is met when the control's percentile on the null sample is:
HIGH_MIN_PCT = 90.0  # expected "high": in the top 10 % of random bare land
LOW_MAX_PCT = 50.0  # expected "low" (decoy): no better than the median random cell


def expectation_met(expected: str, percentile: float) -> bool | None:
    """True/False for high/low expectations, None for 'uncertain' or missing percentile."""
    if percentile is None or not np.isfinite(percentile):
        return None
    if expected == "high":
        return bool(percentile >= HIGH_MIN_PCT)
    if expected == "low":
        return bool(percentile <= LOW_MAX_PCT)
    return None


def control_report(fid: pd.DataFrame, earth: pd.DataFrame) -> pd.DataFrame:
    """One row per (control/decoy, target): d, sigma, percentile, rank among scored cells."""
    meta = earth[["cell_id", "sample_role", "name", "expected"]]
    scored = fid.merge(meta, on="cell_id", how="left")
    scored["rank_all"] = scored.groupby("target_id")["d"].rank(method="min")
    scored["n_scored"] = scored.groupby("target_id")["d"].transform("count")
    rep = scored[scored["sample_role"].isin(["control", "decoy"])].copy()
    rep["expectation_met"] = [
        expectation_met(e, p) for e, p in zip(rep["expected"], rep["percentile"], strict=True)
    ]
    cols = [
        "lens_id",
        "target_id",
        "cell_id",
        "name",
        "sample_role",
        "expected",
        "d",
        "sigma",
        "percentile",
        "rank_all",
        "n_scored",
        "limiting_factor",
        "expectation_met",
    ]
    return rep[cols].sort_values(["lens_id", "target_id", "d"]).reset_index(drop=True)


def null_summary(fid: pd.DataFrame, earth: pd.DataFrame) -> pd.DataFrame:
    """Distribution of d per sample_role and target (does the ranked set beat random land?)."""
    m = fid.merge(earth[["cell_id", "sample_role"]], on="cell_id", how="left")
    g = m.groupby(["lens_id", "target_id", "sample_role"])["d"]
    return g.describe(percentiles=[0.1, 0.5]).reset_index()


def top_k(fid: pd.DataFrame, earth: pd.DataFrame, target_id: str, k: int = 10) -> list[str]:
    roles = earth.set_index("cell_id")["sample_role"]
    f = fid[fid["target_id"] == target_id].copy()
    f = f[f["cell_id"].map(roles).isin(["rank", "seed"])]
    return f.nsmallest(k, "d")["cell_id"].tolist()


def sensitivity_drop_one(
    earth: pd.DataFrame, targets: pd.DataFrame, lens: dict, target_id: str, k: int = 10
) -> pd.DataFrame:
    """Jaccard overlap of the top-k (rank+seed cells) when each descriptor is dropped in turn."""
    base = top_k(score_lens(earth, targets, lens), earth, target_id, k)
    rows = []
    for drop in lens["descriptors"]:
        sub = dict(lens, descriptors=[d for d in lens["descriptors"] if d != drop])
        alt = top_k(score_lens(earth, targets, sub), earth, target_id, k)
        inter, union = len(set(base) & set(alt)), len(set(base) | set(alt))
        rows.append(
            {
                "lens_id": lens["id"],
                "target_id": target_id,
                "dropped": drop,
                "jaccard_top%d" % k: inter / union if union else np.nan,
            }
        )
    return pd.DataFrame(rows)
