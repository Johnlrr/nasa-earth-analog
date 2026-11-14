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
    out = disc.select_hidden(fid, earth, {}, LENS_M1)
    assert list(out["cell_id"]) == ["a"]


def test_permafrost_gate_for_x1():
    lens = {"id": "X1", "footprint_km": 10, "gates": {"permafrost_min": 0.5},
            "descriptors": ["permafrost_flag"]}
    fid = pd.DataFrame([fid_row("hot", 1.0, 0.5, 99.0, lens="X1"),
                        fid_row("cold", 1.2, 0.6, 98.0, lens="X1")])
    earth = pd.DataFrame([earth_row("hot", 20, 10, permafrost_flag=0.0),
                          earth_row("cold", 75, 10, permafrost_flag=1.0)])
    assert list(disc.select_hidden(fid, earth, {}, lens)["cell_id"]) == ["cold"]


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
