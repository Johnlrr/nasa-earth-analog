"""A9b — write every number table of docs/validation_report.md from the pipeline tables.

Each table lives between ``<!-- BEGIN:<name> -->`` and ``<!-- END:<name> -->`` in the report;
this script replaces the block content and leaves the prose alone, so the report never carries a
hand-typed number (PLAN 2b rule 3). Sources: verdicts.parquet (A15), fidelity.parquet (A11),
l1_robust_set.parquet (A12), relocations.csv (A14), bridge_bias.parquet (A16),
m1_stop_rule.json (B13), x1_checklist.parquet (B15), target_scarcity / multilens / sites (2c).

Usage: python scripts/report_tables.py [--check]   (--check: fail if the report is stale)
"""

from __future__ import annotations

import argparse
import json
import re

import pandas as pd

from similitude import io

DERIVED = io.REPO_ROOT / "data" / "derived"
REPORT = io.REPO_ROOT / "docs" / "validation_report.md"


def md_table(df: pd.DataFrame) -> str:
    cols = [str(c) for c in df.columns]
    lines = ["| " + " | ".join(cols) + " |", "|" + "---|" * len(cols)]
    for row in df.itertuples(index=False):
        cells = []
        for v in row:
            if v is None or (isinstance(v, float) and pd.isna(v)) or v is pd.NA:
                cells.append("—")
            elif isinstance(v, float):
                cells.append(f"{v:.3g}" if abs(v) < 1000 else f"{v:.0f}")
            else:
                cells.append(str(v).replace("|", "/").replace("\n", " "))
        lines.append("| " + " | ".join(cells) + " |")
    return "\n".join(lines)


def _level(v: pd.DataFrame) -> pd.Series:
    cell = v["cell_id"].fillna("").ne("")
    tgt = v["target_id"].fillna("").ne("")
    return pd.Series(["cell" if c else ("target" if t else "lens") for c, t in zip(cell, tgt,
                                                                                 strict=True)],
                     index=v.index)


# ============================================================================================
def t_verdicts() -> str:
    v = pd.read_parquet(DERIVED / "verdicts.parquet")
    v["level"] = _level(v)
    g = v.groupby(["lens_id", "level", "state"]).size().unstack("state", fill_value=0)
    g = g.reindex(columns=["TRANSFERS", "NO-ANALOG", "UNOBSERVED"], fill_value=0).reset_index()
    g.columns = ["lens", "level", "TRANSFERS", "NO-ANALOG", "UNOBSERVED"]
    cells = (v[v["level"].eq("cell") & v["state"].eq("TRANSFERS")]
             .groupby(["lens_id", "target_id"])["cell_id"].nunique().reset_index())
    cells.columns = ["lens", "target", "cells with a cell-level TRANSFERS verdict"]
    return md_table(g) + "\n\n" + md_table(cells)


def t_ledger() -> str:
    v = pd.read_parquet(DERIVED / "verdicts.parquet")
    v = v[_level(v).ne("cell") & v["state"].ne("TRANSFERS")]
    out = v[["lens_id", "target_id", "variable", "state", "value", "facility"]].copy()
    out["facility"] = out["facility"].fillna("").str.slice(0, 70)
    out.columns = ["lens", "target", "variable", "state", "value", "facility / why"]
    return md_table(out.fillna({"target": ""}))


def t_terrain_controls() -> str:
    f = pd.read_parquet(DERIVED / "fidelity.parquet")
    f = f[f["lens_id"].isin(["L1", "L2"]) & f["cell_id"].str.match(r"(CTRL|SEED)_", na=False)]
    exp = {}
    for c in io.load_controls():
        exp[c["id"].lower()] = c.get("expected")
    f["expected"] = [exp.get(re.sub(r"^(ctrl|seed)_", "", c.lower()).replace("_reloc", ""), "seed"
                             if c.startswith("SEED") else None) for c in f["cell_id"]]
    f["native rank"] = [f"{int(r)}/{int(n)}" if pd.notna(r) else "—"
                        for r, n in zip(f["native_rank"], f["n_native"], strict=True)]
    out = f[["lens_id", "target_id", "cell_id", "expected", "native rank", "native_rank_basis",
             "percentile"]].sort_values(["lens_id", "target_id", "cell_id"])
    out.columns = ["lens", "target", "control / seed", "expected", "native rank",
                   "rank basis", "null percentile"]
    vc = pd.read_parquet(DERIVED / "validation_controls.parquet")
    if "expectation_met" not in vc:
        raise KeyError("validation_controls.parquet has no expectation_met column")
    met = vc.dropna(subset=["expectation_met"])
    return (md_table(out) + f"\n\nPre-registered control expectations "
            f"(`config/controls.yaml`, all lenses, `validation_controls.parquet`): "
            f"{int(met['expectation_met'].astype(bool).sum())} of {len(met)} "
            f"control/lens/target checks met.")


