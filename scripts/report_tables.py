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
    x1, cov = m["x1_controls"], m["coverage"]
    q_land, q_eva = req["artemis3_landing_slope"]["quote"], req["artemis3_eva_slope"]["quote"]
    return "\n".join([
        f"- **Read against NASA's own Artemis III requirements** (\"{q_land}\"; "
        f"\"{q_eva}\"): {_pct(ref['frac_gt8'])} of "
        f"the Connecting Ridge reference footprint is steeper than the 8° contour of NASA's "
        f"landing-slope map and {_pct(ref['frac_gt20'], 1)} is no-EVA terrain (> 20°). "
        f"{int((kept['in_range_frac_gt8'] & kept['in_range_frac_gt20']).sum())} of the "
        f"{len(kept)} usable Earth cells the engine keeps for it lie "
        f"inside the range of the {int(crit['n_target_footprints'].iloc[0])} Connecting Ridge "
        f"footprints on both readings; {cl['in_range_frac_gt8']} of {cl['n']} classic "
        f"lunar-analog controls do on the 8° reading (their median is "
        f"{_pct(cl['frac_gt8_median'], 1)}, a factor {m['l1_under_sampling']:.1f} below the "
        f"target; maximum {_pct(cl['frac_gt8_max'])}). Same formula and 30 m baseline on both "
        f"worlds; not a landing-site certification.",
        f"- **The L1 test is specific.** Random bare land (null sample) enters the robust set "
        f"for Connecting Ridge in {null['connecting_ridge']['robust_null']} of "
        f"{null['connecting_ridge']['n_null']} cells and for the Shackleton inner wall in "
        f"{null['shackleton_rim']['robust_null']} of {null['shackleton_rim']['n_null']}; "
        f"{cl['robust']} of {cl['n']} classic controls enter it.",
        f"- **Blind rediscovery.** The terrain screen saw only DEM slope and relief, yet "
        f"{red['rank_in_zone']} of its {red['rank_n']} picks fall inside known-analog zones "
        f"against a base rate of {_pct(red['base_rate'], 1)} of bare land "
        f"({red['rank_enrichment']:.0f}-fold, binomial p = {red['rank_p_binomial']:.0e}); the "
        f"fine engine concentrates further for the Shackleton inner wall "
        f"({sh['robust_in_zone']} of {sh['robust_n']} kept against {sh['other_in_zone']} of "
        f"{sh['other_n']} not kept, Fisher p = {sh['p_fisher']:.0e}). For Connecting Ridge, "
        f"{cr['robust_in_zone'] or 'none'} of the {cr['robust_n']} kept cells lies in a "
        f"known-analog zone.",
        f"- **X1 controls on the current checklist:** {len(x1['positive_pass'])} of "
        f"{x1['positive_n']} positive controls pass (Beacon Valley is the calibration site, "
        f"Axel Heiberg is independent) and {len(x1['decoy_rejected'])} of {x1['decoy_n']} wet "
        f"lowland decoys are rejected. M1: {m['m1_checks']['passed']} of {m['m1_checks']['n']} "
        f"pre-registered checks pass, so the stop rule is {m['m1_checks']['verdict']}.",
        f"- **Test-matrix coverage:** a field campaign can be credited with "
        f"{cov['L1']['TRANSFERS']} of {sum(cov['L1'].values())} L1 test variables, "
        f"{cov['L2']['TRANSFERS']} of {sum(cov['L2'].values())} for L2 and "
        f"{cov['X1']['TRANSFERS']} of {sum(cov['X1'].values())} for X1; every other row names "
        f"the facility that replaces the field site, or is marked unobserved "
        f"(`docs/test_protocols.md`).",
    ])


