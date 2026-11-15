# ruff: noqa: E501
"""Open-country leads (scripts/access/access_screen.py): invariants of the published file."""

import json
import math

import pandas as pd
import pytest

from similitude import io

ACCESS = io.REPO_ROOT / "web" / "data" / "access.json"
NEW = io.REPO_ROOT / "data" / "derived" / "access_screen.parquet"
LEADS = io.REPO_ROOT / "data" / "derived" / "access_leads.parquet"


@pytest.fixture(scope="module")
def acc():
    if not ACCESS.exists():
        pytest.skip("access.json not built")
    return json.loads(ACCESS.read_text(encoding="utf-8"))


def test_leads_are_labelled_exploratory_and_state_the_country_rule(acc):
    assert "not verdicts" in acc["status"]
    assert "China" in acc["excluded_countries"] and acc["excluded_reason"]
    assert {r["id"] for r in acc["regions"]} >= {"connecting_ridge", "shackleton_rim"}


def test_no_lead_lies_in_an_excluded_or_unknown_country(acc):
    bad = {*acc["excluded_countries"], "unknown", None}
    for reg in acc["regions"]:
        assert all(lead["country"] not in bad for lead in reg["leads"]), reg["id"]


def test_lead_numbers_are_consistent(acc):
    for reg in acc["regions"]:
        for lead in reg["leads"]:
            assert lead["second_dem"] in {"yes", "no", "not checked"}
            assert 0.0 <= lead["frac_gt8"] <= 1.0 and 0.0 <= lead["frac_gt20"] <= lead["frac_gt8"] + 1e-9
            km = 10.0 * reg["target_frac_gt8"] / max(lead["frac_gt8"], 1e-6)
            assert math.isclose(lead["traverse_km"], round(km, 1), abs_tol=0.11)


def test_every_new_lead_passes_the_unchanged_rule_in_all_three_configurations(acc):
    if not NEW.exists():
        pytest.skip("access_screen.parquet not built")
    new = pd.read_parquet(NEW)
    ok = new["in_i"] & new["in_ii"] & new["in_iii"]
    assert (new["robust"] == ok).all()
    passed = set(zip(new.loc[new["robust"], "cell_id"], new.loc[new["robust"], "target_id"], strict=True))
    for reg in acc["regions"]:
        for lead in reg["leads"]:
            if lead["source"] == "access screen (new)":
                assert (lead["cell_id"], reg["id"]) in passed
        assert reg["new_pass"] == sum(1 for c, t in passed if t == reg["id"])


def test_second_dem_label_matches_the_table(acc):
    if not LEADS.exists():
        pytest.skip("access_leads.parquet not built")
    lt = pd.read_parquet(LEADS)
    lab = {(r.cell_id, r.target_id): ("not checked" if pd.isna(r.robust_alt) else ("yes" if r.robust_alt else "no"))
           for r in lt.itertuples()}
    for reg in acc["regions"]:
        for lead in reg["leads"]:
            assert lab[(lead["cell_id"], reg["id"])] == lead["second_dem"]