def t_l1_robust() -> str:
    r = pd.read_parquet(DERIVED / "l1_robust_set.parquet")
    r = r[r["sample_role"].isin(["rank", "seed"])]
    g = r.groupby("target_id").agg(n=("cell_id", "size"), i=("in_i", "sum"), ii=("in_ii", "sum"),
                                   iii=("in_iii", "sum"), intersection=("robust", "sum"))
    g = g.reset_index()
    g.columns = ["target", "rank+seed cells", "(i) diagonal 11 descriptors",
                 "(ii) full metric 6 descriptors", "(iii) L = 60 m", "robust set (i)∩(ii)∩(iii)"]
    return md_table(g)


def t_relocations() -> str:
    r = pd.read_csv(DERIVED / "relocations.csv")
    out = r[["point_id", "lens_id", "valid_frac_orig", "valid_frac_new", "shift_km",
             "sigma_orig", "sigma_new", "percentile_orig", "percentile_new"]]
    out.columns = ["point", "lens", "valid land before", "after", "shift km", "σ before",
                   "σ after", "pct before", "pct after"]
    return md_table(out)


def t_m1() -> str:
    j = json.loads((DERIVED / "m1_stop_rule.json").read_text(encoding="utf-8"))
    rows = [{"site": k, "largest matched patch km²": v} for k, v in
            j["largest_patch_km2"].items()]
    checks = ", ".join(f"{k} = {v}" for k, v in j["checks"].items())
    floor = ", ".join(f"{k} {v}" for k, v in j["noise_floor"].items())
    q = json.loads((DERIVED / "m1_null_quantiles.json").read_text(encoding="utf-8"))
    return (md_table(pd.DataFrame(rows)) + f"\n\nRule: {j['rule']}. Noise floor (q95 of null "
            f"pixels, B14b; {q['D2300']['n_pixels']:,} null pixels in {q['n_footprints']} "
            f"footprints): {floor}. Lake Salda (relocated) total matched area "
            f"{j['matched_area_km2_lake_salda_relocated']:.2f} km², in fragments; largest "
            f"patch above. Checks: {checks}. **Verdict: {j['verdict']}** "
            f"(evaluated {j['evaluated']}). {j['consequence']}")


def t_x1() -> str:
    x = pd.read_parquet(DERIVED / "x1_checklist.parquet")
    named = x[x["sample_role"].isin(["control", "decoy", "seed"])]
    out = named[["cell_id", "sample_role", "n_met", "failed", "ice_check", "passes_all",
                 "ft_yr"]].rename(columns={"ft_yr": "freeze–thaw days/yr"})
    pool = x[x["sample_role"].isin(["rank", "null"])]
    ok = pool[pool["candidate"].astype(bool) & pool["qa_flag"].eq("ok")]
    v = pd.read_parquet(DERIVED / "verdicts.parquet")
    xt = v[v["lens_id"].eq("X1") & v["state"].eq("TRANSFERS") & v["cell_id"].fillna("").ne("")]
    qa = x.set_index("cell_id").loc[xt["cell_id"].unique(), "qa_flag"]
    not_ok = ", ".join(f"{c} (qa {q})" for c, q in qa[qa.ne("ok")].items()) or "none"
    return (md_table(out) + f"\n\nRank + null cells: {len(pool)}; meeting all three conditions, "
            f"not glacier ice, qa ok: {len(ok)} ({', '.join(ok['cell_id'])}). Cell-level X1 "
            f"TRANSFERS in verdicts.parquet (rank + seed; the A15 rule does not use qa_flag): "
            f"{len(qa)}; with a qa flag other than ok: {not_ok}.")


def t_bridge() -> str:
    b = pd.read_parquet(DERIVED / "bridge_bias.parquet")
    p = b.pivot_table(index=["parameter", "continuum_sensitive", "in_fidelity"],
                      columns="target_id", values="z_median").reset_index()
    p = p.sort_values(p.columns[3])
    level = b["level"].iloc[0]
    return md_table(p) + f"\n\nz = (Earth − target) / tolerance scale; median over Earth cells; " \
                         f"level: {level}."


def t_scarcity() -> str:
    s = pd.read_parquet(DERIVED / "target_scarcity.parquet").drop(
        columns=["usable_cells", "target_id"])
    s.columns = ["lens", "target", "TRANSFERS cells", "ice ok", "ice flag", "ice excluded",
                 "usable", "usable outside known-analog buffers", "sites",
                 "usable, B10-downgraded", "usable, not B10-downgraded (incl. unreviewed)",
                 "of which B10-unreviewed"]
    return md_table(s)


