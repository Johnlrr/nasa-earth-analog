"""B6 tests for the X1 ice-configuration descriptors."""

import math

import pytest

from similitude import io
from similitude.descriptors import ice


def test_keys_match_x1_lens():
    out = ice.ice_config(-10, 0.5, 0.1, 5)
    assert set(out) == set(io.load_lenses()["X1"]["descriptors"])


def test_mars_arcadia_configuration():
    out = ice.ice_config(-60, 0.5, 0.0, 0)
    assert out == {"permafrost_flag": 1.0, "ice_depth_ratio": 0.5, "aridity_p_pet": 0.0,
                   "ft_cycles_yr": 0.0}


def test_no_permafrost_puts_ice_out_of_reach():
    out = ice.ice_config(15, 2.0, 0.05, 0)
    assert out["permafrost_flag"] == 0.0
    assert out["ice_depth_ratio"] == ice.ICE_RATIO_CAP


def test_permafrost_flag_is_linear_between_0_and_minus2():
    assert ice.ice_config(-1, 0.5, 0.1, 0)["permafrost_flag"] == pytest.approx(0.5)


def test_bounds_and_caps():
    out = ice.ice_config(-20, 9.0, 7.0, -3)
    assert out["ice_depth_ratio"] == ice.ICE_RATIO_CAP
    assert out["aridity_p_pet"] == ice.ARIDITY_CAP
    assert out["ft_cycles_yr"] == 0.0


def test_nan_inputs_propagate_without_crash():
    out = ice.ice_config(None, None, float("nan"), None)
    assert all(math.isnan(v) for v in out.values())


def test_stefan_active_layer():
    assert ice.stefan_active_layer(400) == pytest.approx(0.6)
    assert ice.stefan_active_layer(-5) == 0.0
    assert math.isnan(ice.stefan_active_layer(float("nan")))


def test_dry_cold_desert_closer_to_mars_than_wet_permafrost():
    mars = ice.ice_config(-60, 0.5, 0.0, 0)
    dry = ice.ice_config(-12, ice.stefan_active_layer(300), 0.08, 15)
    wet = ice.ice_config(-6, ice.stefan_active_layer(1500), 0.9, 40)

    def dist(a, b):
        scale = {"permafrost_flag": 0.25, "ice_depth_ratio": 0.25, "aridity_p_pet": 0.05,
                 "ft_cycles_yr": 10.0}
        return math.sqrt(sum(((a[k] - b[k]) / s) ** 2 for k, s in scale.items()))

    assert dist(dry, mars) < dist(wet, mars)


def test_aridity_index_pet_floor_keeps_polar_desert_dry():
    polar = ice.aridity_index(150, 20)       # Peary-Land-like: tiny PET
    siberia = ice.aridity_index(450, 450)
    assert polar == pytest.approx(0.3) and polar < siberia
    assert math.isnan(ice.aridity_index(float("nan"), 100))
