import numpy as np
import pandas as pd

from similitude.fidelity import score_lens
from similitude.validation import control_report, expectation_met, sensitivity_drop_one, top_k


def _synthetic(seed=0):
    rng = np.random.default_rng(seed)
    names = ["a", "b", "c"]
    pop = pd.DataFrame(rng.normal(0, 1, (30, 3)), columns=names)
    pop["is_reference"], pop["target_id"] = False, "pop"
    ref = pd.DataFrame([[0.0, 0.0, 0.0]], columns=names)
    ref["is_reference"], ref["target_id"] = True, "tgt"
    targets = pd.concat([pop, ref], ignore_index=True)
    null = pd.DataFrame(rng.normal(5, 1, (40, 3)), columns=names)
    null["sample_role"] = "null"
    rank = pd.DataFrame(rng.normal(3, 1, (15, 3)), columns=names)
    rank["sample_role"] = "rank"
    planted = pd.DataFrame([[0.05, -0.05, 0.0], [9, 9, 9]], columns=names)
    planted["sample_role"] = ["control", "decoy"]
    earth = pd.concat([null, rank, planted], ignore_index=True)
    earth["cell_id"] = [f"c{i}" for i in range(len(earth))]
    earth["name"] = ""
    earth["expected"] = ""
    earth.loc[earth.sample_role == "control", "expected"] = "high"
    earth.loc[earth.sample_role == "decoy", "expected"] = "low"
    lens = {"id": "L1", "descriptors": names, "min_scale": {n: 0.1 for n in names}}
    return earth, targets, lens


def test_expectation_rules():
    assert expectation_met("high", 95) is True
    assert expectation_met("high", 80) is False
    assert expectation_met("low", 20) is True
    assert expectation_met("uncertain", 99) is None
    assert expectation_met("high", float("nan")) is None


def test_planted_control_tops_and_decoy_fails():
    earth, targets, lens = _synthetic()
    fid = score_lens(earth, targets, lens)
    rep = control_report(fid, earth)
    ctrl = rep[rep.sample_role == "control"].iloc[0]
    decoy = rep[rep.sample_role == "decoy"].iloc[0]
    assert ctrl.rank_all == 1 and bool(ctrl.expectation_met)
    assert bool(decoy.expectation_met)  # decoy far away -> low percentile, as expected


def test_top_k_only_rank_and_seed():
    earth, targets, lens = _synthetic()
    fid = score_lens(earth, targets, lens)
    ids = top_k(fid, earth, "tgt", k=5)
    roles = earth.set_index("cell_id").loc[ids, "sample_role"]
    assert set(roles) <= {"rank", "seed"} and len(ids) == 5


def test_sensitivity_shape():
    earth, targets, lens = _synthetic()
    out = sensitivity_drop_one(earth, targets, lens, "tgt", k=5)
    assert len(out) == 3 and out["jaccard_top5"].between(0, 1).all()
