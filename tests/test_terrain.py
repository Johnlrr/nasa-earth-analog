import numpy as np
import pytest
from conftest import make_fbm

from similitude.descriptors.terrain import (
    aggregate_to_baseline,
    roughness_spectrum,
    shadow_fraction,
    slope_stats,
    terrain_descriptors,
)


def test_slope_inclined_plane():
    # 10-degree slope in x direction, 200×200 at 30m
    res = 30.0
    n = 200
    x = np.arange(n) * res
    dem = np.outer(np.ones(n), x) * np.tan(np.radians(10))
    stats = slope_stats(dem, res)
    assert abs(stats["slope_p50"] - 10.0) < 0.1
    assert stats["frac_gt8"] == pytest.approx(1.0)
    assert stats["frac_gt15"] == pytest.approx(0.0)


def test_flat_plane():
    dem = np.zeros((200, 200))
    res = 30.0
    stats = slope_stats(dem, res)
    assert stats["frac_gt8"] == pytest.approx(0.0)
    shad = shadow_fraction(dem, res, max_dist_m=1500.0, exclude_border_m=1500.0)
    for key in ["shadow_e2", "shadow_e5", "shadow_e7"]:
        assert shad[key] == pytest.approx(0.0, abs=1e-6)
    rough = roughness_spectrum(dem, res)
    for s in [1, 2, 4, 8, 16]:
        assert rough[f"rms_s{s}"] == pytest.approx(0.0, abs=1e-6)


def test_fbm_hurst():
    surface = make_fbm(1024, H=0.7, seed=42)
    # Scale to reasonable elevation range
    surface = surface / surface.std() * 10  # 10m std
    rough = roughness_spectrum(surface, res_m=30.0)
    assert abs(rough["hurst"] - 0.7) < 0.15


def test_aggregate_integer_factor():
    # 5m res → 30m: factor 6, 300×300 (divisible by 6)
    rng = np.random.default_rng(0)
    n = 300
    dem = rng.standard_normal((n, n)) * 10
    orig_mean = np.nanmean(dem)
    agg = aggregate_to_baseline(dem, res_m=5.0, L_m=30.0)
    assert agg.shape == (50, 50)
    assert abs(np.nanmean(agg) - orig_mean) / (abs(orig_mean) + 1e-9) < 1e-6


def test_aggregate_raises_on_superresolution():
    dem = np.ones((100, 100))
    with pytest.raises(ValueError):
        aggregate_to_baseline(dem, res_m=30.0, L_m=10.0)


def test_aggregate_non_integer_factor():
    # 5m → 32m: factor 6.4, non-integer, should use Gaussian+zoom
    dem = np.ones((200, 200)) * 5.0
    agg = aggregate_to_baseline(dem, res_m=5.0, L_m=32.0)
    assert agg is not None  # just check it runs
    assert np.all(np.isfinite(agg))


def test_shadow_box():
    # Flat ground with 100m tall box in center
    n = 200
    res = 30.0
    dem = np.zeros((n, n))
    cx, cy = n // 2, n // 2
    bsize = 3
    dem[cx - bsize : cx + bsize, cy - bsize : cy + bsize] = 100.0
    shad = shadow_fraction(dem, res, max_dist_m=1500.0, exclude_border_m=1500.0)
    assert shad["shadow_e2"] > 0
    assert shad["shadow_e2"] >= shad["shadow_e5"] >= shad["shadow_e7"]


def test_nan_robustness():
    rng = np.random.default_rng(1)
    n = 200
    res = 30.0
    x = np.arange(n) * res
    dem = np.outer(np.ones(n), x) * np.tan(np.radians(10.0))
    # Insert 10% NaN
    mask = rng.random((n, n)) < 0.1
    dem[mask] = np.nan
    stats = slope_stats(dem, res)
    assert abs(stats["slope_p50"] - 10.0) < 0.2


def test_terrain_descriptors_keys():
    result = terrain_descriptors(np.zeros((340, 340)), res_m=30.0, L_m=30.0, footprint_m=4000)
    for key in ["slope_p50", "slope_p90", "frac_gt8", "shadow_e2", "rms_s1", "hurst", "L_m"]:
        assert key in result


def test_terrain_descriptors_requires_L_m():
    with pytest.raises(TypeError):
        terrain_descriptors(np.zeros((50, 50)), res_m=30.0)


def test_shadow_from_buffer():
    # 10km chip at 30m = ~333 pixels; footprint 4km = ~133px; buffer = 3km = ~100px
    # Place a 200m tall block 1km outside footprint edge (in buffer), on one azimuth side
    n = 334
    res = 30.0
    dem = np.zeros((n, n))
    center = n // 2
    # block is in buffer, northward (top of image)
    # footprint edge at center-67=100; 1km into buffer = 33px; block at row 67
    block_row = center - 67 - 33  # 1km into buffer from footprint edge
    if block_row < 0:
        block_row = 10
    dem[block_row : block_row + 5, center - 3 : center + 3] = 200.0
    shad = shadow_fraction(dem, res, exclude_border_m=3000.0)
    # At e=2°, there should be some shadow from the block
    assert shad["shadow_e2"] > 0


def test_terrain_descriptors_non_square_chip():
    """Footprint is taken at the true centre of a non-square chip."""
    from similitude.descriptors.terrain import terrain_descriptors

    rows, cols = 340, 400
    yy, xx = np.mgrid[0:rows, 0:cols]
    # 10° plane only inside the central 4 km footprint, flat elsewhere
    dem = np.zeros((rows, cols))
    cr, cc, half = rows // 2, cols // 2, 66
    sl = (slice(cr - half, cr + half), slice(cc - half, cc + half))
    dem[sl] = np.tan(np.radians(10.0)) * 30.0 * xx[sl]
    out = terrain_descriptors(dem, 30.0, 30.0, footprint_m=4000)
    assert abs(out["slope_p50"] - 10.0) < 0.5


def test_shadow_fraction_empty_inner_raises():
    from similitude.descriptors.terrain import shadow_fraction

    with pytest.raises(ValueError):
        shadow_fraction(np.zeros((50, 50)), 30.0, max_dist_m=3000.0)