def t_site_sensitivity() -> str:
    """2c post hoc distances: number of sites and showcase set at 100 / 150 / 200 km."""
    import sys

    sys.path.insert(0, str(io.REPO_ROOT / "scripts"))
    import sites as st

    v = pd.read_parquet(DERIVED / "verdicts.parquet")
    prof = pd.read_parquet(DERIVED / "cell_profiles.parquet")
    partners, down = st.load_partners(), st.b10_downgrades()
    rows = []
    for km in (100.0, 150.0, 200.0):
        b = st.build(v, prof, partners, cluster_km=km, multilens_km=km, downgraded=down)
        s = b["sites"]
        show = s[s["showcase"].ne("")].sort_values("n_cells", ascending=False)
        ee = b["multilens"].query("partner_state == 'engine TRANSFERS'")["site_id"].unique()
        rows.append({"km (cluster = multi-lens)": int(km), "sites": len(s),
                     "sites with an engine partner (L1/L2 + X1)": "; ".join(
                         s.set_index("site_id").loc[list(ee), "name"]) or "—",
                     "showcase": "; ".join(f"{n} ({r})" for n, r in
                                           zip(show["name"], show["showcase"], strict=True))})
    return md_table(pd.DataFrame(rows))


def t_multilens() -> str:
    m = pd.read_parquet(DERIVED / "multilens.parquet")
    s = pd.read_parquet(DERIVED / "sites.parquet").set_index("site_id")["name"]
    m["site"] = m["site_id"].map(s)
    return md_table(m[["site", "cell_id", "lenses", "partner_lens", "partner_label",
                       "distance_km", "partner_state"]])


def t_sites() -> str:
    s = pd.read_parquet(DERIVED / "sites.parquet")
    s = s[s["showcase"].ne("")].sort_values("n_cells", ascending=False)
    s["b10_unreviewed_cells"] = [len([c for c in x.split(",") if c]) for x in
                                 s["b10_unreviewed_cells"]]
    s = s.rename(columns={"b10_unreviewed_cells": "n_b10_unreviewed"})
    return md_table(s[["name", "n_cells", "max_span_km", "lenses_engine_confirmed",
                       "lenses_engine_semiquant", "lenses_hypothesis", "n_b10_unreviewed",
                       "lenses_literature_only", "n_ice_flag", "n_in_exclusion", "attention_n",
                       "hidden_status", "showcase"]])


# ============================================================================================
# PLAN 2d: validity summary and mission value (scripts/mission_value.py outputs)
# ============================================================================================
def _mv() -> dict:
    return json.loads((DERIVED / "mission_value.json").read_text(encoding="utf-8"))


def _mission() -> dict:
    return io.load_yaml(io.CONFIG_DIR / "mission.yaml")


def _pct(x: float, nd: int = 0) -> str:
    return f"{100 * x:.{nd}f} %"


def t_mission_headline() -> str:
    """Headline sentences of PLAN 2d, every number read from mission_value.json."""
    m, req = _mv(), _mission()["requirements"]
    crit = pd.read_parquet(DERIVED / "mission_criteria.parquet")
    kept = crit[crit["group"].eq("Engine match")]
    cl, ref, red = m["l1_classic_controls"], m["l1_reference"], m["rediscovery"]
    null = {r["target_id"]: r for r in m["l1_null"]}
    sh = next(r for r in red["targets"] if r["target_id"] == "shackleton_rim")
    cr = next(r for r in red["targets"] if r["target_id"] == "connecting_ridge")
    x1, cov, ncr = m["x1_controls"], m["coverage"], null["connecting_ridge"]
    q_land, q_eva = req["artemis3_landing_slope"]["quote"], req["artemis3_eva_slope"]["quote"]
    both = int((kept["in_range_frac_gt8"] & kept["in_range_frac_gt20"]).sum())
    return "\n".join([
        f"- **Read beside NASA's Artemis III requirements** (\"{q_land}\"; \"{q_eva}\"): "
        f"{_pct(ref['frac_gt8'])} of the Connecting Ridge reference footprint is steeper than "
        f"8° (the contour NASA draws on its landing-slope map) and {_pct(ref['frac_gt20'], 1)} "
        f"is steeper than 20°. {both} of the {len(kept)} usable Earth cells the engine keeps for "
        f"it lie inside the range of the {int(crit['n_target_footprints'].iloc[0])} Connecting "
        f"Ridge footprints on both shares; of the 4 km footprints of {cl['n']} classic analog "
        f"field sites (the L1 controls), {cl['in_range_frac_gt8']} do on the 8° share (median "
        f"{_pct(cl['frac_gt8_median'], 1)}, a factor {m['l1_under_sampling']:.1f} below the "
        f"target; maximum {_pct(cl['frac_gt8_max'])}) and {cl['in_range_frac_gt20']} do on the "
        f"20° share, which therefore does not discriminate. A consistency check, not an "
        f"independent test: both shares are descriptors the engine selects on, and they compare "
        f"Earth with Moon, not with NASA's maps (§7b).",
        f"- **How selective the L1 test is.** Random bare land (null sample) enters the robust "
        f"set for Connecting Ridge in {ncr['robust_null']} of {ncr['n_null']} cells and for the "
        f"Shackleton inner wall in {null['shackleton_rim']['robust_null']} of "
        f"{null['shackleton_rim']['n_null']}; {cl['robust']} of the {cl['n_scored']} classic "
        f"controls enter it. A null cell that passes is not an error: it is terrain that "
        f"matches. Extrapolated to the {ncr['bare_land_cells']:,} bare-land cells, about "
        f"{ncr['extrapolated_cells']:,} cells (95 % CI {ncr['extrapolated_lo']:,}–"
        f"{ncr['extrapolated_hi']:,}) would pass for Connecting Ridge, so \"2 usable cells\" "
        f"describes our 307-cell sample, not the Earth.",
        f"- **Sanity check against known-analog zones.** {red['rank_in_zone']} of the "
        f"{red['rank_n']} cells the terrain screen picked lie in known-analog zones "
        f"({_pct(red['rank_rate'])}), against {_pct(red['base_rate'], 1)} of all bare land but "
        f"{_pct(red['matched_rate'])} of bare land with the same coarse slope and relief "
        f"({red['matched_enrichment']:.1f}-fold): most of the excess is steep dry terrain "
        f"itself. By site, {sh['sites_with_zone_cell']} of the {sh['sites']} Shackleton-wall "
        f"sites (the largest, Atacama–Puna) and {cr['sites_with_zone_cell']} of the "
        f"{cr['sites']} Connecting Ridge sites hold a cell in a zone of our list "
        f"(`config/exclusion_zones.yaml`, which does not list Qaidam).",
        f"- **X1 controls on the current checklist:** {len(x1['positive_pass'])} of "
        f"{x1['positive_n']} positive controls pass (Beacon Valley is the calibration site, "
        f"Axel Heiberg is independent) and {len(x1['decoy_rejected'])} of {x1['decoy_n']} wet "
        f"lowland decoys are rejected. M1: {m['m1_checks']['passed']} of {m['m1_checks']['n']} "
        f"pre-registered checks pass, so the stop rule is {m['m1_checks']['verdict']}.",
        f"- **Test-matrix coverage (best state over a lens' targets):** by this engine's "
        f"measure a field site reproduces {cov['L1']['TRANSFERS']} of "
        f"{sum(cov['L1'].values())} L1 test variables, {cov['L2']['TRANSFERS']} of "
        f"{sum(cov['L2'].values())} for L2 and {cov['X1']['TRANSFERS']} of "
        f"{sum(cov['X1'].values())} for X1 (one of them the day length, which the polar X1 "
        f"sites do not reproduce in the midnight-sun season); every other row names the "
        f"facility that replaces "
        f"the field site, or is marked unobserved (`docs/test_protocols.md`). M1 publishes no "
        f"site.",
    ])


