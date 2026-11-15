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

    rb = pd.read_parquet(D / "l1_robust_set.parquet")
    rb = rb[rb.target_id.eq("connecting_ridge") & rb.sample_role.isin(["rank", "seed"])]
    for k in ("i", "ii", "iii"):
        put(f"l1_cr_pass_config_{k}", int(rb[f"in_{k}"].sum()),
            "data/derived/l1_robust_set.parquet")

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
            for k in ("extrapolated_cells", "extrapolated_lo", "extrapolated_hi"):
                put(f"null_{r['target_id']}_{k}", r[k], src)
        red = mv["rediscovery"]
        for k in ("rank_in_zone", "rank_n", "rank_rate", "base_rate", "matched_rate",
                  "matched_enrichment"):
            put(f"rediscovery_{k}", red[k], src)
        for r in red["targets"]:
            for k in ("robust_in_zone", "robust_n", "sites", "sites_with_zone_cell"):
                put(f"rediscovery_{r['target_id']}_{k}", r[k], src)
        put("x1_positive_pass", len(mv["x1_controls"]["positive_pass"]), src)
        put("x1_positive_n", mv["x1_controls"]["positive_n"], src)
        put("x1_decoy_rejected", len(mv["x1_controls"]["decoy_rejected"]), src)
        put("x1_decoy_n", mv["x1_controls"]["decoy_n"], src)
        for k in ("seed_devon_island", "seed_changtang_north", "seed_peary_land"):
            put(f"x1_{k}_passes", bool(mv["x1_controls"]["seed_pass"][k]), src)
        for k, val in mv["x1_mission"].items():
            put(f"x1_mission_{k}", val, src)
        put("m1_checks_passed", mv["m1_checks"]["passed"], src)
        put("m1_checks_n", mv["m1_checks"]["n"], src)
        for lens, c in mv["coverage"].items():
            put(f"coverage_{lens}_transfers", c["TRANSFERS"], src)
            put(f"coverage_{lens}_facility", c["NO-ANALOG"], src)
            put(f"coverage_{lens}_unobserved", c["UNOBSERVED"], src)
            put(f"coverage_{lens}_total", sum(c.values()), src)
        for k, val in mv["funnel"].items():
            put(f"funnel_{k}", val, src)
        crit = pd.read_parquet(D / "mission_criteria.parquet")
        src = "data/derived/mission_criteria.parquet"
        for r in crit[crit.group.eq("Engine match")].itertuples():
            slug = next((v for k, v in slugs.items() if k in str(r.name)), r.id)
            put(f"match_{slug}_frac_gt8", r.frac_gt8, src)
            put(f"match_{slug}_frac_gt20", r.frac_gt20, src)
        gz = st[st.name.astype(str).str.contains("Changtang")]
        if len(gz) and pd.notna(gz.attention_n.iloc[0]):
            put("site_gerze_attention", int(gz.attention_n.iloc[0]), "data/derived/sites.parquet")
            put("site_gerze_lenses_engine_confirmed", str(gz.lenses_engine_confirmed.iloc[0]),
                "data/derived/sites.parquet")
        ta = pd.read_parquet(D / "task_attention.parquet")
        for r in ta.itertuples():
            slug = next((v for k, v in slugs.items() if k in str(r.name)), None)
            if slug:
                put(f"task_attention_{slug}_{r.context}", int(r.n_pubs),
                    "data/derived/task_attention.parquet (OpenAlex)")

    # ---- PLAN 2e: checks against known truth (l1_regions.py, cross_dem.py) ----
    rgp = D / "l1_regions.json"
    if rgp.exists():
        rg = json.loads(rgp.read_text(encoding="utf-8"))
        src = "data/derived/l1_regions.json"
        put("nasa_slope_max_abs_diff_deg", rg["nasa_slope_max_abs_diff_deg"], src)
        put("nasa_share_max_abs_diff_points", 100 * rg["nasa_frac_max_abs_diff"], src)
        for k, val in rg["lunar_control"].items():
            put(f"lunar_control_{k}", val, src)
        for k, val in rg["ridge_vs_wall"].items():
            put(f"prevalence_ridge_vs_wall_{k}", val, src)
        for r in rg["prevalence"]:
            for k in ("pass", "n", "rate", "ci_lo", "ci_hi", "cells", "cells_lo", "cells_hi",
                      "screened_pass"):
                put(f"prevalence_{r['target_id']}_{k}", r[k],
                    "data/derived/l1_prevalence.parquet")
        lc = pd.read_parquet(D / "l1_lunar_control.parquet")
        w = lc[lc.reference_region.eq("shackleton_rim")]
        ws, wo = w[w.candidate_region.eq("shackleton_rim")], w[w.candidate_region.ne(
            "shackleton_rim")]
        src = "data/derived/l1_lunar_control.parquet"
        put("lunar_control_wall_same_pass", int(ws.n_pass.sum()), src)
        put("lunar_control_wall_same_n", int(ws.n.sum()), src)
        put("lunar_control_wall_other_pass", int(wo.n_pass.sum()), src)
        put("lunar_control_wall_other_n", int(wo.n.sum()), src)
        reg = pd.read_parquet(D / "l1_regions.parquet")
        reg = reg[reg.robust & reg.sample_role.isin(["rank", "seed"])]
        cd = pd.read_parquet(D / "cross_dem.parquet")
        cd = cd[cd.alt_ok]
        pub = cd[(cd.group.eq("wall match") & cd.target_id.eq("shackleton_rim"))
                 | (cd.group.ne("wall match") & cd.target_id.eq("connecting_ridge"))]
        src = "data/derived/cross_dem.parquet"
        put("cross_dem_same_verdict", int((pub.robust == pub.robust_glo30).sum()), src)
        kept = cd[cd.robust_glo30.astype(bool) & cd.target_id.isin(["connecting_ridge",
                                                                     "shackleton_rim"])]
        for _, sr in show.iterrows():
            slug = next((v for k, v in slugs.items() if k in str(sr["name"])), None)
            d = kept[kept.cell_id.isin(str(sr["cells"]).split(","))]
            if slug and len(d):
                put(f"cross_dem_{slug}_site_unchanged", int(d.robust.sum()), src)
                put(f"cross_dem_{slug}_site_n", int(len(d)), src)
        put("cross_dem_n", int(len(pub)), src)
        base = pd.read_parquet(D / "l1_robust_set.parquet")
        base = base[base.target_id.eq("connecting_ridge")].set_index("cell_id")
        crit = pd.read_parquet(D / "mission_criteria.parquet")
        for r in crit[crit.group.eq("Engine match")].itertuples():
            slug = next((v for k, v in slugs.items() if k in str(r.name)), r.id)
            x = cd[cd.cell_id.eq(r.id) & cd.target_id.eq("connecting_ridge")].iloc[0]
            put(f"cross_dem_{slug}_robust", bool(x.robust), src)
            put(f"cross_dem_{slug}_rank_full_metric", int(x.nr_ii), src)
            put(f"glo30_{slug}_rank_full_metric", int(base.loc[r.id, "nr_ii"]),
                "data/derived/l1_robust_set.parquet")
            put(f"regions_matched_{slug}", int(reg[reg.cell_id.eq(r.id)].shape[0]),
                "data/derived/l1_regions.parquet")
            put(f"traverse_km_{slug}", r.km_for_10km_of_target,
                "data/derived/mission_criteria.parquet")
        put("rank_rule_threshold", float(x.n_i) / 2, src)
        ss = pd.read_parquet(D / "site_stability.parquet")
        ss = ss[ss.ok]
        src = "data/derived/site_stability.parquet"
        cls_ = ss[ss.group.eq("Classic analog")]
        put("stability_classic_robust", int(cls_.robust.sum()), src)
        put("stability_classic_n", int(len(cls_)), src)
        em = ss[ss.group.eq("Engine match")].pivot_table(
            index=["site", "dx", "dy"], columns="dem", values="robust", aggfunc="first")
        for site, d in em.all(axis=1).groupby(level=0):
            slug = next((v for k, v in slugs.items() if k in str(site)), site)
            put(f"stability_{slug}_robust_both_dems", int(d.sum()), src)
            put(f"stability_{slug}_n", int(len(d)), src)
            put(f"stability_{slug}_cell_itself_robust_both_dems",
                bool(d.xs((0, 0), level=("dx", "dy")).iloc[0]), src)
        g30 = ss[ss.dem.eq("GLO-30")].groupby(["group", "site"]).frac_gt8.mean()
        ref8 = float(crit[crit.id.eq("connecting_ridge")].frac_gt8.iloc[0])
        for site, v in g30["Engine match"].items():
            slug = next((val for k, val in slugs.items() if k in str(site)), site)
            put(f"traverse_km_block_{slug}", 10 * ref8 / float(v), src)
        put("traverse_km_block_classic_median", 10 * ref8 / float(g30["Classic analog"].median()),
            src)
        cl = crit[crit.group.eq("Classic analog")]
        put("traverse_km_classic_median", float(cl.km_for_10km_of_target.median()),
            "data/derived/mission_criteria.parquet")
        sp = crit[crit.id.eq("CTRL_sp_crater_black_point")].iloc[0]
        put("sp_crater_frac_gt8", sp.frac_gt8, "data/derived/mission_criteria.parquet")
        put("sp_crater_pass_config_i", bool(base.loc["CTRL_sp_crater_black_point", "in_i"]),
            "data/derived/l1_robust_set.parquet")
        put("classic_pass_any_config", int(
            (base[base.index.isin(cl.id)][["in_i", "in_ii", "in_iii"]].any(axis=1)).sum()),
            "data/derived/l1_robust_set.parquet")

    # open-country leads (scripts/access/access_screen.py; post hoc, exploratory)
    acc_path = io.REPO_ROOT / "web" / "data" / "access.json"
    if acc_path.exists():
        acc = json.loads(acc_path.read_text(encoding="utf-8"))
        src = "web/data/access.json (scripts/access/access_screen.py)"
        put("access_coarse_pool", int(acc["pool"]["coarse_ranked"]), src)
        put("access_open_pool", int(acc["pool"]["open_not_scored_before"]), src)
        put("access_new_scored", int(acc["pool"]["new_scored"]), src)
        put("access_excluded_countries", ", ".join(acc["excluded_countries"]), src)
        for reg in acc["regions"]:
            slug = reg["id"]
            stable = [x for x in reg["leads"] if x["second_dem"] == "yes"]
            usable = [x for x in reg["leads"] if x.get("usable")]
            put(f"access_{slug}_leads", len(reg["leads"]), src)
            put(f"access_{slug}_leads_stable", len(stable), src)
            put(f"access_{slug}_leads_usable", len(usable), src)
            put(f"access_{slug}_new_pass", int(reg["new_pass"]), src)
            put(f"access_{slug}_countries_usable",
                ", ".join(sorted({x["country"] for x in usable})), src)
            if usable:
                best = max(usable, key=lambda x: x["frac_gt8"])
                put(f"access_{slug}_best_usable_country", best["country"], src)
                put(f"access_{slug}_best_usable_frac_gt8", best["frac_gt8"], src)
                put(f"access_{slug}_best_usable_traverse_km", best["traverse_km"], src)

    # V1: pre-registered traverse-outcome test (config/prereg_route_v1.yaml)
    rv_path = D / "route_validity.json"
    if rv_path.exists():
        rv = json.loads(rv_path.read_text(encoding="utf-8"))
        src = "data/derived/route_validity.json (scripts/route_validity.py, pre-registered V1)"
        put("v1_passer_reproduce", rv["passer"][0], src)
        put("v1_passer_n", rv["passer"][1], src)
        put("v1_null_reproduce", rv["null"][0], src)
        put("v1_null_n", rv["null"][1], src)
        put("v1_null_share", rv["null"][0] / rv["null"][1], src)
        put("v1_classic_reproduce", rv["classic"][0], src)
        put("v1_classic_n", rv["classic"][1], src)
        put("v1_passer_second_dem_reproduce", rv["passer_second_dem"][0], src)
        put("v1_moon_native_reproduce", rv["moon_native_reproduce"][0], src)
        put("v1_moon_native_n", rv["moon_native_reproduce"][1], src)
        put("v1_h1_p", rv["H1_p"], src)
        put("v1_h1_verdict", "PASS" if rv["H1_pass"] else "FAIL", src)
        put("v1_h1b_p", rv["H1b_p"], src)
        put("v1_h2_rho", rv["H2_rho"], src)
        put("v1_h2_verdict", "PASS" if rv["H2_pass"] else "FAIL", src)
        put("v1_ridge_climb_10", rv["ridge_outcomes"]["climb_10"], src)
        rvt = pd.read_parquet(D / "route_validity.parquet")
        pas = rvt[rvt.group.eq("passer")]
        put("v1_passer_climb_10_median", float(pas.climb_10.median()), src)
        put("v1_classic_climb_10_median", float(rvt[rvt.group.eq("classic")].climb_10.median()),
            src)

    # V2 (pre-registered threshold) and M1 Mars lens: config/prereg_v2_mars.yaml
    v2_path = D / "route_v2.json"
    if v2_path.exists():
        v2 = json.loads(v2_path.read_text(encoding="utf-8"))
        src = "data/derived/route_v2.json (scripts/v2_mars.py, pre-registered V2)"
        put("v2_n_moon_native", v2["n_moon_native"], src)
        put("v2_tau", v2["tau"], src)
        put("v2_passer_reproduce", v2["passer"][0], src)
        put("v2_passer_n", v2["passer"][1], src)
        put("v2_null_reproduce", v2["null"][0], src)
        put("v2_null_n", v2["null"][1], src)
        put("v2_null_share", v2["null"][0] / v2["null"][1], src)
        put("v2_classic_reproduce", v2["classic"][0], src)
        put("v2_classic_n", v2["classic"][1], src)
        put("v2_classic_share", v2["classic"][0] / v2["classic"][1], src)
        put("v2_h1_p", v2["H1_p"], src)
        put("v2_h1_verdict", "PASS" if v2["H1_pass"] else "FAIL", src)
        # two registered looks at H1 (V1, V2): Bonferroni-adjusted p for the second one
        put("v2_h1_p_bonferroni", min(1.0, 2 * v2["H1_p"]), src)
        put("v2_h1b_p", v2["H1b_p"], src)
        put("v2_h1b_verdict", "PASS" if v2["H1b_pass"] else "FAIL", src)
        put("v2_h2_rho", v2["H2_rho"], src)
    m1_path = D / "mars_m1.json"
    if m1_path.exists():
        m1 = json.loads(m1_path.read_text(encoding="utf-8"))
        src = "data/derived/mars_m1.json (scripts/v2_mars.py, pre-registered M1)"
        put("mars_n_neighbours", m1["n_mars_neighbours"], src)
        put("mars_target_frac_gt8", m1["target"]["frac_gt8"], src)
        put("mars_classic_match", m1["classic_mars"][0], src)
        put("mars_classic_n", m1["classic_mars"][1], src)
        put("mars_classic_share", m1["classic_mars"][0] / m1["classic_mars"][1], src)
        put("mars_null_match", m1["null"][0], src)
        put("mars_null_n", m1["null"][1], src)
        put("mars_null_share", m1["null"][0] / m1["null"][1], src)
        put("mars_moon_passer_match", m1["moon_passers"][0], src)
        put("mars_p", m1["HM1_p"], src)
        put("mars_verdict", "PASS" if m1["HM1_pass"] else "FAIL", src)
        put("mars_open_matches", m1["n_open_matches"], src)
        put("mars_open_countries", len({x["country"] for x in m1["open_matches"]}), src)
        for site, (k, nn) in m1["per_site"].items():
            slug = site.split()[0].strip(",").lower().replace("-", "")
            put(f"mars_site_{slug}", f"{k}/{nn}", src)

    # I1: low-Sun windows of the ridge matches (exploratory, Deviations 32)
    lw_path = D / "lighting_windows.parquet"
    if lw_path.exists():
        lw = pd.read_parquet(lw_path).set_index("cell_id")
        src = "data/derived/lighting_windows.parquet (scripts/build_lighting_windows.py)"
        three = lw[lw.route_reproduces & lw.route_reproduces_second_dem.fillna(False)]
        put("i1_three_tests_n", len(three), src)
        hero = lw[lw.route_reproduces & lw.route_reproduces_second_dem.fillna(False)
                  & lw.open_country & lw.l1_robust_second_dem.fillna(False)
                  & ~lw.in_exclusion_buffer.fillna(True)]
        put("i1_open_all_tests_n", len(hero), src)
        put("i1_open_all_tests_countries", ", ".join(sorted(hero.country.unique())), src)
        for cid, slug in (("E10K_660_-632", "baffin"), ("E10K_-355_-671", "argentina")):
            if cid in lw.index:
                r = lw.loc[cid]
                put(f"i1_{slug}_lat", float(r.lat), src)
                put(f"i1_{slug}_lon", float(r.lon), src)
                put(f"i1_{slug}_window_days", int(r.window_days), src)
                if int(r.window_days) > 0:
                    put(f"i1_{slug}_window_from", r.window_from, src)
                    put(f"i1_{slug}_window_to", r.window_to, src)
                put(f"i1_{slug}_window_lowsun_h", float(r.window_lowsun_min_per_day) / 60.0, src)
                put(f"i1_{slug}_lowsun_min_per_day", float(r.lowsun_min_per_day), src)
                put(f"i1_{slug}_shadow_e2", float(r.shadow_e2), src)
                put(f"i1_{slug}_route_D", float(r.route_D), src)
                put(f"i1_{slug}_frac_gt8", float(
                    pd.read_parquet(D / "access_leads.parquet").set_index("cell_id")
                    .loc[[cid], "frac_gt8"].iloc[0]), "data/derived/access_leads.parquet")
        put("i1_ridge_shadow_e2", float(lw.ridge_shadow_e2.iloc[0]), src)
        t2 = pd.read_parquet(D / "targets_L2.parquet")
        nat = t2[t2.target_id.eq("connecting_ridge") & ~t2.is_reference.astype(bool)]
        t2src = "data/derived/targets_L2.parquet"
        put("i1_ridge_native_shadow_e2_min", float(nat.shadow_e2.min()), t2src)
        put("i1_ridge_native_shadow_e2_max", float(nat.shadow_e2.max()), t2src)
        for cid, slug in (("E10K_-334_-677", "chile"), ("E10K_453_921", "da_qaidam")):
            if cid in lw.index:
                put(f"i1_{slug}_route_reproduces", bool(lw.loc[cid].route_reproduces), src)

    # multi-scale check of the Baffin lead (exploratory, Deviations 34)
    ms_path = D / "multiscale.json"
    if ms_path.exists():
        ms = json.loads(ms_path.read_text(encoding="utf-8"))
        src = "data/derived/multiscale.json (scripts/multiscale_check.py)"
        b = ms["leads"]["E10K_660_-632"]
        put("ms_baffin_holds_all_scales", all(v["holds"] for v in b["scales"].values()), src)
        put("ms_baffin_frac_gt8_5m", b["scales"]["5"]["frac_gt8"], src)
        put("ms_ridge_frac_gt8_5m", ms["moon"]["5"]["ridge"]["frac_gt8"], src)
        put("ms_baffin_frac_gt20_5m", b["scales"]["5"]["frac_gt20"], src)
        put("ms_ridge_frac_gt20_5m", ms["moon"]["5"]["ridge"]["frac_gt20"], src)
        put("ms_baffin_climb_10m", b["routes"]["10"]["climb_10"], src)
        put("ms_ridge_climb_10m", ms["moon"]["routes"]["10"]["climb_10"], src)

    # campaign coverage for Connecting Ridge (exploratory, Deviations 35)
    cp_path = D / "campaign_connecting_ridge.json"
    if cp_path.exists():
        cp = json.loads(cp_path.read_text(encoding="utf-8"))
        src = "data/derived/campaign_connecting_ridge.json (scripts/build_campaign.py)"
        put("camp_n_field", cp["n_field"], src)
        put("camp_two_leads", cp["campaign_two_leads"], src)
        put("camp_best_classic_alone", cp["best_classic_alone"], src)
        put("camp_baffin_joint", cp["per_site_joint"]["Baffin Island lead"], src)
        put("camp_n_facility", cp["n_facility"], src)
        put("camp_haughton_window_days",
            next(x["window_days"] for x in cp["sites"] if x["kind"] == "classic"), src)

    # Artemis atlas: V1 rule and low-Sun calendar per region (exploratory, Deviations 36)
    at_path = D / "artemis_atlas.json"
    if at_path.exists():
        at = json.loads(at_path.read_text(encoding="utf-8"))
        src = "data/derived/artemis_atlas.json (scripts/artemis_atlas.py)"
        put("atlas_n_regions", at["n_regions"], src)
        put("atlas_regions_with_lead", at["regions_with_lead_all_tests"], src)
        put("atlas_regions_with_lead_window",
            sum(r["n_all_tests_window"] > 0 for r in at["regions"]), src)
        put("atlas_leads_all_tests", sum(r["n_all_tests"] for r in at["regions"]), src)
        put("atlas_leads_slope_two_dems", sum(r.get("n_slope_two_dems", 0)
                                              for r in at["regions"]), src)
        sh = next(r for r in at["regions"] if r["target_id"] == "shackleton_rim")
        put("atlas_shackleton_slope_two_dems", sh["n_slope_two_dems"], src)
        put("atlas_shackleton_routes_two_dems", sh["n_routes_two_dems"], src)
        put("atlas_regions_no_lead",
            sum(r["n_leads"] == 0 for r in at["regions"]), src)

    doc = {"generated": dt.datetime.now().isoformat(timespec="minutes"), "numbers": n}
    OUT.write_text(json.dumps(doc, indent=1, ensure_ascii=False), encoding="utf-8")
    for k, val in n.items():
        print(f"{k:45s} {val['value']}")


if __name__ == "__main__":
    main()
