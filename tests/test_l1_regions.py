"""PLAN 2e: known-truth checks of L1 are readings of existing tables with the unchanged rule."""

import json
import re
import sys

import pandas as pd
import pytest

from similitude import io

sys.path.insert(0, str(io.REPO_ROOT / "scripts"))
import l1_regions as lr  # noqa: E402

DERIVED = io.REPO_ROOT / "data" / "derived"


@pytest.fixture(scope="module")
def built():
    if not (DERIVED / "l1_regions.json").exists():
        pytest.skip("l1_regions.json not built")
    return lr.build()  # raises if the published robust sets are not reproduced exactly


def test_published_regions_keep_their_reference_and_others_use_a_population_footprint(built):
    refs = built["summary"]["refs"]
    assert refs["connecting_ridge"] == "connecting_ridge_ref"
    assert refs["shackleton_rim"] == "shackleton_rim_ref"
    assert len(refs) == 6 and all("_pop_" in v for k, v in refs.items() if k not in lr.PUBLISHED)


def test_committed_tables_match_a_rebuild(built):
    saved = json.loads((DERIVED / "l1_regions.json").read_text(encoding="utf-8"))
    for k in ("refs", "lunar_control", "regions_rank_seed_robust", "ridge_vs_wall"):
        assert json.loads(json.dumps(built["summary"][k])) == saved[k], k
    pd.testing.assert_frame_equal(pd.read_parquet(DERIVED / "l1_lunar_control.parquet"),
                                  built["control"])
    pd.testing.assert_frame_equal(pd.read_parquet(DERIVED / "l1_prevalence.parquet"),
                                  built["prevalence"])


def test_lunar_control_never_scores_a_footprint_against_itself(built):
    c = built["control"]
    t = lr.context()["targets"]
    pop = t[~t["is_reference"].astype(bool)].groupby("target_id").size()
    same = c[c["reference_region"].eq(c["candidate_region"])].set_index("reference_region")["n"]
    assert (same < pop.reindex(same.index)).all()      # the reference and its overlaps are out
    assert (c["n_pass"] <= c["n"]).all()


def test_prevalence_counts_only_random_cells(built):
    p = built["prevalence"].set_index("target_id")
    earth = pd.read_parquet(DERIVED / "earth_L1.parquet")
    assert (p["null_n"] == int(earth["sample_role"].eq("null").sum())).all()
    assert ((p["pass"] == p["null_pass"] + p["null2_pass"]) & (p["ci_lo"] <= p["rate"])
            & (p["rate"] <= p["ci_hi"])).all()


def test_cross_dem_covers_the_ridge_cells_and_the_site_note_quotes_it():
    path = DERIVED / "cross_dem.parquet"
    if not path.exists():
        pytest.skip("cross_dem.parquet not built")
    c = pd.read_parquet(path)
    rob = pd.read_parquet(DERIVED / "l1_robust_set.parquet")
    ridge = set(rob[rob["target_id"].eq("connecting_ridge") & rob["robust"]
                    & rob["sample_role"].isin(["rank", "seed"])]["cell_id"])
    got = c[c["target_id"].eq("connecting_ridge")].set_index("cell_id")
    assert ridge <= set(got.index) and got.loc[list(ridge), "robust_glo30"].all()
    note = next(s["note"] for s in io.load_yaml(io.CONFIG_DIR / "sites.yaml")["sites"]
                if s["anchor"] == "E10K_729_-319")
    typed = [int(x) for x in re.findall(r"native rank (\d+) of 49.*?configuration, (\d+) with",
                                        " ".join(note.split()))[0]]
    base = rob[rob["target_id"].eq("connecting_ridge")].set_index("cell_id")
    assert typed == [int(got.loc["E10K_729_-319", "nr_ii"]),
                     int(base.loc["E10K_729_-319", "nr_ii"])]
    assert not bool(got.loc["E10K_729_-319", "robust"])


def test_slope_formula_matches_nasa_rasters_when_available():
    chk = lr.nasa_slope_check()
    if chk is None:
        pytest.skip("PGDA 78 rasters not on this machine")
    assert (chk["slope_p50_ours_5m"] - chk["slope_p50_nasa"]).abs().max() < 0.01
    assert (chk["frac_gt8_ours_5m"] - chk["frac_gt8_nasa"]).abs().max() < 0.001
    saved = pd.read_parquet(DERIVED / "nasa_slope_check.parquet")
    pd.testing.assert_frame_equal(saved, chk)


def test_site_stability_blocks_are_complete_and_neighbours_stay_out_of_verdicts():
    path = DERIVED / "site_stability.parquet"
    if not path.exists():
        pytest.skip("site_stability.parquet not built")
    s = pd.read_parquet(path)
    assert (s.groupby(["anchor", "dem"]).size() == 9).all()
    centre = s[(s["dx"] == 0) & (s["dy"] == 0) & s["dem"].eq("GLO-30")]
    rob = pd.read_parquet(DERIVED / "l1_robust_set.parquet")
    rob = rob[rob["target_id"].eq("connecting_ridge")].set_index("cell_id")["robust"]
    assert (centre["robust"].to_numpy() == rob.loc[centre["anchor"]].to_numpy()).all()
    v = pd.read_parquet(DERIVED / "verdicts.parquet")
    assert not v["cell_id"].fillna("").str.contains(":").any()   # block ids never become verdicts
    regions = pd.read_parquet(DERIVED / "l1_regions.parquet")
    exploratory = set(regions["target_id"]) - set(lr.PUBLISHED)
    assert not (set(v["target_id"].dropna()) & exploratory)


def test_evidence_page_is_the_generated_one_and_its_figures_exist():
    import web_evidence as we

    page = io.REPO_ROOT / "web" / "evidence.html"
    if not page.exists():
        pytest.skip("web/evidence.html not built")
    text = page.read_text(encoding="utf-8")
    assert text == we.build()
    for name in re.findall(r'src="figures/([^"]+)"', text):
        assert (io.REPO_ROOT / "docs" / "figures" / name).exists(), name
    for banned in ("meets the requirement", "credited towards TRL", "false-positive"):
        assert banned not in text