def t_validity() -> str:
    m = _mv()
    null = {r["target_id"]: r for r in m["l1_null"]}
    cl, x1, m1 = m["l1_classic_controls"], m["x1_controls"], m["m1_checks"]

    def nul(t):
        r = null[t]
        return (f"{r['robust_null']}/{r['n_null']} = {_pct(r['null_rate'], 1)} "
                f"(95 % CI {_pct(r['null_ci_lo'], 2)}–{_pct(r['null_ci_hi'], 1)}; about "
                f"{r['extrapolated_cells']:,} of {r['bare_land_cells']:,} bare-land cells, "
                f"CI {r['extrapolated_lo']:,}–{r['extrapolated_hi']:,})")
    rows = [
        {"lens": "L1", "check": "random bare land (null) in the robust set, Connecting Ridge",
         "result": nul("connecting_ridge"),
         "reading": "pass rate of random bare land = unbiased prevalence estimate"},
        {"lens": "L1", "check": "random bare land (null) in the robust set, Shackleton wall",
         "result": nul("shackleton_rim"),
         "reading": "pass rate of random bare land = unbiased prevalence estimate"},
        {"lens": "L1", "check": "screened cells (rank) in the robust set",
         "result": "; ".join(f"{t}: {null[t]['robust_rank']}/{null[t]['n_rank']}" for t in null),
         "reading": "the coarse screen was aimed at Connecting Ridge"},
        {"lens": "L1", "check": "classic analog field sites (L1 controls) in the robust set",
         "result": f"{cl['robust']}/{cl['n_scored']}",
         "reading": "pre-registered 'high' for Haughton is a miss (§3); no accepted "
                    "Connecting Ridge analog exists to serve as a positive control"},
        {"lens": "L2", "check": "Sun geometry of the lunar south pole",
         "result": "NO-ANALOG at every Earth site", "reading": "as pre-registered (A7)"},
        {"lens": "M1", "check": "pre-registered pixel checks (B14a)",
         "result": f"{m1['passed']}/{m1['n']} → stop rule {m1['verdict']}",
         "reading": "nothing published for M1"},
        {"lens": "X1", "check": "positive controls passing all 3 conditions",
         "result": f"{len(x1['positive_pass'])}/{x1['positive_n']} "
                   f"({', '.join(x1['positive_pass'])})",
         "reading": "Beacon Valley is calibration; Axel Heiberg is independent"},
        {"lens": "X1", "check": "wet-lowland decoys rejected",
         "result": f"{len(x1['decoy_rejected'])}/{x1['decoy_n']}",
         "reading": "semi-quantitative, floors set after seeing data (Deviations 3); seed "
                    "list not provably pre-registered (Deviations 23)"},
    ]
    return md_table(pd.DataFrame(rows))


