import numpy as np

from similitude.descriptors.astro import low_sun_hours, low_sun_windows


def test_equator_and_mid_latitude_have_no_window():
    assert low_sun_windows(0.0)["window_days"] == 0
    assert low_sun_windows(-28.8)["window_days"] == 0


def test_window_starts_where_noon_sun_drops_below_threshold():
    # noon elevation = 90 - lat + decl <= 7  ->  decl <= lat - 83; at 63.85 N: decl <= -19.15
    w = low_sun_windows(63.85)
    decl_lim = np.radians(63.85 - 83.0)
    days = np.arange(365)
    decl = np.radians(23.44) * np.sin(2 * np.pi * (days + 0.5) / 365)
    expect = int((decl <= decl_lim + 1e-9).sum())
    assert abs(w["window_days"] - expect) <= 2
    assert 55 <= w["window_days"] <= 80
    # window centred on the December solstice (model day ~274)
    mid = (w["window_first_day"] + (w["window_days"] - 1) / 2) % 365
    assert abs(mid - 274) <= 3


def test_polar_night_days_are_not_window_days():
    w = low_sun_windows(80.0)
    assert w["window_days"] < 60  # mostly polar night or high sun


def test_consistent_with_low_sun_hours():
    a = low_sun_hours(63.85)
    w = low_sun_windows(63.85)
    assert abs(w["lowsun_min_per_day"] - a["lowsun_frac_time"] * 1440) < 1e-6
