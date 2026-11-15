"""PLAN 2d: mission criteria, validity summary and coverage are readings of existing tables."""

import json
import sys

import pandas as pd
import pytest

from similitude import io

sys.path.insert(0, str(io.REPO_ROOT / "scripts"))
import mission_value as mv  # noqa: E402

DERIVED = io.REPO_ROOT / "data" / "derived"


def _targets():
    return pd.DataFrame({
        "target_id": ["t", "t", "t", "u"], "is_reference": [True, False, False, True],
        "slope_p50": [12.0, 8.0, 15.0, 30.0], "frac_gt8": [0.7, 0.5, 0.9, 0.99],
        "frac_gt20": [0.05, 0.01, 0.2, 0.9]})


def _earth():
    return pd.DataFrame({
        "cell_id": ["A", "CTRL_x", "CTRL_y", "CTRL_y_reloc"],
        "name": ["a", "x", "y", "y moved"], "sample_role": ["rank", "control", "control", "extra"],
        "in_exclusion_buffer": [False, False, False, False],
        "slope_p50": [11.0, 3.0, 1.0, 2.0], "frac_gt8": [0.6, 0.1, 0.05, 0.95],
        "frac_gt20": [0.3, 0.0, 0.0, 0.1]})


def test_relocated_control_replaces_the_original():
    assert set(mv.classic_controls(_earth())["cell_id"]) == {"CTRL_x", "CTRL_y_reloc"}


def test_mission_criteria_range_is_the_targets_own_footprints():
    c = mv.mission_criteria(_targets(), _earth(), ["A"], target="t").set_index("id")
    assert c.loc["t", "group"] == "Moon target" and c.loc["t", "frac_gt8"] == 0.7
    assert c.loc["A", "in_range_frac_gt8"] and not c.loc["A", "in_range_frac_gt20"]  # 0.3 > 0.2
    assert not c.loc["CTRL_x", "in_range_frac_gt8"]
    assert not c.loc["CTRL_y_reloc", "in_range_frac_gt8"]                             # 0.95 > 0.9
    assert c["n_target_footprints"].iloc[0] == 3 and "u" not in c.index


def test_null_rate_and_rediscovery_counts():
    robust = pd.DataFrame({
        "target_id": ["t"] * 6, "cell_id": list("abcdef"),
        "sample_role": ["null", "null", "null", "null", "rank", "rank"],
        "robust": [True, False, False, False, True, False]})
    r = mv.l1_null_rate(robust)[0]
    assert (r["robust_null"], r["n_null"], r["robust_rank"], r["n_rank"]) == (1, 4, 1, 2)
    assert r["null_ci_lo"] < 0.25 < r["null_ci_hi"]
    tier1 = pd.DataFrame({"cell_id": [f"c{i}" for i in range(100)],
                          "in_exclusion_buffer": [True] * 2 + [False] * 98})
    earth = pd.DataFrame({"cell_id": ["e", "f"], "sample_role": ["rank", "rank"],
                          "in_exclusion_buffer": [True, False]})
    d = mv.rediscovery(tier1, earth, robust)
    assert d["base_rate"] == 0.02 and d["rank_in_zone"] == 1 and d["rank_enrichment"] == 25.0
    t = d["targets"][0]
    assert (t["robust_in_zone"], t["robust_n"], t["other_in_zone"], t["other_n"]) == (1, 1, 0, 1)


def test_coverage_takes_one_state_per_lens_variable_and_ignores_cells():
    v = pd.DataFrame({
        "lens_id": ["L1", "L1", "L1", "L1"], "target_id": ["a", "b", "", ""],
        "cell_id": ["", "", "", "X"], "variable": ["v", "v", "g", "v"],
        "state": ["NO-ANALOG", "TRANSFERS", "NO-ANALOG", "TRANSFERS"],
        "facility": ["", "", "rig", ""]})
    c = mv.coverage(v).set_index("variable")
    assert len(c) == 2 and c.loc["v", "state"] == "TRANSFERS" and c.loc["g", "facility"] == "rig"


def test_requirements_are_quoted_with_a_source():
    for key, r in mv.CFG["requirements"].items():
        assert r["quote"] and r["document"] and r["source"].startswith("https://"), key
    for lens, p in mv.CFG["protocols"].items():
        assert all(k in mv.CFG["requirements"] for k in p["requirement"]), lens


# ---- committed tables -----------------------------------------------------------------------
@pytest.fixture(scope="module")
def built():
    if not (DERIVED / "mission_value.json").exists():
        pytest.skip("mission_value.json not built")
    return mv.build(attention_enabled=False)


def test_committed_mission_value_matches_a_rebuild(built):
    saved = json.loads((DERIVED / "mission_value.json").read_text(encoding="utf-8"))
    saved.pop("generated")
    assert json.loads(json.dumps(built["value"])) == saved
    crit = pd.read_parquet(DERIVED / "mission_criteria.parquet")
    pd.testing.assert_frame_equal(crit, built["criteria"])


def test_coverage_matches_verdicts_and_every_facility_row_names_a_facility_or_is_a_result(built):
    v = pd.read_parquet(DERIVED / "verdicts.parquet")
    lens_level = v[v["cell_id"].fillna("").eq("")]
    cov = built["coverage"]
    assert set(zip(cov["lens_id"], cov["variable"], strict=True)) == set(
        zip(lens_level["lens_id"], lens_level["variable"], strict=True))
    total = sum(sum(c.values()) for c in built["value"]["coverage"].values())
    assert total == len(cov)


def test_protocols_cover_every_published_lens_of_the_showcase_sites():
    cards = json.loads((DERIVED / "field_facility.json").read_text(encoding="utf-8"))["sites"]
    text = (io.REPO_ROOT / "docs" / "test_protocols.md").read_text(encoding="utf-8")
    for c in cards:
        assert f"### {c['name']}" in text
        for lens in (c["lenses_engine_confirmed"] + "," + c["lenses_engine_semiquant"]).split(","):
            assert not lens or lens in mv.CFG["protocols"]
    assert "does not assign or certify a TRL" in text


def test_every_slide_key_exists_in_slide_numbers():
    import re

    text = (io.REPO_ROOT / "docs" / "slides_draft.md").read_text(encoding="utf-8")
    numbers = json.loads((io.REPO_ROOT / "docs" / "slide_numbers.json").read_text(
        encoding="utf-8"))["numbers"]
    keys = set(re.findall(r"`([A-Za-z0-9_]+)`", " ".join(re.findall(r"\[([^\]]*)\]", text))))
    assert keys and not sorted(k for k in keys if k not in numbers)


def test_values_typed_beside_a_slide_key_match_slide_numbers():
    import re

    text = (io.REPO_ROOT / "docs" / "slides_draft.md").read_text(encoding="utf-8")
    numbers = json.loads((io.REPO_ROOT / "docs" / "slide_numbers.json").read_text(
        encoding="utf-8"))["numbers"]
    pairs = re.findall(r"`([A-Za-z0-9_]+)`\s*=\s*([0-9.]+)", text)
    assert pairs
    for key, typed in pairs:
        assert abs(float(numbers[key]["value"]) - float(typed.rstrip("."))) < 0.01, key