def t_mission_criteria() -> str:
    c = pd.read_parquet(DERIVED / "mission_criteria.parquet")
    req, cav = _mission()["requirements"], _mission()["criteria_caveat"]
    out = pd.DataFrame({
        "group": c["group"], "site": c["name"].fillna(c["id"]), "cell": c["id"],
        "median slope °": c["slope_p50"].round(1),
        "steeper than 8° (30 m baseline)": [_pct(x) for x in c["frac_gt8"]],
        "steeper than 20° (30 m baseline)": [_pct(x, 1) for x in c["frac_gt20"]],
        "km of traverse for the > 8° terrain of 10 km on the target": c[
            "km_for_10km_of_target"].round(0).astype(int),
        "8° share inside target range": c["in_range_frac_gt8"].map({True: "yes", False: "no"}),
        "20° share inside target range": c["in_range_frac_gt20"].map({True: "yes",
                                                                       False: "no"})})
    r = c.iloc[0]
    return (md_table(out) + f"\n\nTarget range = minimum to maximum over the "
            f"{int(r['n_target_footprints'])} Connecting Ridge footprints (PGDA 78 Site01): "
            f"8° share {_pct(r['range_lo_frac_gt8'])}–{_pct(r['range_hi_frac_gt8'])}, 20° share "
            f"{_pct(r['range_lo_frac_gt20'], 1)}–{_pct(r['range_hi_frac_gt20'], 1)}. "
            f"Requirements: \"{req['artemis3_landing_slope']['quote']}\" and "
            f"\"{req['artemis3_eva_slope']['quote']}\" — "
            f"{req['artemis3_landing_slope']['document']} "
            f"({req['artemis3_landing_slope']['source']}). The traverse column assumes that "
            f"the share of steep terrain along a path equals the areal share of the footprint. "
            f"Caveat: {cav}")


def t_coverage() -> str:
    import sys

    sys.path.insert(0, str(io.REPO_ROOT / "scripts"))
    import mission_value as mv

    cov = mv.coverage(pd.read_parquet(DERIVED / "verdicts.parquet"))
    g = cov.groupby(["lens_id", "state"])["variable"].agg("; ".join).unstack(fill_value="—")
    g = g.reindex(columns=mv.STATE_ORDER, fill_value="—").reset_index()
    g.columns = ["lens", "TRANSFERS (field)", "NO-ANALOG (facility)", "UNOBSERVED"]
    return (md_table(g) + "\n\nOne state per lens and variable: the best state over the lens' "
            "targets (L1 slope–roughness and L2 shadow casting transfer for both targets; M1 "
            "aqueous minerals are NO-ANALOG for the two analog targets and UNOBSERVED for the "
            "other two; M1's only TRANSFERS row is the day–night cycle from the ledger, and M1 "
            "publishes no site). The day–night cycle is a planet-level ledger row (a Mars sol "
            "is 24.6 h): the X1 sites that pass are polar and do not reproduce it in the "
            "midnight-sun field season, so at those sites X1 reproduces 1 variable, not 2. "
            "The null extrapolation of §1 refers to cells passing the robust set, before the "
            "ice filter and the visual review.")


def t_task_attention() -> str:
    t = pd.read_parquet(DERIVED / "task_attention.parquet")
    s = pd.read_parquet(DERIVED / "sites.parquet")
    p = t.pivot(index="key", columns="context", values="n_pubs")
    s = s[s["query"].notna()].copy()
    s["anchor"] = [next((k for k in p.index if k in cells.split(",")), None)
                   for cells in s["cells"]]
    out = pd.DataFrame({
        "site": s["name"],
        "B8 context (Mars OR Moon OR lunar OR planetary), site name": s["attention_site_name"],
        "Moon context": s["anchor"].map(p["moon"]), "Mars context": s["anchor"].map(p["mars"]),
        "site Attention used for hidden_status (max with member cells)": s["attention_n"],
        "hidden_status": s["hidden_status"]}).sort_values("site")
    return (md_table(out) + "\n\nContexts (both subsets of the B8 context): Moon = "
            "`(analog OR analogue) AND (Moon OR lunar)`, Mars = `(analog OR analogue) AND "
            "(Mars)`, on the same site-name query (OpenAlex title/abstract search, "
            f"{t['date'].max()}; the B8 counts may be a day older). The last count column is "
            "the maximum of the site-name count and the member cells' counts (for Peary Land "
            "the cell name is \"Greenland\"). Supplementary: `hidden_status` is not recomputed "
            "from the task counts.")



# ============================================================================================
# PLAN 2e: checks against known truth (scripts/l1_regions.py, scripts/cross_dem.py)
# ============================================================================================
def _reg() -> dict:
    return json.loads((DERIVED / "l1_regions.json").read_text(encoding="utf-8"))


