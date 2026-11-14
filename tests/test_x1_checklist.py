"""B15 tests: X1 three-condition checklist and glacier filter."""

import importlib.util

import numpy as np
import pandas as pd

from similitude import io

_spec = importlib.util.spec_from_file_location(
    "x1_checklist", io.REPO_ROOT / "scripts" / "gee" / "x1_checklist.py")
x1 = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(x1)


def frame(**cols):
    base = {"cell_id": ["a"], "maat_c": [-10.0], "ft_yr": [5.0], "aridity_p_pet": [0.2],
            "ice_frac": [0.0]}
    base.update({k: [v] for k, v in cols.items()})
    return pd.DataFrame(base)


def test_dry_cold_no_thaw_passes():
    r = x1.evaluate(frame()).iloc[0]
    assert r["passes_all"] and r["candidate"] and r["n_met"] == 3 and r["failed"] == "-"


def test_each_condition_can_fail():
    assert x1.evaluate(frame(maat_c=0.5)).iloc[0]["failed"] == "permafrost"
    assert x1.evaluate(frame(ft_yr=160.0)).iloc[0]["failed"] == "no_thaw_to_ice"
    assert x1.evaluate(frame(aridity_p_pet=0.9)).iloc[0]["failed"] == "dry_overburden"


def test_missing_data_counts_as_not_met():
    r = x1.evaluate(frame(ft_yr=np.nan)).iloc[0]
    assert not r["passes_all"] and "no_thaw_to_ice" in r["failed"]


def test_glacier_ice_excluded_and_unknown_reported():
    assert not x1.evaluate(frame(ice_frac=0.7)).iloc[0]["candidate"]
    assert x1.evaluate(frame(ice_frac=0.1)).iloc[0]["ice_check"].startswith("flag")
    r = x1.evaluate(frame(ice_frac=np.nan)).iloc[0]
    assert r["candidate"] and r["ice_check"].startswith("not assessed")


def test_thresholds_documented_in_lens_config():
    ck = io.load_lenses()["X1"]["checklist"]
    assert set(ck) >= {"permafrost", "no_thaw_to_ice", "dry_overburden"}
    assert "ft_yr <= 20" in ck["no_thaw_to_ice"]["rule"]
    assert "0.5" in ck["dry_overburden"]["rule"]
