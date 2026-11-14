"""B9 tests: exclusion flags, NMS, hidden-analog filter, evidence caps, Test Card export."""

import pandas as pd
import pytest

from similitude import discovery as disc
from similitude import io


def fid_row(cell, d, sigma, pct, target="t1", lens="M1"):
    return {"cell_id": cell, "lens_id": lens, "target_id": target, "d": d, "sigma": sigma,
            "sigma_capped": False, "metric_mode": "diag", "percentile": pct, "n_null": 60,
            "limiting_factor": "D2300", "no_analog": False}


def earth_row(cell, lat, lon, role="rank", qa="ok", excl=False, **kw):
    return {"cell_id": cell, "lat": lat, "lon": lon, "sample_role": role, "qa_flag": qa,
            "in_exclusion_buffer": excl, **kw}


LENS_M1 = {"id": "M1", "footprint_km": 5, "gates": {}, "descriptors": ["D2300"]}


def test_nms_two_cells_closer_than_footprint_keep_one():
    df = pd.DataFrame([{"cell_id": "a", "lat": 20.0, "lon": 40.0, "d": 1.0},
                       {"cell_id": "b", "lat": 20.02, "lon": 40.0, "d": 2.0},   # ~2.2 km away
                       {"cell_id": "c", "lat": 21.0, "lon": 40.0, "d": 3.0}])
    kept = disc.nms(df, footprint_km=5)
    assert list(kept["cell_id"]) == ["a", "c"]


def test_exclusion_flag_matches_bao_zone_types():
    assert disc.exclusion_flag(-70.0, 10.0)[0]            # lat_max (Antarctica)
    assert disc.exclusion_flag(64.0, -18.0)[0]            # bbox (Iceland)
    assert disc.exclusion_flag(-24.5, -69.3)[0]           # circle (Atacama)
    assert not disc.exclusion_flag(22.9, 58.5)[0]         # Oman


def test_select_hidden_filters_role_gate_buffer_fidelity_attention():
    fid = pd.DataFrame([fid_row("good", 1.0, 0.5, 99.0), fid_row("excluded", 0.5, 0.3, 99.5),
                        fid_row("null1", 0.8, 0.4, 99.0), fid_row("famous", 1.1, 0.6, 98.0),
                        fid_row("weak", 5.0, 3.0, 50.0), fid_row("badqa", 0.9, 0.4, 99.0)])
    earth = pd.DataFrame([earth_row("good", 10, 10), earth_row("excluded", 20, 20, excl=True),
                          earth_row("null1", 30, 30, role="null"), earth_row("famous", 40, 40),
                          earth_row("weak", 50, 50), earth_row("badqa", 15, 15, qa="low_valid")])
    att = {"good": 0, "famous": 200, "weak": 0}
    out = disc.select_hidden(fid, earth, att, LENS_M1)
    assert list(out["cell_id"]) == ["good"]


def test_select_hidden_uses_sigma_when_percentile_missing():
    fid = pd.DataFrame([fid_row("a", 1.0, 0.8, None), fid_row("b", 2.0, 1.5, None)])
    earth = pd.DataFrame([earth_row("a", 10, 10), earth_row("b", 30, 30)])
    out = disc.select_hidden(fid, earth, {"a": 0, "b": 0}, LENS_M1)
    assert list(out["cell_id"]) == ["a"]


def test_high_percentile_but_beyond_2_sigma_is_rejected():
    # Bao's rule (DESIGN 2.2(3)): when every cell is far, the closest still gets pct 100
    assert not disc.passes_fidelity({"sigma": 3.1, "percentile": 100.0})
    assert disc.passes_fidelity({"sigma": 1.9, "percentile": 95.0})


def test_l2_judged_on_sigma_shadow_not_total_sigma():
    row = {"sigma": 14.0, "sigma_shadow": 0.4, "percentile": 99.0}
    assert disc.passes_fidelity(row)
    assert not disc.passes_fidelity({**row, "sigma_shadow": 2.5})


def test_score_column_and_ranking_use_d_shadow_when_present():
    fid = pd.DataFrame([{**fid_row("a", 20.0, 14.0, 99.0, lens="L2"), "d_shadow": 3.0},
                        {**fid_row("b", 15.0, 10.0, 99.0, lens="L2"), "d_shadow": 9.0}])
    assert disc.score_column(fid) == "d_shadow"
    assert disc.score_column(fid.drop(columns="d_shadow")) == "d"
    df = fid.assign(lat=[10.0, 30.0], lon=[0.0, 0.0])
    assert list(disc.nms(df, 4, score=disc.score_column(fid))["cell_id"]) == ["a", "b"]


def test_both_id_conventions():
    assert disc.attention_key({"cell_id": "SEED_Harrat_Khaybar"}) == "harrat_khaybar"
    assert disc.attention_key({"cell_id": "CTRL_haughton_devon"}) == "haughton_devon"
    assert disc.control_cell_ids("wadi_rum") == ("ctl_wadi_rum", "CTRL_wadi_rum")


