"""B0 contract tests: config files are consistent and the candidates schema bites."""

import copy
import json

import pytest

from similitude import io

MOCK = io.REPO_ROOT / "web" / "data" / "candidates.mock.geojson"


@pytest.fixture()
def mock_doc():
    with open(MOCK, encoding="utf-8") as fh:
        return json.load(fh)


def test_mock_file_is_valid():
    assert io.validate_candidates(MOCK) == 3


def test_mock_covers_every_mvp_lens(mock_doc):
    lenses = set()
    for f in mock_doc["features"]:
        lenses |= set(f["properties"]["lens_scores"])
    assert lenses == {"L1", "L2", "M1", "X1"}


def test_missing_evidence_status_is_rejected(mock_doc):
    del mock_doc["features"][0]["properties"]["evidence_status"]
    errors = io.check_candidates(mock_doc)
    assert any("evidence_status" in e for e in errors)


def test_bad_evidence_status_value_is_rejected(mock_doc):
    mock_doc["features"][0]["properties"]["evidence_status"] = "confirmed"
    assert io.check_candidates(mock_doc)


def test_validate_raises_with_all_errors(tmp_path, mock_doc):
    bad = copy.deepcopy(mock_doc)
    del bad["features"][0]["properties"]["evidence_status"]
    del bad["features"][1]["properties"]["data_sources"]
    p = tmp_path / "bad.geojson"
    p.write_text(json.dumps(bad), encoding="utf-8")
    with pytest.raises(io.CandidateValidationError) as exc:
        io.validate_candidates(p)
    assert len(exc.value.errors) >= 2


def test_percentile_may_be_null_but_must_be_present(mock_doc):
    assert mock_doc["features"][2]["properties"]["lens_scores"]["X1"]["percentile"] is None
    assert io.check_candidates(mock_doc) == []
    del mock_doc["features"][2]["properties"]["lens_scores"]["X1"]["percentile"]
    assert io.check_candidates(mock_doc)


def test_geometry_must_match_lat_lon(mock_doc):
    mock_doc["features"][0]["geometry"]["coordinates"] = [0.0, 0.0]
    errors = io.check_candidates(mock_doc)
    assert any("geometry" in e for e in errors)


def test_x1_only_cannot_be_engine_confirmed(mock_doc):
    mock_doc["features"][2]["properties"]["evidence_status"] = "engine-confirmed"
    errors = io.check_candidates(mock_doc)
    assert any("engine-semiquant" in e for e in errors)


def test_unknown_lens_rejected(mock_doc):
    scores = mock_doc["features"][0]["properties"]["lens_scores"]
    scores["Z9"] = scores["L1"]
    assert io.check_candidates(mock_doc)


def test_duplicate_ids_rejected(mock_doc):
    mock_doc["features"][1]["properties"]["id"] = mock_doc["features"][0]["properties"]["id"]
    errors = io.check_candidates(mock_doc)
    assert any("duplicate" in e for e in errors)


# ---------------- config consistency ----------------


def test_lenses_have_required_fields():
    lenses = io.load_lenses()
    assert set(lenses) == {"L1", "L2", "M1", "X1"}
    for lens in lenses.values():
        for key in ("id", "body", "footprint_km", "baseline", "descriptors", "min_scale",
                    "gates", "targets", "ledger"):
            assert key in lens, f"{lens['id']} missing {key}"
        for d in lens["descriptors"]:
            io.min_scale_for(lens, d, target_value=1.0)  # every descriptor has a tolerance


def test_l1_l2_footprint_is_4km():
    lenses = io.load_lenses()
    assert lenses["L1"]["footprint_km"] == 4 and lenses["L2"]["footprint_km"] == 4


def test_l1_descriptors_match_terrain_library():
    import numpy as np

    from similitude.descriptors.terrain import roughness_spectrum, slope_stats

    dem = np.random.default_rng(0).normal(size=(64, 64))
    keys = set(slope_stats(dem, 30.0)) | set(roughness_spectrum(dem, 30.0))
    assert set(io.load_lenses()["L1"]["descriptors"]) <= keys


def test_lens_targets_exist():
    targets = io.load_targets()
    for lens in io.load_lenses().values():
        for t in lens["targets"]:
            assert t in targets, f"{lens['id']}: unknown target {t}"
            assert lens["id"] in targets[t]["lenses"]


def test_controls_complete_and_locked_fields():
    controls = io.load_controls()
    assert len(controls) >= 10
    ids = [c["id"] for c in controls]
    assert len(ids) == len(set(ids))
    lenses = io.load_lenses()
    for c in controls:
        for key in ("lens_id", "lat", "lon", "footprint_km", "source", "expected",
                    "expected_rgb", "role"):
            assert key in c, f"{c['id']} missing {key}"
        assert c["lens_id"] in lenses
        assert c["expected"] in {"high", "uncertain", "low"}
        assert c["expected_rgb"] in {"high", "uncertain", "low"}
    # M1 controls must lie inside EMIT coverage (PLAN edge case)
    for c in controls:
        if c["lens_id"] == "M1":
            assert abs(c["lat"]) <= 52
    roles = {(c["lens_id"], c["role"]) for c in controls}
    assert ("M1", "decoy") in roles and ("M1", "positive") in roles


