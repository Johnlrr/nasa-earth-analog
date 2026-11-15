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

    # ---- B17: sites, target scarcity, multi-lens (slide 5-6), 2c contract ----
    e1 = pd.read_parquet(D / "earth_L1.parquet")
    put("l1_cells_scored_rank_seed", int(e1.sample_role.isin(["rank", "seed"]).sum()),
        "data/derived/earth_L1.parquet (sample_role rank + seed)")
    sc = pd.read_parquet(D / "target_scarcity.parquet").set_index(["lens_id", "target_id"])
    src = "data/derived/target_scarcity.parquet"
    for (lid, tid), r in sc.iterrows():
        for col in ("n_transfers", "n_usable", "n_usable_outside_exclusion",
                    "n_usable_not_downgraded", "n_usable_b10_unreviewed", "n_sites_usable"):
            put(f"scarcity_{lid}_{tid}_{col}", int(r[col]), src)
    ml = pd.read_parquet(D / "multilens.parquet")
    eng = ml[ml.partner_state.astype(str).str.startswith("engine")]
    put("multilens_engine_engine_sites", int(eng.site_id.nunique()),
        "data/derived/multilens.parquet")
    st = pd.read_parquet(D / "sites.parquet")
    put("sites_total", int(len(st)), "data/derived/sites.parquet")
    put("sites_showcase", int((st.showcase.fillna("").astype(str).str.len() > 0).sum()),
        "data/derived/sites.parquet")
    put("sites_attention_known", int(st.attention_n.notna().sum()), "data/derived/sites.parquet")
    put("sites_hidden_yes", int(st.hidden_status.astype(str).str.lower().eq("yes").sum()),
        "data/derived/sites.parquet")
    # per showcase site: attention, hidden status, cell count (slide 5 wording)
    slugs = {"Zanda": "zanda_gar", "Peary": "peary_land", "Qaidam": "da_qaidam",
             "Jebel Akhdar": "jebel_akhdar", "Mauna": "mauna_loa", "Atacama": "atacama_puna"}
    show = st[st.showcase.fillna("").astype(str).str.len() > 0]
    for _, r in show.iterrows():
        slug = next((v for k, v in slugs.items() if k in str(r["name"])), None)
        if slug is None:
            continue
        if pd.notna(r["attention_n"]):
            put(f"site_{slug}_attention", int(r["attention_n"]), "data/derived/sites.parquet")
        put(f"site_{slug}_hidden_status", str(r["hidden_status"]), "data/derived/sites.parquet")
        put(f"site_{slug}_n_cells", int(r["n_cells"]), "data/derived/sites.parquet")
        put(f"site_{slug}_max_span_km", float(r["max_span_km"]), "data/derived/sites.parquet")

    # ---- data volume (slide 7) ----
    put("emit_footprints_m1", int(pd.read_parquet(D / "earth_M1.parquet").shape[0]),
        "data/derived/earth_M1.parquet")
    put("l1_chips", int(pd.read_parquet(D / "earth_L1.parquet").shape[0]),
        "data/derived/earth_L1.parquet")

    # ---- PLAN 2d: mission criteria, validity, coverage (scripts/mission_value.py) ----
    mvp = D / "mission_value.json"
    if mvp.exists():
        mv = json.loads(mvp.read_text(encoding="utf-8"))
        src = "data/derived/mission_value.json"
        for k, val in mv["l1_reference"].items():
            put(f"cr_{k}", val, src)
        for k, val in mv["l1_classic_controls"].items():
            put(f"classic_{k}", val, src)
        put("classic_under_sampling_factor", mv["l1_under_sampling"], src)
        for r in mv["l1_null"]:
            put(f"null_{r['target_id']}_robust", r["robust_null"], src)
            put(f"null_{r['target_id']}_n", r["n_null"], src)
        red = mv["rediscovery"]
        for k in ("rank_in_zone", "rank_n", "base_rate", "rank_enrichment"):
            put(f"rediscovery_{k}", red[k], src)
        for r in red["targets"]:
            put(f"rediscovery_{r['target_id']}_robust_in_zone", r["robust_in_zone"], src)
            put(f"rediscovery_{r['target_id']}_robust_n", r["robust_n"], src)
        put("x1_positive_pass", len(mv["x1_controls"]["positive_pass"]), src)
        put("x1_positive_n", mv["x1_controls"]["positive_n"], src)
        put("x1_decoy_rejected", len(mv["x1_controls"]["decoy_rejected"]), src)
        put("x1_decoy_n", mv["x1_controls"]["decoy_n"], src)
        put("m1_checks_passed", mv["m1_checks"]["passed"], src)
        put("m1_checks_n", mv["m1_checks"]["n"], src)
        for lens, c in mv["coverage"].items():
            put(f"coverage_{lens}_transfers", c["TRANSFERS"], src)
            put(f"coverage_{lens}_facility", c["NO-ANALOG"], src)
            put(f"coverage_{lens}_total", sum(c.values()), src)
        for k, val in mv["funnel"].items():
            put(f"funnel_{k}", val, src)
        crit = pd.read_parquet(D / "mission_criteria.parquet")
        src = "data/derived/mission_criteria.parquet"
        for r in crit[crit.group.eq("Engine match")].itertuples():
            slug = next((v for k, v in slugs.items() if k in str(r.name)), r.id)
            put(f"match_{slug}_frac_gt8", r.frac_gt8, src)
            put(f"match_{slug}_frac_gt20", r.frac_gt20, src)
        ta = pd.read_parquet(D / "task_attention.parquet")
        for r in ta.itertuples():
            slug = next((v for k, v in slugs.items() if k in str(r.name)), None)
            if slug:
                put(f"task_attention_{slug}_{r.context}", int(r.n_pubs),
                    "data/derived/task_attention.parquet (OpenAlex)")

    doc = {"generated": dt.datetime.now().isoformat(timespec="minutes"), "numbers": n}
    OUT.write_text(json.dumps(doc, indent=1, ensure_ascii=False), encoding="utf-8")
    for k, val in n.items():
        print(f"{k:45s} {val['value']}")


if __name__ == "__main__":
    main()