def test_permafrost_gate_for_x1():
    lens = {"id": "X1", "footprint_km": 10, "gates": {"permafrost_min": 0.5},
            "descriptors": ["permafrost_flag"]}
    fid = pd.DataFrame([fid_row("hot", 1.0, 0.5, 99.0, lens="X1"),
                        fid_row("cold", 1.2, 0.6, 98.0, lens="X1")])
    earth = pd.DataFrame([earth_row("hot", 20, 10, permafrost_flag=0.0),
                          earth_row("cold", 75, 10, permafrost_flag=1.0)])
    att = {"hot": 0, "cold": 0}
    assert list(disc.select_hidden(fid, earth, att, lens)["cell_id"]) == ["cold"]


def test_evidence_status_caps():
    assert disc.evidence_status("X1", "hidden") == "engine-semiquant"
    assert disc.evidence_status("M1", "hidden") == "engine-confirmed"
    assert disc.evidence_status("M1", "control") == "literature-only"
    assert disc.evidence_status("M1", "decoy") == "hypothesis"


def test_best_target_keeps_smallest_d_per_cell():
    fid = pd.DataFrame([fid_row("a", 3.0, 1, 90, target="t1"), fid_row("a", 2.0, 1, 90,
                                                                         target="t2")])
    assert disc.best_target(fid).iloc[0]["target_id"] == "t2"


def test_attention_key_strips_prefixes():
    assert disc.attention_key({"cell_id": "seed_harrat_khaybar"}) == "harrat_khaybar"
    assert disc.attention_key({"cell_id": "ctl_wadi_rum"}) == "wadi_rum"
    assert disc.attention_key({"cell_id": "rank_003"}) == "rank_003"


def test_cannot_test_reads_ledger_for_lens():
    lines = disc.cannot_test("M1")
    assert any("gravity" in s.lower() for s in lines)


def test_feature_from_lens_score_is_contract_valid():
    lens = io.load_lenses()["M1"]
    row = pd.Series(fid_row("seed_x", 2.5, 1.2, None, target="jezero_margin"))
    ls = disc.lens_score(row, lens)
    props = {"id": "M1-seed_x", "name": "X", "lat": 10.0, "lon": 20.0, "footprint_km": 5.0,
             "role": "hidden", "process_title": "t", "lens_scores": {"M1": ls},
             "test_here": disc.TEST_HERE["M1"], "cannot_test": disc.cannot_test("M1"),
             "attention": {"n_pubs": 0, "query": "q", "source": "OpenAlex", "date": "2026-11-14"},
             "evidence_status": "engine-confirmed", "data_sources": ["NASA EMIT"]}
    doc = {"type": "FeatureCollection", "features": [disc.feature(props)]}
    assert io.check_candidates(doc) == []
    assert ls["percentile"] is None


@pytest.mark.skipif(not (io.REPO_ROOT / "web/data/candidates.geojson").exists(),
                    reason="discovery not run yet")
def test_exported_candidates_file_is_valid():
    assert io.validate_candidates(io.REPO_ROOT / "web/data/candidates.geojson") > 0


def test_verdicts_read_not_generated():
    assert disc.verdicts_for(None, "L1", "c1") == []
    v = pd.DataFrame([
        {"lens_id": "L1", "target_id": "connecting_ridge", "cell_id": "c1", "test": "LTV traverse",
         "variable": "slope_roughness", "state": "TRANSFERS", "value": 30, "reason": "robust set",
         "facility": None},
        {"lens_id": "L1", "target_id": None, "cell_id": None, "test": "wheel sinkage",
         "variable": "gravity", "state": "NO-ANALOG", "value": 0.165, "reason": None,
         "facility": "offload rig"},
        {"lens_id": "L1", "target_id": "", "cell_id": "", "test": "landing safety",
         "variable": "boulders", "state": "UNOBSERVED", "value": None, "reason": "30 m DEM",
         "facility": "in situ"},
        {"lens_id": "L2", "target_id": "connecting_ridge", "cell_id": "c1", "test": "x",
         "variable": "y", "state": "TRANSFERS", "value": None, "reason": None, "facility": None},
        {"lens_id": "L1", "target_id": "connecting_ridge", "cell_id": "c2", "test": "x",
         "variable": "y", "state": "TRANSFERS", "value": None, "reason": None, "facility": None},
    ])
    out = disc.verdicts_for(v, "L1", "c1")
    assert [r["state"] for r in out] == ["TRANSFERS", "NO-ANALOG", "UNOBSERVED"]
    assert [r["scope"] for r in out] == ["cell", "lens", "lens"]
    assert out[0]["value"] == 30 and out[2]["value"] is None


