"""Tests for fidelity.py — A5 verification suite."""

from __future__ import annotations

import math

import numpy as np
import pandas as pd
import pytest
import scipy.stats

from similitude.fidelity import (
    _sigma_tail_approx,
    fit_population,
    limiting_factor,
    mahalanobis_d,
    score_lens,
    sigma_dissimilarity,
)

# ---------------------------------------------------------------------------
# helpers
# ---------------------------------------------------------------------------


def _pop(n: int, K: int, rng: np.random.Generator) -> np.ndarray:
    return rng.standard_normal((n, K))


def _min_scale(K: int, val: float = 0.1) -> np.ndarray:
    return np.full(K, val)


# ---------------------------------------------------------------------------
# 1. E == t → d ≈ 0, σ ≈ 0
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("K", [1, 3, 5])
def test_e_equals_t_gives_zero(K):
    rng = np.random.default_rng(42)
    n = max(5 * K, 30)
    X = _pop(n, K, rng)
    m = fit_population(X, _min_scale(K))
    t = np.zeros(K)
    E = t[np.newaxis, :]
    d = mahalanobis_d(E, t, m)
    assert d[0] == pytest.approx(0.0, abs=1e-10)
    sigma, _ = sigma_dissimilarity(E, t, m)
    assert sigma[0] == pytest.approx(0.0, abs=1e-10)


# ---------------------------------------------------------------------------
# 2. σ monotone increasing as e drifts away along one axis
# ---------------------------------------------------------------------------


def test_sigma_monotone():
    rng = np.random.default_rng(0)
    K = 4
    n = 5 * K + 5
    X = _pop(n, K, rng)
    m = fit_population(X, _min_scale(K))
    t = np.zeros(K)
    deltas = np.linspace(0, 10, 50)
    E = np.zeros((len(deltas), K))
    E[:, 0] = deltas
    sigma, _ = sigma_dissimilarity(E, t, m)
    for i in range(len(sigma) - 1):
        assert sigma[i] <= sigma[i + 1] + 1e-12, f"not monotone at i={i}"


# ---------------------------------------------------------------------------
# 3. n < 5·K → mode "diag"
# ---------------------------------------------------------------------------


def test_small_n_gives_diag():
    rng = np.random.default_rng(1)
    K = 6
    n = 5 * K - 1  # one below threshold
    X = _pop(n, K, rng)
    m = fit_population(X, _min_scale(K), mode="auto")
    assert m.mode == "diag"


def test_large_n_gives_full_or_pca():
    rng = np.random.default_rng(2)
    K = 3
    n = 5 * K + 10
    X = _pop(n, K, rng)
    m = fit_population(X, _min_scale(K), mode="auto")
    assert m.mode in ("full", "pca")


# ---------------------------------------------------------------------------
# 4. Constant column in population → mahalanobis_d finite;
#    when only that column deviates by δ: d = δ / min_scale (1e-9 tol)
#    Test for both "diag" (explicit) and "full" (auto but forced via large n).
# ---------------------------------------------------------------------------


def test_constant_column_diag():
    rng = np.random.default_rng(3)
    K = 3
    n = 10  # < 5*K=15 → diag
    X = _pop(n, K, rng)
    X[:, 1] = 5.0  # column 1 constant
    ms_val = 0.5
    ms = _min_scale(K, ms_val)
    m = fit_population(X, ms, mode="auto")
    assert m.mode == "diag"
    t = np.zeros(K)
    delta = 2.0
    e = np.array([[0.0, delta, 0.0]])
    d = mahalanobis_d(e, t, m)
    assert np.isfinite(d[0])
    expected = delta / ms_val  # only constant col deviates; others are 0
    assert d[0] == pytest.approx(expected, rel=1e-9)


