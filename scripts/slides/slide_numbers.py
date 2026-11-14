"""B12 — every number on the slides, read from pipeline tables (review 4.3: no hand-typed numbers).

Output: docs/slide_numbers.json (key -> {value, source}). Slides cite keys from this file.
Run after the final pipeline (A8/A12/A15/B13/B15) and again after Data Freeze.
"""

from __future__ import annotations

import datetime as dt
import json

import pandas as pd

from similitude import io

D = io.REPO_ROOT / "data" / "derived"
OUT = io.REPO_ROOT / "docs" / "slide_numbers.json"


def main() -> None:
    n: dict[str, dict] = {}

    def put(key, value, source):
        if hasattr(value, "item"):
            value = value.item()
        if isinstance(value, float):
            value = round(value, 4)
        n[key] = {"value": value, "source": source}

    # ---- attention (slide 2, 5) ----
    att = pd.read_parquet(D / "attention.parquet").set_index("key")["n_pubs"]
    for k in ("atacama_yungay", "harrat_khaybar", "haughton_devon", "lake_salda"):
        if k in att.index and pd.notna(att[k]):
            put(f"attention_{k}", int(att[k]), "data/derived/attention.parquet (OpenAlex)")

    # ---- validation controls (slide 2, 4) ----
    vc = pd.read_parquet(D / "validation_controls.parquet")
    src = "data/derived/validation_controls.parquet"
    salda = vc[(vc.cell_id == "ctl_lake_salda") & (vc.target_id == "jezero_margin")]
    if len(salda):
        put("salda_footprint_percentile_vs_jezero", float(salda.percentile.iloc[0]), src)
    hd = vc[(vc.cell_id == "CTRL_haughton_devon") & (vc.target_id == "connecting_ridge")]
    if len(hd):
        put("haughton_L1_percentile", float(hd.percentile.iloc[0]), src)
    if "expectation_met" in vc:
        met = vc.dropna(subset=["expectation_met"])
        put("controls_expectations_met", int(met.expectation_met.astype(bool).sum()), src)
        put("controls_expectations_total", int(len(met)), src)

    # ---- M1 pixel test (slide 4, 5) ----
    sr = json.loads((D / "m1_stop_rule.json").read_text(encoding="utf-8"))
    src = "data/derived/m1_stop_rule.json"
    put("m1_stop_rule_verdict", sr["verdict"], src)
    lp = sr["largest_patch_km2"]
    put("salda_relocated_largest_patch_km2", lp["ctl_lake_salda__relocated"], src)
    put("salda_relocated_matched_area_km2", sr["matched_area_km2_lake_salda_relocated"], src)
    put("semail_largest_patch_km2_max",
        max(lp[k] for k in lp if k.startswith("seed_semail")), src)
    put("wadi_rum_largest_patch_km2", lp["ctl_wadi_rum"], src)
    put("simpson_largest_patch_km2", lp["ctl_simpson_desert"], src)
    put("harrat_khaybar_largest_patch_km2", lp["seed_harrat_khaybar"], src)
    px = pd.read_parquet(D / "earth_M1_pixels.parquet")
    sem = px[(px.cell_id.str.startswith("seed_semail")) & (px.target_id == "jezero_margin")]
    put("semail_matched_area_km2_max", float(sem.matched_area_km2.max()),
        "data/derived/earth_M1_pixels.parquet")
    q = json.loads((D / "m1_null_quantiles.json").read_text(encoding="utf-8"))
    put("m1_null_pixels", int(q["D2300"]["n_pixels"]), "data/derived/m1_null_quantiles.json")
    put("m1_null_footprints", int(q["n_footprints"]), "data/derived/m1_null_quantiles.json")

    # ---- L1 robust set (slide 5) ----
    rb = pd.read_parquet(D / "l1_robust_set.parquet")
    src = "data/derived/l1_robust_set.parquet"
    for tid in ("connecting_ridge", "shackleton_rim"):
        sel = rb[(rb.target_id == tid) & rb.robust.astype(bool) & rb.nms_keep.astype(bool)]
        put(f"l1_robust_cells_{tid}", int(len(sel)), src)
    n_native = int(rb["n_i"].max())
    put("l1_n_native_footprints", n_native, src)

    # ---- L2 sun geometry (slide 6) ----
    e2 = pd.read_parquet(D / "earth_L2.parquet")
    t2 = pd.read_parquet(D / "targets_L2.parquet")
    put("l2_earth_best_lowsun_frac_daylight", float(e2.lowsun_frac_daylight.max()),
        "data/derived/earth_L2.parquet")
    put("l2_moon_lowsun_frac_daylight",
        float(t2[t2.is_reference.astype(bool)].lowsun_frac_daylight.max()),
        "data/derived/targets_L2.parquet")

    # ---- verdicts (slide 3, 6) ----
    v = pd.read_parquet(D / "verdicts.parquet")
    src = "data/derived/verdicts.parquet"
    for lid in ("L1", "L2", "M1", "X1"):
        cell = v[(v.lens_id == lid) & v.cell_id.notna() & (v.cell_id != "")
                 & (v.state == "TRANSFERS")]
        put(f"verdict_transfers_cells_{lid}", int(cell.cell_id.nunique()), src)
    put("verdict_rows_total", int(len(v)), src)

    # ---- X1 checklist (slide 5) ----
    x = pd.read_parquet(D / "x1_checklist.parquet")
    src = "data/derived/x1_checklist.parquet"
    pool = x[x.sample_role.isin(["rank", "null"])]
    put("x1_cells_scored", int(len(pool)), src)
    put("x1_cells_pass_all_not_glacier", int((pool.candidate & pool.qa_flag.eq("ok")).sum()), src)
    pamir = x[x.cell_id.isin(["seed_east_pamir_murghab", "seed_changtang_north",
                              "seed_karakul_structure", "seed_qiangtang_east",
                              "seed_west_kunlun_aksai_chin", "seed_kunlun_pass"])]
    put("x1_pamir_changtang_pass", int(pamir.passes_all.sum()), src)
    put("x1_pamir_changtang_total", int(len(pamir)), src)
    put("x1_tibet_ft_days_min", float(pamir.ft_yr.min()), src)
    put("x1_tibet_ft_days_max", float(pamir.ft_yr.max()), src)
    xi = x.set_index("cell_id")
    put("x1_beacon_valley_conditions_met", int(xi.loc["ctl_beacon_valley", "n_met"]), src)

    # ---- data volume (slide 7) ----
    put("emit_footprints_m1", int(pd.read_parquet(D / "earth_M1.parquet").shape[0]),
        "data/derived/earth_M1.parquet")
    put("l1_chips", int(pd.read_parquet(D / "earth_L1.parquet").shape[0]),
        "data/derived/earth_L1.parquet")

    doc = {"generated": dt.datetime.now().isoformat(timespec="minutes"), "numbers": n}
    OUT.write_text(json.dumps(doc, indent=1, ensure_ascii=False), encoding="utf-8")
    for k, val in n.items():
        print(f"{k:45s} {val['value']}")


if __name__ == "__main__":
    main()