REGION_LABELS = {"connecting_ridge": "Connecting Ridge", "shackleton_rim": "Shackleton inner wall",
                 "de_gerlache_rim": "de Gerlache rim", "malapert_massif": "Malapert massif",
                 "nobile_rim_1": "Nobile rim 1", "peak_near_shackleton": "peak near Shackleton"}


def _label(region: str) -> str:
    return REGION_LABELS.get(region, region.replace("_", " "))


def t_checks_headline() -> str:
    """Headline sentences of PLAN 2e, every number read from the 2e tables."""
    r = _reg()
    c = pd.read_parquet(DERIVED / "cross_dem.parquet")
    c = c[c["alt_ok"]]
    pub = c[((c["group"].eq("wall match") & c["target_id"].eq("shackleton_rim"))
             | (c["group"].ne("wall match") & c["target_id"].eq("connecting_ridge")))]
    same = int((pub["robust"] == pub["robust_glo30"]).sum())
    ridge = c[c["target_id"].eq("connecting_ridge")].set_index("cell_id")
    prof = pd.read_parquet(DERIVED / "cell_profiles.parquet").set_index("cell_id")["ice_check"]
    usable = [i for i in ridge[ridge["group"].eq("ridge match")].index
              if not str(prof.get(i, "")).startswith("excluded")]
    sites = pd.read_parquet(DERIVED / "sites.parquet")
    names = {x: s.name.split(",")[0] for s in sites.itertuples() for x in s.cells.split(",")}

    def dem_line(i):
        x = ridge.loc[i]
        verdict = "stays" if x["robust"] else "does **not** stay"
        return (f"{names.get(i, i)} {verdict} in the robust set with {x['alt_source']} (native "
                f"rank {int(x['nr_i'])}/{int(x['nr_ii'])}/{int(x['nr_iii'])} of "
                f"{int(x['n_i'])}; the rule needs at least {x['n_i'] / 2:g} in each)")
    reg = pd.read_parquet(DERIVED / "l1_regions.parquet")
    reg = reg[reg["robust"] & reg["sample_role"].isin(["rank", "seed"])]
    n_reg = {i: sorted(reg[reg["cell_id"].eq(i)]["target_id"]) for i in usable}
    lc = r["lunar_control"]
    ctrl = pd.read_parquet(DERIVED / "l1_lunar_control.parquet")
    wall = ctrl[ctrl["reference_region"].eq("shackleton_rim")]
    w_same = wall[wall["candidate_region"].eq("shackleton_rim")].iloc[0]
    w_other = wall[wall["candidate_region"].ne("shackleton_rim")]
    p = pd.read_parquet(DERIVED / "l1_prevalence.parquet").set_index("target_id")
    cr, sh = p.loc["connecting_ridge"], p.loc["shackleton_rim"]
    return "\n".join([
        f"- **The slope code reproduces NASA's own product.** On the six PGDA 78 sites our "
        f"formula at 5 m differs from NASA's slope rasters by at most "
        f"{r['nasa_slope_max_abs_diff_deg']:.4f}° on the median slope and "
        f"{100 * r['nasa_frac_max_abs_diff']:.3f} points on the 8° and 20° shares.",
        f"- **A second, independent Earth DEM.** Recomputed from NASADEM or ArcticDEM, "
        f"{same} of {len(pub)} verdicts are unchanged (ridge cells, classic controls, a sample "
        "of wall cells). " + "; ".join(dem_line(i) for i in usable) + ". A verdict that "
        "changes with the DEM is marginal and is reported as such.",
        "- **Six regions, not two (exploratory).** " + "; ".join(
            f"{names.get(i, i)} is in the robust set of {len(v)} of the 6 PGDA 78 regions "
            f"({', '.join(_label(x) for x in v)})" for i, v in n_reg.items()) + ".",
        f"- **Known truth on the Moon.** Scored like Earth cells, footprints of the same "
        f"region pass in {lc['same_pass']} of {lc['same_n']} cases and footprints of other "
        f"regions in {lc['other_pass']} of {lc['other_n']}; for the Shackleton inner wall, "
        f"{int(w_same['n_pass'])} of {int(w_same['n'])} against "
        f"{int(w_other['n_pass'].sum())} of {int(w_other['n'].sum())}. The test separates the "
        f"steep wall from ridge terrain; it does not tell the ridge and rim regions apart: it "
        f"recognises a terrain class, not a named place.",
        f"- **Unbiased prevalence.** In {int(cr['n'])} random bare-land cells, "
        f"{int(cr['pass'])} pass for Connecting Ridge ({_pct(cr['rate'], 2)}, 95 % CI "
        f"{_pct(cr['ci_lo'], 2)}–{_pct(cr['ci_hi'], 2)}) and {int(sh['pass'])} for the "
        f"Shackleton inner wall ({_pct(sh['rate'], 2)}, {_pct(sh['ci_lo'], 2)}–"
        f"{_pct(sh['ci_hi'], 2)}); Fisher exact p = {r['ridge_vs_wall_p_fisher']:.2g}.",
    ])