def test_constant_column_full_no_nan():
    rng = np.random.default_rng(4)
    K = 3
    n = 5 * K + 20  # → full
    X = _pop(n, K, rng)
    X[:, 2] = 3.0  # column 2 constant
    ms_val = 0.3
    ms = _min_scale(K, ms_val)
    m = fit_population(X, ms, mode="auto")
    # mode must be full or pca, never diag
    assert m.mode in ("full", "pca")
    t = np.zeros(K)
    delta = 1.5
    e = np.array([[0.0, 0.0, delta]])
    d = mahalanobis_d(e, t, m)
    assert np.isfinite(d[0])
    assert not np.isnan(d[0])
    expected = delta / ms_val
    # In full mode with decorrelated constant column: d = delta / min_scale
    assert d[0] == pytest.approx(expected, rel=1e-9)


# ---------------------------------------------------------------------------
# 5. K = 1 → sigma == d (up to 1e-9)
# ---------------------------------------------------------------------------


def test_k1_sigma_equals_d():
    rng = np.random.default_rng(5)
    K = 1
    n = 5 * K + 10
    X = _pop(n, K, rng)
    ms = _min_scale(K, 0.01)
    m = fit_population(X, ms, mode="diag")
    t = np.zeros(K)
    # several d values
    deltas = np.array([0.0, 0.5, 1.0, 2.0, 3.0])
    E = deltas[:, np.newaxis]
    d = mahalanobis_d(E, t, m)
    sigma, _ = sigma_dissimilarity(E, t, m)
    for i in range(len(deltas)):
        assert sigma[i] == pytest.approx(d[i], rel=1e-9), f"K=1 sigma != d at delta={deltas[i]}"


# ---------------------------------------------------------------------------
# 6. d = 50, K = 14 → σ finite, not NaN/inf, capped may be True;
#    over d = 1..200 (K=14) σ strictly increasing (rank preserved).
# ---------------------------------------------------------------------------


def test_large_d_sigma_finite():
    rng = np.random.default_rng(6)
    K = 14
    n = 5 * K + 10
    X = _pop(n, K, rng)
    ms = _min_scale(K, 0.01)
    m = fit_population(X, ms, mode="diag")
    t = np.zeros(K)
    # single point with d ≈ 50 along first axis; adjust for diag scale
    # In diag mode, d = ||diff / scale||; scale ≈ max(1, 0.01) = 1
    e_50 = np.zeros((1, K))
    e_50[0, 0] = 50.0  # will produce d ≈ 50 when scale[:,0] ≈ 1
    mahalanobis_d(e_50, t, m)  # must not raise
    sigma, capped = sigma_dissimilarity(e_50, t, m)
    assert np.isfinite(sigma[0]), f"sigma should be finite, got {sigma[0]}"
    assert not np.isnan(sigma[0])

    # Rank preservation over d = 1..200
    deltas = np.arange(1, 201, dtype=float)
    E_range = np.zeros((len(deltas), K))
    E_range[:, 0] = deltas
    d_range = mahalanobis_d(E_range, t, m)
    sigma_range, _ = sigma_dissimilarity(E_range, t, m)
    # Both d_range and sigma_range should be strictly increasing
    assert np.all(np.diff(d_range) > 0), "d not strictly increasing"
    assert np.all(np.diff(sigma_range) > 0), "sigma not strictly increasing over d range"


# ---------------------------------------------------------------------------
# 7. limiting_factor returns correct descriptor name
# ---------------------------------------------------------------------------


def test_limiting_factor_correct_name():
    rng = np.random.default_rng(7)
    K = 4
    names = ["slope", "rough", "shadow", "hurst"]
    ms = _min_scale(K, 0.5)
    n = 5 * K + 5
    X = _pop(n, K, rng)
    m = fit_population(X, ms, mode="diag")
    t = np.zeros(K)
    # Shift only descriptor index 2 ("shadow") by large amount
    e = np.zeros((1, K))
    e[0, 2] = 100.0
    result = limiting_factor(e, t, m, names)
    assert result[0] == "shadow"


# ---------------------------------------------------------------------------
# 8. tail approximation accuracy: chi(1).isf(1e-30) vs _sigma_tail_approx
# ---------------------------------------------------------------------------


