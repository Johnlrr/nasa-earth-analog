import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

import build_verdicts as bv  # noqa: E402

L1 = {"id": "L1", "name": "Touchdown & Traverse"}
L2 = {"id": "L2", "name": "Low-Sun Navigation"}
M1 = {"id": "M1", "name": "Aqueous Minerals", "analog_targets": ["jezero_margin"],
      "unobserved_targets": {"oxia_planum": "empty match"},
      "pixel_match": {"pass_largest_patch_km2": 0.1}}
X1 = {"id": "X1", "name": "Ice", "primary_target": "arcadia_planitia"}


def _frame(rows):
    df = pd.DataFrame(rows, columns=bv.COLUMNS)
    bv.check(df)
    return df


def _robust(**kw):
    base = {"cell_id": "a", "target_id": "t", "sample_role": "rank", "nms_keep": True,
            "robust": True, "set_rule": "intersection", "score": 40.0,
            "nr_i": 40, "nr_ii": 40, "nr_iii": 40, "n_i": 49}
    return {**base, **kw}


def test_l1_only_robust_rank_seed_cells_get_rows():
    robust = pd.DataFrame([
        _robust(cell_id="in"),
        _robust(cell_id="null_in", sample_role="null"),
        _robust(cell_id="out", nms_keep=False, robust=False),
    ])
    df = _frame(bv.l1_rows(L1, robust))
    cells = set(df[df.cell_id != ""].cell_id)
    assert cells == {"in"}
    lens = df[df.cell_id == ""].iloc[0]
    assert lens.state == "TRANSFERS" and lens.value == 1


def test_l1_empty_set_is_lens_no_analog():
    robust = pd.DataFrame([_robust(nms_keep=False, robust=False)])
    df = _frame(bv.l1_rows(L1, robust))
    assert len(df) == 1 and df.state.iloc[0] == "NO-ANALOG"


def test_l2_sun_no_analog_and_shadow_by_native_rank():
    fid = pd.DataFrame({
        "cell_id": ["a", "b"], "target_id": "t", "sigma": [14.0, 15.0], "no_analog": True,
        "native_rank": [30.0, 10.0], "n_native": 49, "sigma_shadow": [0.5, 1.5]})
    earth = pd.DataFrame({"cell_id": ["a", "b"], "sample_role": "rank",
                          "lowsun_frac_daylight": [0.28, 0.1]})
    targets = pd.DataFrame({"target_id": ["t"], "is_reference": [True],
                            "lowsun_frac_daylight": [1.0]})
    df = _frame(bv.l2_rows(L2, fid, earth, targets))
    sun = df[df.variable == "sun_geometry"].iloc[0]
    assert sun.state == "NO-ANALOG" and sun.value == 14.0
    shadow_cells = df[(df.variable == "shadow_casting") & (df.cell_id != "")]
    assert shadow_cells.cell_id.tolist() == ["a"]


def test_m1_without_pixel_table_has_only_unobserved():
    df = _frame(bv.m1_rows(M1, None, None))
    assert set(df.state) == {"UNOBSERVED"} and (df.cell_id == "").all()


def test_m1_stop_rule_fail_blocks_cell_transfers():
    pixels = pd.DataFrame({"cell_id": ["s"], "target_id": "jezero_margin", "sample_role": "seed",
                           "largest_patch_km2": [19.0], "matched_area_km2": [25.0]})
    stop = {"verdict": "FAIL", "largest_patch_km2": {"ctl_lake_salda__relocated": 0.05}}
    df = _frame(bv.m1_rows(M1, stop, pixels))
    assert not ((df.cell_id != "") & (df.state == "TRANSFERS")).any()
    assert "FAIL" in df[df.target_id == "jezero_margin"].reason.iloc[0]


def test_m1_stop_rule_pass_uses_patch_threshold():
    pixels = pd.DataFrame({"cell_id": ["big", "small"], "target_id": "jezero_margin",
                           "sample_role": "rank", "largest_patch_km2": [0.5, 0.05],
                           "matched_area_km2": [1.0, 0.1]})
    df = _frame(bv.m1_rows(M1, {"verdict": "PASS"}, pixels))
    states = df.set_index("cell_id").state
    assert states["big"] == "TRANSFERS" and states["small"] == "NO-ANALOG"


def test_x1_checklist_states():
    chk = pd.DataFrame({
        "cell_id": ["ok", "ice", "fail", "n", "c"],
        "sample_role": ["rank", "rank", "seed", "null", "control"],
        "candidate": [True, False, False, True, True],
        "passes_all": [True, True, False, True, True],
        "ice_check": ["ok", "excluded: glacier ice", "ok", "ok", "ok"],
        "failed": ["-", "-", "no_thaw_to_ice", "-", "-"], "n_met": [3, 3, 2, 3, 3]})
    df = _frame(bv.x1_rows(X1, chk)).set_index("cell_id")
    assert df.loc["ok", "state"] == "TRANSFERS"
    assert df.loc["ice", "state"] == "NO-ANALOG" and "glacier" in df.loc["ice", "reason"]
    assert "no_thaw_to_ice" in df.loc["fail", "reason"]
    assert "n" not in df.index and "c" not in df.index  # only rank/seed are candidates
    assert df.loc["", "value"] == 1


def test_ledger_default_no_analog_and_explicit_transfers():
    items = [
        {"id": "gravity", "applies_to": ["L1"], "ratio_target_over_earth": 0.165,
         "consequence": "c", "mitigation": "offload rig"},
        {"id": "day", "applies_to": ["L1"], "verdict": "TRANSFERS", "mitigation": "None needed"},
        {"id": "other", "applies_to": ["M1"]},
    ]
    df = _frame(bv.ledger_rows(L1, items)).set_index("variable")
    assert df.loc["gravity", "state"] == "NO-ANALOG"
    assert df.loc["gravity", "facility"] == "offload rig"
    assert df.loc["day", "state"] == "TRANSFERS" and df.loc["day", "facility"] == ""
    assert "other" not in df.index
    assert np.isnan(df.loc["day", "value"])