def test_m1_pixel_match_rules_preregistered():
    """B14a: the pixel-match rules exist and are internally consistent before B13 runs."""
    from similitude.descriptors import spectral as sp

    lens = io.load_lenses()["M1"]
    pm = lens["pixel_match"]
    swir = set(sp.SWIR_PARAMS)
    assert set(pm["diagnostic"]) == set(lens["analog_targets"])
    for tid, spec in pm["diagnostic"].items():
        assert spec["params"] and set(spec["params"]) <= swir, tid
        assert set(spec["params"]) <= set(lens["descriptors"]), tid  # no excluded parameter
        assert spec["mica_phase"]
    assert pm["diagnostic"]["nili_fossae_olivine"]["target_variant"]["OLINDEX"] == "ratioed"
    assert 0 < pm["frac_of_target"] <= 1
    assert pm["noise_floor_min"] == 0.01 and pm["noise_floor_quantile"] == 0.95
    assert pm["connectivity"] == 8 and pm["pass_largest_patch_km2"] == 0.1
    assert pm["scene_rule"] == "most_valid_pixels"
    nf = pm["noise_floor"]
    if nf is not None:  # filled in B14b: one floor per diagnostic parameter, never below min
        used = {p for spec in pm["diagnostic"].values() for p in spec["params"]}
        assert set(nf) == used and min(nf.values()) >= pm["noise_floor_min"]
    for k in ("HCPINDEX", "BD2250", "MIN2250"):
        assert k not in lens["descriptors"] and k in lens["excluded_descriptors"]
    assert lens["unobserved_variables"] and io.load_lenses()["X1"]["unobserved_variables"]


def test_a15_contract_for_m1_x1():
    """verdict_variables / unobserved (structured) for Linh's lenses, ledger variable+facility."""
    import json

    lenses = io.load_lenses()
    for lid in ("M1", "X1"):
        lens = lenses[lid]
        assert lens["verdict_variables"]
        for var, spec in lens["verdict_variables"].items():
            assert {"test", "targets", "source", "rule"} <= set(spec), (lid, var)
            assert set(spec["targets"]) <= set(lens["targets"]), (lid, var)
        for u in lens["unobserved"]:
            assert {"variable", "reason", "facility"} <= set(u), lid
    for body in ("moon", "mars"):
        led = io.load_yaml(io.REPO_ROOT / "ledger" / f"{body}.yaml")
        for it in led["items"]:
            assert it.get("variable") and it.get("facility"), (body, it["id"])
    sr = json.loads((io.REPO_ROOT / "data/derived/m1_stop_rule.json").read_text(encoding="utf-8"))
    assert isinstance(sr["m1_controls_pass"], bool)
    assert sr["m1_controls_pass"] == (sr["verdict"] == "PASS")


# ---------------- B17: site features (2c contract) ----------------


def site_feature(**over):
    props = {"feature_type": "site", "id": "site:E10K_729_-319", "site_id": "site:E10K_729_-319",
             "name": "Peary Land, North Greenland", "lat": 82.6, "lon": -33.1, "n_cells": 1,
             "member_cells": ["E10K_729_-319"], "max_span_km": 0.0, "lenses": ["L1"],
             "lenses_engine_confirmed": ["L1"], "lenses_engine_semiquant": ["X1"],
             "lenses_hypothesis": [], "lenses_literature_only": [], "b10_unreviewed_cells": [],
             "hidden_status": "unknown: attention not known", "attention_n": None,
             "n_in_exclusion": 0,
             "field": [{"lens": "L1", "target": "connecting_ridge", "variable": "slope_roughness",
                        "value": 41.0, "reason": "robust set"}],
             "facility": [{"lens": "L1", "target": None, "variable": "gravity", "value": 0.165,
                           "reason": "r", "facility": "offload rig", "source": "https://x"}],
             "unobserved": [{"lens": "L1", "variable": "boulders", "reason": "30 m DEM"}]}
    props.update(over)
    return {"type": "Feature", "geometry": {"type": "Point", "coordinates": [props["lon"],
                                                                             props["lat"]]},
            "properties": props}


def test_site_feature_valid_next_to_cell_candidates(mock_doc):
    mock_doc["features"].append(site_feature())
    assert io.check_candidates(mock_doc) == []


def test_site_with_x1_engine_confirmed_is_rejected():
    doc = {"type": "FeatureCollection",
           "features": [site_feature(lenses_engine_confirmed=["L1", "X1"],
                                     lenses_engine_semiquant=[])]}
    errors = io.check_candidates(doc)
    assert any("X1 can never be engine-confirmed" in e for e in errors)


def test_site_hidden_needs_known_low_attention_and_no_exclusion():
    doc = {"type": "FeatureCollection", "features": [site_feature(hidden_status="yes")]}
    assert any("known attention" in e for e in io.check_candidates(doc))
    doc = {"type": "FeatureCollection",
           "features": [site_feature(hidden_status="yes", attention_n=2, n_in_exclusion=1)]}
    assert any("exclusion zone" in e for e in io.check_candidates(doc))
    doc = {"type": "FeatureCollection",
           "features": [site_feature(hidden_status="yes", attention_n=2)]}
    assert io.check_candidates(doc) == []


def test_site_facility_rows_need_a_source_and_counts_match():
    bad = site_feature()
    del bad["properties"]["facility"][0]["source"]
    assert io.check_candidates({"type": "FeatureCollection", "features": [bad]})
    doc = {"type": "FeatureCollection", "features": [site_feature(n_cells=2)]}
    assert any("member_cells" in e for e in io.check_candidates(doc))
    doc = {"type": "FeatureCollection",
           "features": [site_feature(lenses_hypothesis=["L1"])]}
    assert any("in both" in e for e in io.check_candidates(doc))