def test_tail_approx_accuracy():
    p = 1e-30
    chi_1 = scipy.stats.chi(1)
    exact = chi_1.isf(p)
    # Build L from p: L = -2 * log(p)
    L = -2 * math.log(p)
    approx = _sigma_tail_approx(L)
    rel_err = abs(approx - exact) / abs(exact)
    assert rel_err < 0.01, f"tail approx error {rel_err:.3%} > 1%"


# ---------------------------------------------------------------------------
# 9. score_lens: synthetic data tests
# ---------------------------------------------------------------------------


def _make_score_lens_data(n_null: int = 40, include_match: bool = True):
    """
    Create minimal earth + targets + lens dicts for score_lens tests.
    K = 2, descriptors = ["d1", "d2"].
    Target is at [0, 0]. Population is spread around [5, 5].
    """
    rng = np.random.default_rng(99)
    K = 2
    names = ["d1", "d2"]

    # Population for fitting (non-reference targets), centred at [5,5]
    n_pop = 20
    X_pop = rng.standard_normal((n_pop, K)) + 5.0

    targets_rows = []
    for i in range(n_pop):
        targets_rows.append(
            {
                "target_id": f"pop_{i}",
                "is_reference": False,
                "d1": X_pop[i, 0],
                "d2": X_pop[i, 1],
            }
        )
    targets_rows.append({"target_id": "ref_0", "is_reference": True, "d1": 0.0, "d2": 0.0})
    targets = pd.DataFrame(targets_rows)

    # Earth rows
    earth_rows = []

    # null rows
    for i in range(n_null):
        earth_rows.append(
            {
                "cell_id": f"null_{i}",
                "sample_role": "null",
                "d1": rng.standard_normal() * 3,
                "d2": rng.standard_normal() * 3,
            }
        )

    # rank rows (far from target)
    for i in range(5):
        earth_rows.append(
            {
                "cell_id": f"rank_{i}",
                "sample_role": "rank",
                "d1": 10.0 + rng.standard_normal(),
                "d2": 10.0 + rng.standard_normal(),
            }
        )

    # planted match: exactly at target
    if include_match:
        earth_rows.append(
            {
                "cell_id": "match",
                "sample_role": "rank",
                "d1": 0.0,
                "d2": 0.0,
            }
        )

    earth = pd.DataFrame(earth_rows)

    lens = {
        "id": "L1",
        "descriptors": names,
        "min_scale": {"d1": 0.1, "d2": 0.1},
    }
    return earth, targets, lens


def test_score_lens_match_has_smallest_sigma():
    earth, targets, lens = _make_score_lens_data(n_null=40, include_match=True)
    result = score_lens(earth, targets, lens)
    match_row = result[result["cell_id"] == "match"]
    assert len(match_row) == 1
    assert match_row["d"].iloc[0] == pytest.approx(0.0, abs=1e-10)
    assert match_row["sigma"].iloc[0] == pytest.approx(0.0, abs=1e-10)
    # match should have highest or near-highest percentile
    assert match_row["percentile"].iloc[0] >= 90.0


def test_score_lens_match_percentile_near_100():
    earth, targets, lens = _make_score_lens_data(n_null=40, include_match=True)
    result = score_lens(earth, targets, lens)
    match_row = result[result["cell_id"] == "match"]
    pct = match_row["percentile"].iloc[0]
    # almost all null rows have d > 0, so percentile should be close to 100
    assert pct >= 90.0


def test_score_lens_null_lt_30_gives_nan_percentile():
    earth, targets, lens = _make_score_lens_data(n_null=20, include_match=True)
    result = score_lens(earth, targets, lens)
    # all percentiles should be None/NaN when n_null < 30
    pcts = result["percentile"]
    assert pcts.isna().all()


