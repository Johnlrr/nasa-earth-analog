"""B1 tests for the shared spectral descriptor library."""

import numpy as np
import pytest

from similitude import io
from similitude.descriptors import spectral as sp

WL = sp.COMMON_WL_NM


def gauss(center, depth=0.2, sigma=20.0):
    return depth * np.exp(-0.5 * ((WL - center) / sigma) ** 2)


def spectrum(*bands, level=0.3):
    r = np.ones_like(WL)
    for c, d, s in bands:
        r = r - gauss(c, d, s)
    return level * r


BAND_DEPTH_LIKE = [k for k, v in sp.PARAM_TABLE.items() if v["kind"] != "shoulder"]


def test_grid_bounds_and_gaps():
    assert WL[0] == 400 and WL[-1] == 2490
    assert np.all(np.diff(WL) >= 10)
    for lo, hi in sp.GAPS_NM:
        assert not np.any((WL >= lo) & (WL <= hi))


def test_param_table_complete():
    for name, p in sp.PARAM_TABLE.items():
        for key in ("vb14", "kind", "group", "original_nm", "used_nm", "meaning"):
            assert key in p, f"{name} missing {key}"
        if p["original_nm"] != p["used_nm"] or "original_centers_nm" in p:
            assert "substitution" in p, f"{name} changed anchors without a substitution note"


def test_no_used_anchor_in_gap_or_beyond_grid():
    def flat(x):
        for v in x:
            if isinstance(v, (tuple, list)):
                yield from flat(v)
            else:
                yield v

    for name, p in sp.PARAM_TABLE.items():
        anchors = list(flat(p["used_nm"])) + list(p.get("centers_nm", ()))
        for lam in anchors:
            assert 400 <= lam <= 2490, (name, lam)
            assert not sp._in_gap(lam), (name, lam)


def test_flat_spectrum_all_band_depths_zero():
    params = sp.crism_params(np.full_like(WL, 0.3), subset="all")
    for name in BAND_DEPTH_LIKE:
        assert abs(params[name]) < 1e-9, name
    for name in ("SH600", "SH770"):
        assert params[name] == pytest.approx(1.0)


def test_absorption_2300_vs_2210():
    r2300 = spectrum((2300, 0.2, 20))
    p = sp.crism_params(r2300)
    assert p["D2300"] > 0.05
    assert p["BD2210"] <= 0.01

    r2210 = spectrum((2210, 0.2, 20))
    q = sp.crism_params(r2210)
    assert q["BD2210"] > 0.05
    assert q["D2300"] <= 0.01


def test_carbonate_doublet_needs_both_bands():
    carbonate = spectrum((2300, 0.2, 20), (2500, 0.2, 30))
    only_2300 = spectrum((2300, 0.2, 20))
    assert sp.crism_params(carbonate)["MIN2295_2480"] > 0.02
    assert sp.crism_params(only_2300)["MIN2295_2480"] <= 0.01


def test_olivine_broad_1um_band_raises_olindex():
    olivine = spectrum((1050, 0.35, 150), (1250, 0.25, 120))
    assert sp.crism_params(olivine)["OLINDEX"] > 0.05
    assert abs(sp.crism_params(np.full_like(WL, 0.3))["OLINDEX"]) < 1e-9


def test_swir_subset_matches_m1_lens_descriptors():
    keys = set(sp.crism_params(np.full_like(WL, 0.3), subset="swir"))
    m1 = set(io.load_lenses()["M1"]["descriptors"])
    assert m1 <= keys
    excluded = set(io.load_lenses()["M1"]["excluded_descriptors"])
    assert keys - m1 == excluded  # every SWIR parameter is either used or excluded with a reason
    assert set(sp.EXCLUDED_FROM_M1) <= excluded
    assert not keys & set(sp.VNIR_PARAMS)


def test_sam_identity_and_scale_invariance():
    a = spectrum((2300, 0.2, 20), (2500, 0.1, 30))
    assert sp.sam(a, a) == pytest.approx(0.0, abs=1e-7)
    assert sp.sam(a, 2.5 * a) == pytest.approx(0.0, abs=1e-7)
    b = spectrum((2210, 0.2, 20))
    assert sp.sam(a, b) > 0.01


def test_resample_from_emit_like_grid():
    wl_emit = np.arange(381.0, 2493.0, 7.43)
    smooth = 0.2 + 0.1 * np.sin(wl_emit / 300.0)
    smooth[(wl_emit > 1340) & (wl_emit < 1450)] = -9999.0  # EMIT-style fill in water bands
    out = sp.resample(wl_emit, smooth)
    assert out.shape == WL.shape
    expect = 0.2 + 0.1 * np.sin(WL / 300.0)
    ok = np.isfinite(out)
    assert ok.sum() > 0.95 * WL.size
    assert np.allclose(out[ok], expect[ok], atol=2e-3)


def test_resample_no_extrapolation_and_stack():
    wl = np.arange(1000.0, 2000.0, 5.0)
    out = sp.resample(wl, np.ones_like(wl))
    assert np.isnan(out[WL < 995]).all() and np.isnan(out[WL > 2005]).all()
    stack = sp.resample(wl, np.ones((2, 3, wl.size)))
    assert stack.shape == (2, 3, WL.size)


def test_resample_ignores_emit_minus_001_fill():
    wl_emit = np.arange(381.0, 2493.0, 7.43)
    r = np.full_like(wl_emit, 0.4)
    r[(wl_emit > 1325) & (wl_emit < 1460)] = -0.01
    r[(wl_emit > 1765) & (wl_emit < 1970)] = -0.01
    out = sp.resample(wl_emit, r)
    ok = np.isfinite(out)
    assert np.allclose(out[ok], 0.4)
    p = sp.crism_params(out)
    m1 = io.load_lenses()["M1"]["descriptors"]
    for name in m1:  # every M1 descriptor survives the widest EMIT fill seen in real scenes
        assert abs(p[name]) < 1e-9, name
    assert np.isnan(p["BD1750"])  # right shoulder masked -> excluded from M1 (PARAM_TABLE note)


def test_crism_params_rejects_wrong_grid():
    with pytest.raises(ValueError):
        sp.crism_params(np.ones(10))