def t_validity() -> str:
    m = _mv()
    null = {r["target_id"]: r for r in m["l1_null"]}
    cl, x1, m1 = m["l1_classic_controls"], m["x1_controls"], m["m1_checks"]

    def nul(t):
        r = null[t]
        return (f"{r['robust_null']}/{r['n_null']} = {_pct(r['null_rate'], 1)} "
                f"(95 % CI {_pct(r['null_ci_lo'], 2)}–{_pct(r['null_ci_hi'], 1)})")
    rows = [
        {"lens": "L1", "check": "random bare land (null) in the robust set, Connecting Ridge",
         "result": nul("connecting_ridge"), "reading": "false-positive rate of the test"},
        {"lens": "L1", "check": "random bare land (null) in the robust set, Shackleton wall",
         "result": nul("shackleton_rim"), "reading": "false-positive rate of the test"},
        {"lens": "L1", "check": "screened cells (rank) in the robust set",
         "result": "; ".join(f"{t}: {null[t]['robust_rank']}/{null[t]['n_rank']}" for t in null),
         "reading": "the coarse screen was aimed at Connecting Ridge"},
        {"lens": "L1", "check": "classic lunar-analog controls in the robust set",
         "result": f"{cl['robust']}/{cl['n']}",
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
         "reading": "semi-quantitative, floors set after seeing data (Deviations 3)"},
    ]
    return md_table(pd.DataFrame(rows))


def t_mission_criteria() -> str:
    c = pd.read_parquet(DERIVED / "mission_criteria.parquet")
    req, cav = _mission()["requirements"], _mission()["criteria_caveat"]
    out = pd.DataFrame({
        "group": c["group"], "site": c["name"].fillna(c["id"]), "cell": c["id"],
        "median slope °": c["slope_p50"].round(1),
        "steeper than 8° (landing-map contour)": [_pct(x) for x in c["frac_gt8"]],
        "steeper than 20° (no-EVA)": [_pct(x, 1) for x in c["frac_gt20"]],
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
            f"({req['artemis3_landing_slope']['source']}). Caveat: {cav}")


def t_coverage() -> str:
    import sys

    sys.path.insert(0, str(io.REPO_ROOT / "scripts"))
    import mission_value as mv

    cov = mv.coverage(pd.read_parquet(DERIVED / "verdicts.parquet"))
    g = cov.groupby(["lens_id", "state"])["variable"].agg("; ".join).unstack(fill_value="—")
    g = g.reindex(columns=mv.STATE_ORDER, fill_value="—").reset_index()
    g.columns = ["lens", "TRANSFERS (field)", "NO-ANALOG (facility)", "UNOBSERVED"]
    return md_table(g)


def t_task_attention() -> str:
    t = pd.read_parquet(DERIVED / "task_attention.parquet")
    s = pd.read_parquet(DERIVED / "sites.parquet")
    p = t.pivot(index="key", columns="context", values="n_pubs")
    s = s[s["query"].notna()].copy()
    s["anchor"] = [next(k for k in p.index if k in cells.split(",")) for cells in s["cells"]]
    out = pd.DataFrame({
        "site": s["name"], "any body (B8 query, site name)": s["attention_site_name"],
        "Moon context": s["anchor"].map(p["moon"]), "Mars context": s["anchor"].map(p["mars"]),
        "site Attention used for hidden_status": s["attention_n"],
        "hidden_status": s["hidden_status"]}).sort_values("site")
    q = t.iloc[0]
    return (md_table(out) + "\n\nContexts: Moon = `(analog OR analogue) AND (Moon OR lunar)`, "
            "Mars = `(analog OR analogue) AND (Mars OR Martian)`, on the same site-name query "
            f"(OpenAlex title/abstract search, {q['date']}). Supplementary: `hidden_status` is "
            "not recomputed from these counts.")



TABLES = {"verdicts": t_verdicts, "ledger": t_ledger, "terrain_controls": t_terrain_controls,
          "l1_robust": t_l1_robust, "relocations": t_relocations, "m1": t_m1, "x1": t_x1,
          "bridge": t_bridge, "scarcity": t_scarcity, "site_sensitivity": t_site_sensitivity,
          "multilens": t_multilens, "sites": t_sites,
          "mission_headline": t_mission_headline, "validity": t_validity,
          "mission_criteria": t_mission_criteria, "coverage": t_coverage,
          "task_attention": t_task_attention}


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