def test_score_lens_no_analog_when_all_far():
    """When every earth point is very far (sigma > 2 for all), no_analog = True."""
    rng = np.random.default_rng(55)
    K = 2
    names = ["d1", "d2"]

    n_pop = 20
    X_pop = rng.standard_normal((n_pop, K)) * 0.01  # tight population near [0,0]
    targets_rows = []
    for i in range(n_pop):
        targets_rows.append(
            {"target_id": f"pop_{i}", "is_reference": False, "d1": X_pop[i, 0], "d2": X_pop[i, 1]}
        )
    targets_rows.append({"target_id": "ref_0", "is_reference": True, "d1": 0.0, "d2": 0.0})
    targets = pd.DataFrame(targets_rows)

    # All earth rows very far from target
    n_null = 40
    earth_rows = []
    for i in range(n_null):
        earth_rows.append(
            {
                "cell_id": f"null_{i}",
                "sample_role": "null",
                "d1": 1000.0 + rng.standard_normal(),
                "d2": 1000.0 + rng.standard_normal(),
            }
        )
    earth = pd.DataFrame(earth_rows)

    lens = {"id": "L1", "descriptors": names, "min_scale": {"d1": 0.1, "d2": 0.1}}
    result = score_lens(earth, targets, lens)
    assert result["no_analog"].all()


def test_score_lens_schema_columns():
    earth, targets, lens = _make_score_lens_data(n_null=40)
    result = score_lens(earth, targets, lens)
    required = [
        "cell_id",
        "lens_id",
        "target_id",
        "d",
        "sigma",
        "sigma_capped",
        "metric_mode",
        "percentile",
        "limiting_factor",
        "no_analog",
        "feature_set",
    ]
    for col in required:
        assert col in result.columns, f"missing column: {col}"


def test_score_lens_l2_shadow_columns():
    """L2 lens should produce d_shadow and sigma_shadow columns."""
    rng = np.random.default_rng(77)
    K = 3
    names = ["lowsun_frac", "shadow_e2", "shadow_e5"]

    n_pop = 20
    X_pop = rng.standard_normal((n_pop, K))
    targets_rows = []
    for i in range(n_pop):
        targets_rows.append(
            {
                "target_id": f"pop_{i}",
                "is_reference": False,
                "lowsun_frac": X_pop[i, 0],
                "shadow_e2": X_pop[i, 1],
                "shadow_e5": X_pop[i, 2],
            }
        )
    targets_rows.append(
        {
            "target_id": "ref_0",
            "is_reference": True,
            "lowsun_frac": 0.0,
            "shadow_e2": 0.0,
            "shadow_e5": 0.0,
        }
    )
    targets = pd.DataFrame(targets_rows)

    earth_rows = []
    n_null = 40
    for i in range(n_null):
        earth_rows.append(
            {
                "cell_id": f"null_{i}",
                "sample_role": "null",
                "lowsun_frac": rng.standard_normal(),
                "shadow_e2": rng.standard_normal(),
                "shadow_e5": rng.standard_normal(),
            }
        )
    earth = pd.DataFrame(earth_rows)

    lens = {
        "id": "L2",
        "descriptors": names,
        "min_scale": {"lowsun_frac": 0.05, "shadow_e2": 0.05, "shadow_e5": 0.05},
    }
    result = score_lens(earth, targets, lens)
    assert "d_shadow" in result.columns
    assert "sigma_shadow" in result.columns


def test_score_lens_feature_set():
    earth, targets, lens = _make_score_lens_data(n_null=40)
    result = score_lens(earth, targets, lens)
    assert (result["feature_set"] == "twin_formula").all()