def t_nasa_slope() -> str:
    c = pd.read_parquet(DERIVED / "nasa_slope_check.parquet")
    r = _reg()
    out = pd.DataFrame({
        "region (PGDA 78)": [f"{_label(a)} ({b})" for a, b in zip(c["region"], c["pgda_site"],
                                                                  strict=True)],
        "median slope °, NASA raster": c["slope_p50_nasa"].round(2),
        "ours at 5 m": c["slope_p50_ours_5m"].round(2),
        "> 8°, NASA raster": [_pct(x, 1) for x in c["frac_gt8_nasa"]],
        "> 8°, ours 5 m": [_pct(x, 1) for x in c["frac_gt8_ours_5m"]],
        "> 8°, ours 30 m": [_pct(x, 1) for x in c["frac_gt8_ours_30m"]],
        "> 20°, NASA raster": [_pct(x, 1) for x in c["frac_gt20_nasa"]],
        "> 20°, ours 5 m": [_pct(x, 1) for x in c["frac_gt20_ours_5m"]],
        "> 20°, ours 30 m": [_pct(x, 1) for x in c["frac_gt20_ours_30m"]]})
    d8 = (c["frac_gt8_ours_30m"] - c["frac_gt8_ours_5m"]).abs().max()
    d20 = (c["frac_gt20_ours_30m"] - c["frac_gt20_ours_5m"]).abs().max()
    return (md_table(out) + f"\n\nCentral 4 km footprint of each PGDA 78 site; NASA raster = "
            f"`SiteNN_final_adj_5mpp_slp.tif`. Largest difference between our formula at 5 m "
            f"and NASA's slope raster: {r['nasa_slope_max_abs_diff_deg']:.4f}° on the median "
            f"slope, {100 * r['nasa_frac_max_abs_diff']:.3f} percentage points on the shares. "
            f"Going from a 5 m to a 30 m baseline moves the 8° share by at most "
            f"{100 * d8:.1f} points and the 20° share by at most {100 * d20:.1f} points.")


def t_cross_dem() -> str:
    c = pd.read_parquet(DERIVED / "cross_dem.parquet")
    c = c[c["alt_ok"]]
    g = c.groupby(["group", "target_id"]).agg(
        cells=("cell_id", "size"), glo30=("robust_glo30", "sum"), alt=("robust", "sum"),
        agree=("cell_id", lambda s: int((c.loc[s.index, "robust"]
                                         == c.loc[s.index, "robust_glo30"]).sum())))
    g = g.reset_index()
    g.columns = ["cells", "target", "n", "robust with Copernicus GLO-30",
                 "robust with the second DEM", "same verdict"]
    d = c[c["group"].ne("wall match") & c["target_id"].eq("connecting_ridge")].copy()
    s = pd.read_parquet(DERIVED / "sites.parquet")
    names = {x: r.name for r in s.itertuples() for x in r.cells.split(",")}
    d["site"] = [names.get(i, n) if isinstance(names.get(i, n), str) else i
                 for i, n in zip(d["cell_id"], d["name"], strict=True)]
    cells = pd.DataFrame({
        "cells": d["group"], "site": d["site"], "cell": d["cell_id"],
        "second DEM": d["alt_source"],
        "> 8°, GLO-30": [_pct(x, 1) for x in d["frac_gt8_glo30"]],
        "> 8°, second DEM": [_pct(x, 1) for x in d["frac_gt8_alt"]],
        "native rank (i)/(ii)/(iii), second DEM": [
            f"{int(a)}/{int(b)}/{int(e)} of {int(n)}" for a, b, e, n in
            zip(d["nr_i"], d["nr_ii"], d["nr_iii"], d["n_i"], strict=True)],
        "robust, GLO-30": d["robust_glo30"].map({True: "yes", False: "no"}),
        "robust, second DEM": d["robust"].map({True: "yes", False: "no"})})
    return (md_table(g) + "\n\n" + md_table(cells.sort_values(["cells", "site"]))
            + "\n\nSecond DEM: NASADEM (NASA, SRTM C-band radar of 2000) between 56° S and "
            "60° N, ArcticDEM mosaic (stereo optical, averaged to 30 m) above 60° N; same "
            "code, baselines and rule. \"Wall match\" = a seeded sample of the cells kept for "
            "the Shackleton inner wall. Three of the five ridge cells are ice-excluded (§7) "
            "and are listed only for the DEM comparison.")


def t_lunar_control() -> str:
    c = pd.read_parquet(DERIVED / "l1_lunar_control.parquet")
    c["txt"] = c["n_pass"].astype(str) + "/" + c["n"].astype(str)
    p = c.pivot(index="reference_region", columns="candidate_region", values="txt")
    p.index = [_label(i) for i in p.index]
    p.columns = [_label(i) for i in p.columns]
    p = p.reset_index().rename(columns={"index": "reference region ↓ / footprints of →"})
    r = _reg()["lunar_control"]
    return (md_table(p) + f"\n\nLeave-one-out on the Moon: each population footprint is "
            f"scored like an Earth cell against each region's reference and must pass all "
            f"three configurations. Same region: {r['same_pass']} of {r['same_n']} pass; other "
            f"regions: {r['other_pass']} of {r['other_n']}. Footprints of one region are "
            f"3–4 km apart, so they are not independent.")


