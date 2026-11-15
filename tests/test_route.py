import numpy as np

from similitude.route import _ascent_along_tree, robust_scale, route_distance, route_outcomes


def test_flat_plane_fully_reachable_no_detour():
    o = route_outcomes(np.zeros((80, 80)), 30.0)
    assert o["reach_6"] == 1.0 and o["reach_8"] == 1.0
    # 8-connected grid metric: detour of an octile path is between 1 and 1.083
    assert 1.0 <= o["detour_8"] <= 1.09
    assert o["climb_10"] == 0.0


def test_cliff_splits_grid():
    dem = np.zeros((80, 80))
    dem[:, 40:] = 500.0  # vertical wall between columns 39 and 40
    o = route_outcomes(dem, 30.0)
    assert 0.0 < o["reach_8"] < 1.0
    # only same-side pairs connect: compare with a direct count from the same sources
    rng = np.random.default_rng(20261115)
    src = rng.choice(np.arange(80 * 80), size=24, replace=False)
    yy, xx = np.divmod(np.arange(80 * 80), 80)
    same, tot = 0, 0
    for s in src:
        sy, sx = divmod(int(s), 80)
        e = 30.0 * np.hypot(yy - sy, xx - sx)
        sel = (e >= 1000) & (e <= 2500)
        tot += sel.sum()
        same += (sel & ((xx >= 40) == (sx >= 40))).sum()
    assert abs(o["reach_8"] - same / tot) < 1e-12


def test_steep_plane_blocks_low_limit():
    # 12 deg plane: up-slope edges 12 deg, diagonal edges 8.55 deg. At 8 deg only contour moves
    # remain (pairs on one row); at 10 deg a zigzag reaches everything with a detour
    y = np.arange(80)[:, None] * 30.0 * np.tan(np.radians(12.0))
    dem = np.repeat(y, 80, axis=1)
    o = route_outcomes(dem, 30.0)
    assert o["reach_8"] < 0.2
    assert o["detour_10"] > 1.05
    assert o["climb_10"] >= 0.0


def test_too_much_nodata_is_skipped():
    dem = np.zeros((50, 50))
    dem[:10] = np.nan
    o = route_outcomes(dem, 30.0)
    assert np.isnan(o["reach_6"]) and o["nan_frac"] > 0.05


def test_ascent_along_tree():
    # chain 0 <- 1 <- 2 <- 3 with heights 0, 5, 3, 10: ascents 0, 5, 5, 12
    pred = np.array([-9999, 0, 1, 2])
    z = np.array([0.0, 5.0, 3.0, 10.0])
    assert np.allclose(_ascent_along_tree(pred, z), [0, 5, 5, 12])


def test_distance_and_scale():
    nat = np.array([[0.5, 1.0], [0.7, 1.2], [0.9, 1.4]])
    s = robust_scale(nat)
    assert np.all(s > 0)
    d = route_distance(nat, nat[1], s)
    assert d[1] == 0.0 and d[0] > 0 and d[2] > 0
