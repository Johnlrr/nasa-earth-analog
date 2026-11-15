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
    met = vc.dropna(subset=["expectation_met"]) if "expectation_met" in vc else vc.iloc[:0]
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


TABLES = {"verdicts": t_verdicts, "ledger": t_ledger, "terrain_controls": t_terrain_controls,
          "l1_robust": t_l1_robust, "relocations": t_relocations, "m1": t_m1, "x1": t_x1,
          "bridge": t_bridge, "scarcity": t_scarcity, "site_sensitivity": t_site_sensitivity,
          "multilens": t_multilens, "sites": t_sites}


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