def t_region_prevalence() -> str:
    p = pd.read_parquet(DERIVED / "l1_prevalence.parquet")
    r = _reg()
    out = pd.DataFrame({
        "region": [_label(x) + ("" if pub else " (medoid reference, exploratory)")
                   for x, pub in zip(p["target_id"], p["published"], strict=True)],
        "pre-registered null": p["null_pass"].astype(str) + "/" + p["null_n"].astype(str),
        "extension (same rule, new seed)": p["null2_pass"].astype(str) + "/"
        + p["null2_n"].astype(str),
        "combined": p["pass"].astype(str) + "/" + p["n"].astype(str),
        "pass rate (95 % CI)": [f"{_pct(a, 2)} ({_pct(b, 2)}–{_pct(c, 2)})" for a, b, c in
                                zip(p["rate"], p["ci_lo"], p["ci_hi"], strict=True)],
        "bare-land cells (95 % CI)": [f"{a:,} ({b:,}–{c:,})" for a, b, c in
                                      zip(p["cells"], p["cells_lo"], p["cells_hi"],
                                          strict=True)],
        "screened cells kept (rank + seed)": [r["regions_rank_seed_robust"][x]
                                              for x in p["target_id"]]})
    return (md_table(out) + "\n\nPass = robust set (all three configurations), before the ice "
            "filter and the visual review. Connecting Ridge against the Shackleton inner wall "
            f"on the combined random sample: Fisher exact p = "
            f"{r['ridge_vs_wall_p_fisher']:.2g}. The last column comes from the sample "
            "screened towards Connecting Ridge and is not a prevalence.")


def t_region_matches() -> str:
    s = pd.read_parquet(DERIVED / "l1_regions.parquet")
    s = s[s["sample_role"].isin(["rank", "seed"]) & s["robust"]]
    s = s[s["cell_id"].isin(s[s["target_id"].ne("shackleton_rim")]["cell_id"])]
    sites = pd.read_parquet(DERIVED / "sites.parquet")
    names = {x: r.name for r in sites.itertuples() for x in r.cells.split(",")}
    prof = pd.read_parquet(DERIVED / "cell_profiles.parquet").set_index("cell_id")
    g = s.groupby("cell_id").agg(
        regions=("target_id", lambda x: ", ".join(_label(i) for i in sorted(x))),
        n=("target_id", "size"), lat=("lat", "first"), lon=("lon", "first")).reset_index()
    g["site"] = [names.get(c, prof["name"].get(c, c)) for c in g["cell_id"]]
    g["ice filter"] = [prof["ice_check"].get(c, "not assessed") for c in g["cell_id"]]
    g = g.sort_values(["n", "cell_id"], ascending=[False, True])
    out = g[["site", "cell_id", "lat", "lon", "n", "regions", "ice filter"]]
    out.columns = ["site", "cell", "lat", "lon", "regions matched (of 6)", "regions",
                   "ice filter (A13)"]
    return (md_table(out) + "\n\nScreened cells (rank + seed) in the robust set of at least "
            "one ridge, rim or massif region. Only the Connecting Ridge and Shackleton rows "
            "are verdicts; the other four regions use a medoid reference and are exploratory.")



TABLES = {"verdicts": t_verdicts, "ledger": t_ledger, "terrain_controls": t_terrain_controls,
          "l1_robust": t_l1_robust, "relocations": t_relocations, "m1": t_m1, "x1": t_x1,
          "bridge": t_bridge, "scarcity": t_scarcity, "site_sensitivity": t_site_sensitivity,
          "multilens": t_multilens, "sites": t_sites,
          "mission_headline": t_mission_headline, "validity": t_validity,
          "mission_criteria": t_mission_criteria, "coverage": t_coverage,
          "task_attention": t_task_attention,
          "checks_headline": t_checks_headline, "nasa_slope": t_nasa_slope,
          "cross_dem": t_cross_dem,
          "lunar_control": t_lunar_control, "region_prevalence": t_region_prevalence,
          "region_matches": t_region_matches}


def fill(text: str, tables: dict) -> str:
    for name, fn in tables.items():
        pat = re.compile(rf"(<!-- BEGIN:{name} -->\n).*?(<!-- END:{name} -->)", re.S)
        if not pat.search(text):
            raise KeyError(f"marker {name} missing in report")
        body = fn()
        text = pat.sub(lambda m, body=body: m.group(1) + body + "\n" + m.group(2), text)
    return text


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--check", action="store_true")
    args = ap.parse_args()
    old = REPORT.read_text(encoding="utf-8")
    new = fill(old, TABLES)
    if args.check:
        raise SystemExit(0 if new == old else "validation_report.md is stale: run "
                         "scripts/report_tables.py")
    REPORT.write_text(new, encoding="utf-8")
    print(f"{REPORT}: {len(TABLES)} tables refreshed")


if __name__ == "__main__":
    main()
