import sys
from pathlib import Path

import pandas as pd
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

import sites as st  # noqa: E402

VCOLS = ["lens_id", "target_id", "cell_id", "test", "variable", "state", "value", "reason",
         "facility"]


def _v(rows):
    return pd.DataFrame([dict(zip(VCOLS, r, strict=True)) for r in rows])


def _cells():
    # A-B 100 km apart, B-C 100 km apart (A-C 200 km: single linkage chains them), D far away
    return pd.DataFrame({
        "cell_id": ["A", "B", "C", "D"], "lat": [0.0, 0.0, 0.0, 40.0],
        "lon": [0.0, 0.8993, 1.7986, 0.0], "lenses": ["L1", "L1,L2", "L1", "L2"],
        "targets": ["L1:connecting_ridge", "L1:shackleton_rim,L2:shackleton_rim",
                    "L1:shackleton_rim", "L2:connecting_ridge"],
        "name": ["a", "b", "c", "d"],
        "ice_check": ["excluded: perennial ice", "ok", "flag: some ice", "ok"],
        "in_exclusion_buffer": [False, True, False, False]})


def _verdicts():
    return _v([
        ("L1", "", "", "T", "gravity", "NO-ANALOG", 0.165, "g", "Offload rig"),
        ("L1", "", "", "T", "boulders", "UNOBSERVED", None, "below DEM", ""),
        ("L1", "connecting_ridge", "", "T", "slope_roughness", "TRANSFERS", 1, "summary", ""),
        ("L1", "connecting_ridge", "A", "T", "slope_roughness", "TRANSFERS", 40, "rank 40", ""),
        ("L1", "shackleton_rim", "B", "T", "slope_roughness", "TRANSFERS", 30, "rank 30", ""),
        ("L1", "shackleton_rim", "C", "T", "slope_roughness", "TRANSFERS", 35, "rank 35", ""),
        ("L2", "shackleton_rim", "B", "S", "shadow_casting", "TRANSFERS", 20, "rank 20", ""),
        ("L2", "connecting_ridge", "D", "S", "shadow_casting", "TRANSFERS", 25, "rank 25", ""),
        ("X1", "", "", "I", "day_night_cycle", "TRANSFERS", 1.03, "day length", ""),
        ("X1", "", "", "I", "pressure", "NO-ANALOG", 0.006, "p", "CO2 chamber"),
        ("X1", "arcadia", "x_near", "I", "ice_configuration", "TRANSFERS", 3, "3 conds", ""),
        ("M1", "jezero", "", "M", "aqueous_mineral", "NO-ANALOG", None, "stop rule", ""),
    ])


def test_single_linkage_chains_and_site_id_is_smallest_cell():
    c = _cells()
    s = st.cluster_cells(c, km=150)
    assert list(s) == ["site:A", "site:A", "site:A", "site:D"]
    assert list(st.cluster_cells(c, km=50)) == ["site:A", "site:B", "site:C", "site:D"]


def test_name_sites_manual_anchor_wins_and_rejects_two_anchors():
    c = _cells().assign(site_id=st.cluster_cells(_cells()))
    n = st.name_sites(c, [{"anchor": "B", "name": "Big", "query": '"Big"'}]).set_index("site_id")
    assert n.loc["site:A", "name"] == "Big" and n.loc["site:A", "name_source"] == "manual"
    assert n.loc["site:D", "name"] == "d" and pd.isna(n.loc["site:D", "query"])
    with pytest.raises(ValueError):
        st.name_sites(c, [{"anchor": "A", "name": "x", "query": "x"},
                          {"anchor": "C", "name": "y", "query": "y"}])


def test_target_scarcity_counts_ice_and_exclusion_and_ignores_summary_rows():
    c = _cells().assign(site_id=st.cluster_cells(_cells()))
    s = st.target_scarcity(_verdicts(), c).set_index(["lens_id", "target_id"])
    cr = s.loc[("L1", "connecting_ridge")]
    assert cr["n_transfers"] == 1 and cr["n_ice_excluded"] == 1 and cr["n_usable"] == 0
    rim = s.loc[("L1", "shackleton_rim")]
    assert rim["n_transfers"] == 2 and rim["n_usable"] == 2
    assert rim["n_usable_outside_exclusion"] == 1 and rim["n_sites_usable"] == 1


def test_multilens_state_comes_from_verdicts():
    c = _cells().assign(site_id=st.cluster_cells(_cells()))
    partners = pd.DataFrame({"partner_id": ["x_near", "m_seed", "x_far"],
                             "partner_lens": ["X1", "M1", "X1"], "lat": [40.1, 0.5, -60.0],
                             "lon": [0.0, 0.0, 0.0], "label": ["x", "m", "far"]})
    ml = st.multilens(c, partners, _verdicts())
    got = {(r.cell_id, r.partner_id): r.partner_state for r in ml.itertuples()}
    assert got[("D", "x_near")] == "engine TRANSFERS"
    assert got[("A", "m_seed")] == "literature-only"     # M1 has no cell-level TRANSFERS
    assert not any(p == "x_far" for _, p in got)


def test_showcase_rules():
    c = _cells().assign(site_id=st.cluster_cells(_cells()))
    sites = st.summarise_sites(c)
    ml = pd.DataFrame({"site_id": ["site:D"]})
    rules = dict(zip(sites["site_id"], st.showcase_rules(sites, c, _verdicts(), ml),
                     strict=True))
    # site:A: ridge cell A is ice-excluded -> no (a); holds an exclusion-buffer cell -> no (c)
    assert rules["site:A"] == ""
    assert rules["site:D"] == "a,b,c"


def test_field_facility_split_never_shows_set_summaries_as_site_verdict():
    partners = pd.DataFrame({"partner_lens": ["X1", "M1"], "partner_id": ["x_near", "m_seed"],
                             "partner_label": ["x", "seed m"], "distance_km": [10.0, 90.0],
                             "partner_state": ["engine TRANSFERS", "literature-only"]})
    card = st.field_facility({"site_id": "site:D"}, ["D"], _verdicts(), partners)
    vars_ = {(f["lens"], f["variable"]) for f in card["field"]}
    assert ("L2", "shadow_casting") in vars_ and ("X1", "ice_configuration") in vars_
    assert ("X1", "day_night_cycle") in vars_                      # lens-level physics
    assert all(f["reason"] != "summary" for f in card["field"])     # set summary excluded
    assert {f["variable"] for f in card["facility"]} == {"pressure"}  # X1 only; L1 not in site
    assert card["lenses"] == ["L2", "X1"]
    assert len(card["literature_notes"]) == 1 and "literature-only" in card["literature_notes"][0]