def test_pixel_match_and_new_fields_are_contract_valid():
    px = pd.DataFrame([{"cell_id": "seed_x", "target_id": "jezero_margin",
                        "matched_area_km2": 3.333, "largest_patch_km2": 3.185}])
    pm = disc.pixel_match_for(px, "seed_x", "jezero_margin")
    assert pm == {"matched_area_km2": 3.333, "largest_patch_km2": 3.185,
                  "pixel_footprint": "original"}
    assert disc.pixel_match_for(px, "seed_x", "nili_fossae_olivine") == {}
    lens = io.load_lenses()["M1"]
    row = pd.Series({**fid_row("seed_x", 2.5, 1.2, 95.0, target="jezero_margin"),
                     "native_rank": 40, "n_native": 53, "native_rank_basis": "d"})
    ls = {**disc.lens_score(row, lens), **pm}
    assert ls["native_rank"] == 40 and ls["n_native"] == 53
    props = {"id": "M1-seed_x", "name": "X", "lat": 10.0, "lon": 20.0, "footprint_km": 5.0,
             "role": "control", "analog_role": "aqueous", "process_title": "t",
             "lens_scores": {"M1": ls}, "test_here": [], "cannot_test": [],
             "attention": {"n_pubs": 0, "query": "q", "source": "OpenAlex", "date": "d"},
             "evidence_status": "literature-only", "data_sources": ["NASA EMIT"],
             "verdicts": [{"lens": "M1", "scope": "lens", "test": "t", "variable": "v",
                           "state": "UNOBSERVED", "value": None, "reason": "r",
                           "facility": "f"}]}
    assert io.check_candidates({"type": "FeatureCollection",
                                "features": [disc.feature(props)]}) == []
    props["verdicts"][0]["state"] = "MAYBE"
    assert io.check_candidates({"type": "FeatureCollection", "features": [disc.feature(props)]})


def test_unknown_attention_is_not_hidden():
    fid = pd.DataFrame([fid_row("known", 1.0, 0.5, 99.0), fid_row("unknown", 0.9, 0.4, 99.0)])
    earth = pd.DataFrame([earth_row("known", 10, 10), earth_row("unknown", 30, 30)])
    att = {"known": 0}
    assert list(disc.select_hidden(fid, earth, att, LENS_M1)["cell_id"]) == ["known"]
    both = disc.select_hidden(fid, earth, att, LENS_M1, keep_unknown_attention=True)
    assert set(both["cell_id"]) == {"known", "unknown"}


def test_lens_level_transfers_summary_not_shown_and_transfers_cells():
    v = pd.DataFrame([
        {"lens_id": "L1", "target_id": "connecting_ridge", "cell_id": "c1", "test": "t",
         "variable": "slope_roughness", "state": "TRANSFERS", "value": 30, "reason": None,
         "facility": None},
        {"lens_id": "L1", "target_id": "connecting_ridge", "cell_id": None, "test": "t",
         "variable": "slope_roughness", "state": "TRANSFERS", "value": 5,
         "reason": "5 cells in the robust set", "facility": None},
        {"lens_id": "L1", "target_id": "shackleton_rim", "cell_id": "c2", "test": "t",
         "variable": "slope_roughness", "state": "TRANSFERS", "value": 10, "reason": None,
         "facility": None},
        {"lens_id": "L1", "target_id": None, "cell_id": None, "test": "t",
         "variable": "gravity", "state": "NO-ANALOG", "value": 0.165, "reason": None,
         "facility": "rig"},
    ])
    # a control outside the robust set: physics only, no summary TRANSFERS pretending to be its own
    ctrl = disc.verdicts_for(v, "L1", "ctrl_x", "connecting_ridge")
    assert [(r["variable"], r["state"]) for r in ctrl] == [("gravity", "NO-ANALOG")]
    c1 = disc.verdicts_for(v, "L1", "c1", "connecting_ridge")
    assert [(r["scope"], r["state"]) for r in c1] == [("cell", "TRANSFERS"), ("lens", "NO-ANALOG")]
    assert disc.transfers_cells(None, "L1") is None
    assert disc.transfers_cells(v, "L1") == {"c1": "connecting_ridge", "c2": "shackleton_rim"}
    assert disc.transfers_cells(v, "M1") == {}
    fid = pd.DataFrame([fid_row("c1", 1.0, 0.5, 50.0, lens="L1"),
                        fid_row("c3", 0.5, 0.2, 99.0, lens="L1")])
    earth = pd.DataFrame([earth_row("c1", 10, 10), earth_row("c3", 30, 30)])
    lens = {"id": "L1", "footprint_km": 4, "gates": {}, "descriptors": []}
    att = {"c1": 0, "c3": 0}
    out = disc.select_hidden(fid, earth, att, lens, transfers=disc.transfers_cells(v, "L1"))
    assert list(out["cell_id"]) == ["c1"]  # c3 has a better sigma but no TRANSFERS verdict
    assert disc.select_hidden(fid, earth, att, lens, transfers={}).empty