def test_score_lens_min_scale_10pct_target():
    """min_scale value {rel: 0.1} (lenses.yaml contract) resolves to 0.1*|t_k|."""
    rng = np.random.default_rng(88)
    K = 2
    names = ["d1", "d2"]
    n_pop = 20
    X_pop = rng.standard_normal((n_pop, K)) + 5.0
    targets_rows = [
        {"target_id": f"pop_{i}", "is_reference": False, "d1": X_pop[i, 0], "d2": X_pop[i, 1]}
        for i in range(n_pop)
    ]
    targets_rows.append({"target_id": "ref_0", "is_reference": True, "d1": 10.0, "d2": 20.0})
    targets = pd.DataFrame(targets_rows)

    n_null = 40
    earth_rows = [
        {
            "cell_id": f"null_{i}",
            "sample_role": "null",
            "d1": rng.standard_normal() * 2 + 10,
            "d2": rng.standard_normal() * 2 + 20,
        }
        for i in range(n_null)
    ]
    earth = pd.DataFrame(earth_rows)

    lens = {"id": "L1", "descriptors": names, "min_scale": {"d1": {"rel": 0.1}, "d2": {"rel": 0.1}}}
    result = score_lens(earth, targets, lens)
    # Just check it runs without error and produces valid numbers
    assert result["d"].notna().any()


# ---------------------------------------------------------------------------
# Native rank (A11)
# ---------------------------------------------------------------------------


def _native_data(lens_id="L1"):
    names = ["d1", "d2"]
    rows = [{"target_id": "site", "is_reference": True, "body": "moon", "lat": -89.0,
             "lon": 0.0, "footprint_m": 4000.0, "d1": 0.0, "d2": 0.0}]
    # 10 siblings at descriptor distance 1..10, far apart on the ground
    for i in range(10):
        rows.append({"target_id": "site", "is_reference": False, "body": "moon",
                     "lat": -85.0 + i * 0.2, "lon": 90.0, "footprint_m": 4000.0,
                     "d1": float(i + 1), "d2": 0.0})
    # one sibling overlapping the reference footprint (1 km away) -> excluded
    rows.append({"target_id": "site", "is_reference": False, "body": "moon",
                 "lat": -89.0 + 1000 / 1_737_400 * 180 / np.pi, "lon": 0.0,
                 "footprint_m": 4000.0, "d1": 0.0, "d2": 0.0})
    targets = pd.DataFrame(rows)
    earth = pd.DataFrame([
        {"cell_id": "same", "sample_role": "rank", "d1": 0.0, "d2": 0.0},
        {"cell_id": "far", "sample_role": "rank", "d1": 1e6, "d2": 1e6},
    ])
    lens = {"id": lens_id, "descriptors": names, "min_scale": {"d1": 1.0, "d2": 1.0}}
    return earth, targets, lens


def test_native_rank_counts():
    from similitude.fidelity import native_rank

    out = native_rank(np.array([0.0, 2.5, 99.0, np.nan]), np.array([1, 2, 3, 4.0]))
    assert out[:3].tolist() == [4, 2, 0] and np.isnan(out[3])


def test_native_rank_in_score_lens():
    earth, targets, lens = _native_data()
    res = score_lens(earth, targets, lens).set_index("cell_id")
    assert (res["n_native"] == 10).all()  # overlapping sibling excluded
    assert res.loc["same", "native_rank"] == 10  # cell identical to target
    assert res.loc["far", "native_rank"] == 0  # farther than every footprint
    assert (res["native_rank_basis"] == "d").all()


def test_native_rank_empty_for_m1():
    earth, targets, lens = _native_data("M1")
    res = score_lens(earth, targets, lens)
    assert res["native_rank"].isna().all()
    assert res["native_rank_basis"].str.contains("not defined").all()


def test_native_rank_l2_uses_shadow_distance():
    earth, targets, lens = _native_data("L2")
    for df in (earth, targets):
        df["shadow_e2"] = df["d1"]
        df["lowsun_frac"] = 1e6  # astro part far away: d is huge, d_shadow is not
    targets.loc[targets.is_reference, "lowsun_frac"] = 0.0
    lens["descriptors"] = ["lowsun_frac", "shadow_e2"]
    lens["min_scale"] = {"lowsun_frac": 1.0, "shadow_e2": 1.0}
    res = score_lens(earth, targets, lens).set_index("cell_id")
    assert (res["native_rank_basis"] == "d_shadow").all()
    assert res.loc["same", "native_rank"] == 10
