import numpy as np

from similitude.relocate import footprint_fraction, relocate


def test_dry_footprint_not_moved():
    mask = np.ones((41, 41), bool)
    r = relocate(mask, footprint_px=9, res_m=100)
    assert not r.moved and r.found and r.frac_before == 1.0


def test_half_water_footprint_moves_to_shore():
    # West half water, east half land; centre sits just inside the water.
    mask = np.zeros((41, 41), bool)
    mask[:, 22:] = True
    r = relocate(mask, footprint_px=9, res_m=100)
    assert r.frac_before < 0.5
    assert r.moved and r.found and r.frac_after >= 0.5
    assert r.d_row == 0 and r.d_col > 0  # moved straight east, nothing more
    assert r.shift_m == r.d_col * 100


def test_lake_centre_moves_to_nearest_shore():
    # Round lake of radius 12 px, off-centre to the south: the nearest valid
    # footprint lies north of the original point.
    yy, xx = np.mgrid[:61, :61]
    mask = ((yy - 34) ** 2 + (xx - 30) ** 2) > 12**2
    r = relocate(mask, footprint_px=9, res_m=60)
    assert r.moved and r.d_row < 0 and r.frac_after >= 0.5


def test_no_valid_land_reports_not_found():
    r = relocate(np.zeros((21, 21), bool), footprint_px=5, res_m=100)
    assert not r.found and not r.moved


def test_edge_counts_as_invalid():
    frac = footprint_fraction(np.ones((5, 5), bool), 3)
    assert frac[0, 0] < 1.0 and frac[2, 2] == 1.0
