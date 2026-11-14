import pytest

from similitude.descriptors.astro import low_sun_hours


def test_lowsun_frac_lat0_vs_lat85():
    low0 = low_sun_hours(0.0)
    low85 = low_sun_hours(85.0)
    assert low0["lowsun_frac_daylight"] < low85["lowsun_frac_daylight"]


def test_lat85_az_coverage():
    result = low_sun_hours(85.0)
    assert result["lowsun_az_coverage"] > 0.9


def test_lat0_az_coverage():
    result = low_sun_hours(0.0)
    assert result["lowsun_az_coverage"] < 0.5


def test_moon_south_pole():
    result = low_sun_hours(-89.5, obliquity_deg=1.54)
    assert result["lowsun_frac_daylight"] == pytest.approx(1.0, abs=0.01)
    assert result["lowsun_az_coverage"] == pytest.approx(1.0, abs=0.01)


def test_all_values_in_range():
    for lat in [-89.5, 0.0, 45.0, 85.0]:
        result = low_sun_hours(lat)
        assert 0 <= result["lowsun_frac_time"] <= 1
        assert 0 <= result["lowsun_frac_daylight"] <= 1
        assert 0 <= result["lowsun_az_coverage"] <= 1
        assert result["lowsun_hours_yr"] >= 0
