import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

import l1_profile as lp  # noqa: E402


def _verdicts():
    cols = ["lens_id", "target_id", "cell_id", "state", "variable"]
    rows = [
        ("L1", "", "", "NO-ANALOG", "gravity"),               # lens-level row: ignored
        ("L1", "connecting_ridge", "", "TRANSFERS", "slope"),  # target-level, no cell: ignored
        ("L1", "connecting_ridge", "A", "TRANSFERS", "slope"),
        ("L1", "shackleton_rim", "A", "TRANSFERS", "slope"),
        ("L1", "shackleton_rim", "B", "TRANSFERS", "slope"),
        ("L2", "shackleton_rim", "B", "TRANSFERS", "shadow"),
        ("L2", "shackleton_rim", "C", "NO-ANALOG", "shadow"),  # not kept
        ("X1", "arcadia", "D", "TRANSFERS", "ice"),             # other lens: ignored
    ]
    return pd.DataFrame(rows, columns=cols)


def test_profiled_cells_only_cell_level_transfers_of_l1_l2():
    c = lp.profiled_cells(_verdicts()).set_index("cell_id")
    assert list(c.index) == ["A", "B"]
    assert c.loc["A", "lenses"] == "L1"
    assert c.loc["A", "targets"] == "L1:connecting_ridge,L1:shackleton_rim"
    assert c.loc["B", "lenses"] == "L1,L2"


def test_ice_check_thresholds_committed_in_plan():
    assert lp.ice_check(0.21) == "excluded: perennial ice"
    assert lp.ice_check(0.2) == "flag: some ice"   # > 0.2 excludes, 0.2 itself is a flag
    assert lp.ice_check(0.05) == "flag: some ice"
    assert lp.ice_check(0.049) == "ok"
    assert lp.ice_check(np.nan) == "not assessed"
    assert lp.ice_check(None) == "not assessed"


def test_review_note_reports_unknown_attention_and_l2_snow():
    r = {"ice_frac": 0.1, "attention_n": pd.NA, "in_exclusion_buffer": True,
         "lenses": "L1,L2", "snow_free_frac": 0.8}
    note = lp.review_note(r)
    assert "flag: some ice" in note and "attention unknown" in note
    assert "exclusion buffer" in note and "snow_free_frac 0.80" in note
    assert "snow_free_frac" not in lp.review_note({**r, "lenses": "L1"})


def test_apply_profiles_keeps_existing_names_and_touches_only_profiled_cells():
    earth = pd.DataFrame({"cell_id": ["A", "B", "CTRL_x"], "name": [None, "", "Kept name"]})
    prof = pd.DataFrame({"cell_id": ["A", "CTRL_x"], "name": ["Geo A", "Geo X"],
                         "ice_frac": [0.0, 0.3], "review_note": ["ice ok", "ice excluded"]})
    out = lp.apply_profiles(earth, prof).set_index("cell_id")
    assert out.loc["A", "name"] == "Geo A"
    assert out.loc["CTRL_x", "name"] == "Kept name"
    assert out.loc["CTRL_x", "ice_frac"] == 0.3
    assert out.loc["B", "name"] == "" and pd.isna(out.loc["B", "ice_frac"])
    assert out.loc["B", "review_note"] is None
