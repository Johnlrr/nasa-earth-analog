"""PLAN 2d — validity summary and mission value, read from tables that already exist.

Nothing here changes a threshold or a verdict. All steps are post hoc (the results were known)
and are listed in the Deviations table of docs/validation_report.md.

mission_criteria : slope descriptors of the Moon targets, of the Earth cells the engine keeps for
                   Connecting Ridge and of the classic lunar-analog controls, set beside the
                   published Artemis III slope requirements (config/mission.yaml).
validity         : per lens, what the controls show for the CURRENT engine: random bare land
                   (null) passing the L1 robust test, classic controls, X1 controls and decoys,
                   M1 stop-rule checks; and a sanity check against known-analog zones.
coverage         : per lens, how many test variables TRANSFER / are NO-ANALOG / UNOBSERVED.
task_attention   : OpenAlex counts of the named sites with a Moon-only and a Mars-only context
                   (supplementary; hidden_status is NOT recomputed from it).
protocols        : docs/test_protocols.md, one test protocol per lens and showcase site.

Outputs: data/derived/mission_criteria.parquet, data/derived/mission_value.json,
         data/derived/task_attention.parquet, docs/test_protocols.md
Usage  : python scripts/mission_value.py [--no-attention]
"""

from __future__ import annotations

import argparse
import datetime as dt
import json
import sys
import time

import pandas as pd
from scipy import stats

from similitude import io

sys.path.insert(0, str(io.REPO_ROOT / "scripts" / "attention"))
import openalex  # noqa: E402

DERIVED = io.REPO_ROOT / "data" / "derived"
CFG = io.load_yaml(io.CONFIG_DIR / "mission.yaml")
SITES = io.load_yaml(io.CONFIG_DIR / "sites.yaml")
MOON_TARGET = "connecting_ridge"
# both are subsets of the B8 context "(analog OR analogue) AND (Mars OR Moon OR lunar OR planetary)"
TASK_CONTEXT = {"moon": "(analog OR analogue) AND (Moon OR lunar)",
                "mars": "(analog OR analogue) AND (Mars)"}
SCREEN_COLS = ["slope_p50_90m", "relief_90m", "frac_gt8_90m"]
STATE_ORDER = ["TRANSFERS", "NO-ANALOG", "UNOBSERVED"]


# ============================================================================================
# mission criteria
# ============================================================================================
def classic_controls(earth: pd.DataFrame) -> pd.DataFrame:
    """L1 control rows; where A14 relocated a control, the relocated row replaces the original."""
    c = earth[earth["cell_id"].str.startswith("CTRL_")].copy()
    relocated = {i[: -len("_reloc")] for i in c["cell_id"] if i.endswith("_reloc")}
    return c[~c["cell_id"].isin(relocated)]


def mission_criteria(targets: pd.DataFrame, earth: pd.DataFrame, kept_cells: list[str],
                     target: str = MOON_TARGET, names: dict | None = None) -> pd.DataFrame:
    """One row per site with the two slope shares NASA's Artemis III requirements are stated in.

    ``in_range_*``: the value lies inside the range spanned by the target's own footprints (the
    reference and its population), i.e. the site is as steep as the lunar target itself varies.
    """
    cols = ["slope_p50", "frac_gt8", "frac_gt20"]
    t = targets[targets["target_id"].eq(target)]
    lo, hi = t[cols].min(), t[cols].max()
    ref = t[t["is_reference"]].iloc[0]
    names = names or {}
    rows = [{"group": "Moon target", "id": target,
             "name": names.get(target, f"{target} (reference footprint)"),
             **{c: float(ref[c]) for c in cols}}]
    e = earth.drop_duplicates("cell_id").set_index("cell_id")
    for cid in kept_cells:
        rows.append({"group": "Engine match", "id": cid,
                     "name": names.get(cid, e.loc[cid, "name"]),
                     **{c: float(e.loc[cid, c]) for c in cols}})
    for r in classic_controls(earth).itertuples():
        rows.append({"group": "Classic analog", "id": r.cell_id, "name": r.name,
                     **{c: float(getattr(r, c)) for c in cols}})
    out = pd.DataFrame(rows)
    for c in ("frac_gt8", "frac_gt20"):
        out[f"in_range_{c}"] = out[c].between(lo[c], hi[c])
        out[f"range_lo_{c}"], out[f"range_hi_{c}"] = float(lo[c]), float(hi[c])
    out["n_target_footprints"] = len(t)
    # traverse length that meets as much > 8 deg terrain as 10 km on the target, assuming the
    # share along a path equals the areal share of the footprint
    out["km_for_10km_of_target"] = 10.0 * float(ref["frac_gt8"]) / out["frac_gt8"]
    return out


# ============================================================================================
# validity
# ============================================================================================
def _ci(k: int, n: int) -> tuple[float, float]:
    ci = stats.binomtest(k, n).proportion_ci(confidence_level=0.95, method="exact")
    return float(ci.low), float(ci.high)


def l1_null_rate(robust: pd.DataFrame) -> list[dict]:
    """Share of null (random bare-land) and of screened (rank) cells in the L1 robust set."""
    rows = []
    for target, g in robust.groupby("target_id"):
        row = {"target_id": target}
        for role in ("null", "rank", "control"):
            d = g[g["sample_role"].eq(role)]
            k, n = int(d["robust"].sum()), len(d)
            row |= {f"n_{role}": n, f"robust_{role}": k}
            if role == "null" and n:
                row["null_rate"] = k / n
                row["null_ci_lo"], row["null_ci_hi"] = _ci(k, n)
        rows.append(row)
    return rows


def rediscovery(tier1: pd.DataFrame, earth: pd.DataFrame, robust: pd.DataFrame,
                site_cells: pd.DataFrame | None = None) -> dict:
    """Sanity check: do the cells the terrain screen picks fall in known-analog zones?

    The screen saw only DEM slope and relief; config/exclusion_zones.yaml was never an input.
    Two base rates: all bare land, and the terrain-matched stratum (bare-land cells inside the
    5-95 % range of the screened cells on the coarse screen variables), because known-analog
    zones sit in steep, high, dry terrain. Cells cluster in space, so no p-value is given;
    ``sites`` counts single-linkage sites instead of cells.
    """
    zone = tier1["in_exclusion_buffer"].astype(bool)
    e = earth.drop_duplicates("cell_id")
    rank_ids = set(e.loc[e["sample_role"].eq("rank"), "cell_id"])
    rank = tier1[tier1["cell_id"].isin(rank_ids)]
    rank_zone = e.loc[e["sample_role"].eq("rank"), "in_exclusion_buffer"].astype(bool)
    out = {"base_in_zone": int(zone.sum()), "base_n": len(tier1),
           "base_rate": float(zone.mean()), "rank_in_zone": int(rank_zone.sum()),
           "rank_n": len(rank_zone), "rank_rate": float(rank_zone.mean()), "targets": []}
    out["rank_enrichment"] = out["rank_rate"] / out["base_rate"]
    cols = [c for c in SCREEN_COLS if c in tier1.columns]
    if cols and len(rank):
        m = pd.Series(True, index=tier1.index)
        for c in cols:
            m &= tier1[c].between(rank[c].quantile(0.05), rank[c].quantile(0.95))
        out |= {"matched_n": int(m.sum()), "matched_in_zone": int((m & zone).sum()),
                "matched_rate": float((m & zone).sum() / m.sum())}
        out["matched_enrichment"] = out["rank_rate"] / out["matched_rate"]
    r = robust[robust["sample_role"].eq("rank")].merge(
        e[["cell_id", "in_exclusion_buffer"]], on="cell_id")
    r["zone"] = r["in_exclusion_buffer"].astype(bool)
    site_of = {} if site_cells is None else dict(zip(site_cells["cell_id"],
                                                     site_cells["site_id"], strict=True))
    for target, g in r.groupby("target_id"):
        k = g[g["robust"]]
        sites = {site_of.get(c) for c in k["cell_id"]} - {None}
        zone_sites = {site_of.get(c) for c in k.loc[k["zone"], "cell_id"]} - {None}
        out["targets"].append({
            "target_id": target, "robust_in_zone": int(k["zone"].sum()), "robust_n": len(k),
            "other_in_zone": int((~g["robust"] & g["zone"]).sum()),
            "other_n": int((~g["robust"]).sum()),
            "sites": len(sites), "sites_with_zone_cell": len(zone_sites)})
    return out


def x1_controls(x1: pd.DataFrame) -> dict:
    """Controls, decoys and seeds of the current X1 checklist (B15)."""
    pos = x1[x1["sample_role"].eq("control")]
    dec = x1[x1["sample_role"].eq("decoy")]
    seed = x1[x1["sample_role"].eq("seed")]
    return {"positive_pass": sorted(pos[pos["passes_all"]]["cell_id"]),
            "positive_n": len(pos),
            "decoy_rejected": sorted(dec[~dec["passes_all"]]["cell_id"]), "decoy_n": len(dec),
            "seed_pass": {r.cell_id: bool(r.passes_all) for r in seed.itertuples()}}


def x1_mission(x1: pd.DataFrame, verdicts: pd.DataFrame, targets: pd.DataFrame) -> pd.DataFrame:
    """Modelled depth to ice-bearing ground of the X1 TRANSFERS cells and of the Mars references,
    beside the Mars Life Explorer numbers (land within 1 m of ice, drill to 2 m).

    Earth: Stefan thaw depth from ERA5-Land thawing degree-days (active_layer_m), taken as the
    depth to ice-bearing permafrost. Mars: ice_depth_ratio x 1 m (the descriptor's drill reach),
    from the sources in targets_X1. A reading of existing descriptors, not a measurement.
    """
    kept = set(verdicts[verdicts["lens_id"].eq("X1") & verdicts["state"].eq("TRANSFERS")
                        & verdicts["cell_id"].fillna("").ne("")]["cell_id"])
    e = x1[x1["cell_id"].isin(kept)]
    rows = [{"body": "Mars", "id": r.footprint_id, "depth_to_ice_m": float(r.ice_depth_ratio),
             "capped": bool(r.ice_depth_ratio >= 3.0), "source": r.source}
            for r in targets.itertuples()]
    rows += [{"body": "Earth", "id": r.cell_id, "depth_to_ice_m": float(r.active_layer_m),
              "capped": False, "source": f"lat {r.lat:.2f}, lon {r.lon:.2f}; qa {r.qa_flag}; "
                                         f"ice check {r.ice_check}"} for r in e.itertuples()]
    out = pd.DataFrame(rows)
    out["within_1m"] = out["depth_to_ice_m"] <= 1.0
    out["within_2m"] = out["depth_to_ice_m"] <= 2.0
    return out


def coverage(verdicts: pd.DataFrame) -> pd.DataFrame:
    """Per lens and test variable, one state: the test-transfer matrix (lens/target-level rows)."""
    v = verdicts[verdicts["cell_id"].fillna("").eq("")].copy()
    v["rank"] = v["state"].map({s: i for i, s in enumerate(STATE_ORDER)})
    v = v.sort_values("rank", kind="stable").drop_duplicates(["lens_id", "variable"])
    return v[["lens_id", "variable", "state", "facility"]].sort_values(
        ["lens_id", "state", "variable"]).reset_index(drop=True)


# ============================================================================================
# task attention (supplementary)
# ============================================================================================
def task_attention(enabled: bool) -> pd.DataFrame:
    """Cached counts; new queries only when ``enabled``. The caller writes the table."""
    path = DERIVED / "task_attention.parquet"
    old = pd.read_parquet(path) if path.exists() else pd.DataFrame(
        columns=["key", "context", "name", "query", "n_pubs", "source", "date"])
    cache = {(r.key, r.context): r for r in old.itertuples() if pd.notna(r.n_pubs)}
    rows, today = [], dt.date.today().isoformat()
    for s in SITES["sites"]:
        for ctx, text in TASK_CONTEXT.items():
            q = f"({s['query']}) AND {text}"
            hit = cache.get((s["anchor"], ctx))
            if hit is not None and hit.query == q:
                rows.append(hit._asdict() | {"Index": None})
                continue
            if not enabled:
                continue
            try:
                n = openalex.count(q)
            except openalex.BudgetExhausted as exc:
                print(f"OpenAlex budget exhausted: {str(exc)[:80]}")
                enabled = False
                continue
            if n is not None:
                rows.append({"key": s["anchor"], "context": ctx, "name": s["name"], "query": q,
                             "n_pubs": n, "source": "OpenAlex", "date": today})
            time.sleep(1.1)
    out = pd.DataFrame(rows).drop(columns="Index", errors="ignore")
    if len(out):
        out["n_pubs"] = out["n_pubs"].astype("Int64")
    return out


# ============================================================================================
# protocols
# ============================================================================================
def shortfall_names() -> dict:
    out = {}
    for body in ("moon", "mars"):
        for g in io.load_yaml(io.REPO_ROOT / "ledger" / f"{body}.yaml").get("nasa_gaps", []):
            out[g["id"]] = (g["name"], g["source"])
    return out


def _robustness_lines(cell_id: str) -> list[str]:
    """PLAN 2e readings for one kept cell, when those tables exist (never a verdict)."""
    out = []
    p = DERIVED / "cross_dem.parquet"
    if p.exists():
        c = pd.read_parquet(p)
        c = c[c["cell_id"].eq(cell_id) & c["target_id"].eq(MOON_TARGET) & c["alt_ok"]]
        if len(c):
            r = c.iloc[0]
            out.append(f"- **Second DEM ({r['alt_source']}), cell {cell_id}:** "
                       + ("stays in" if r["robust"] else "**leaves**")
                       + f" the robust set (native rank {int(r['nr_i'])}/{int(r['nr_ii'])}/"
                       f"{int(r['nr_iii'])} of {int(r['n_i'])}; the rule needs "
                       f"{r['n_i'] / 2:g})" + ("" if r["robust"] else
                                              ": the terrain verdict here is marginal") + ".")
    p = DERIVED / "l1_regions.parquet"
    if p.exists():
        g = pd.read_parquet(p)
        g = g[g["cell_id"].eq(cell_id) & g["robust"]]
        if len(g):
            out.append(f"- **PGDA 78 south-pole sites matched by cell {cell_id} (exploratory "
                       f"beyond the two published targets):** {len(g)} of 6 — "
                       + ", ".join(sorted(x.replace("_", " ") for x in g["target_id"])) + ".")
    return out


def render_protocols(cards: list[dict], crit: pd.DataFrame, cov: pd.DataFrame,
                     generated: str, x1m: pd.DataFrame | None = None) -> str:
    req, gaps = CFG["requirements"], shortfall_names()
    counts = cov.groupby(["lens_id", "state"]).size().unstack(fill_value=0)
    out = ["# Test protocols for the showcase sites (PLAN 2d)", "",
           f"Generated {generated} by `scripts/mission_value.py` from `verdicts.parquet`, "
           "`field_facility.json`, `mission_criteria.parquet` and `config/mission.yaml`. "
           "Post hoc presentation layer: no threshold or verdict changed.", "",
           "## What a card is, in NASA's terms", "",
           "NASA's TRL definitions make a *\"Documented definition of relevant environment\"* "
           "an exit criterion of TRL 4, before *\"" + req["trl_relevant_environment"]["quote"]
           + f"\"* at TRL 5 ([source]({req['trl_relevant_environment']['source']})). That "
           "definition belongs to the technology project and its own system. A SIMILITUDE card "
           "is an **input** to it: for one site it says, per test variable, whether the site "
           "reproduces the target by a stated, reproducible measure (**Field**), whether no "
           "Earth site does and which facility is used instead (**Facility**), or that this "
           "engine cannot judge (**Unobserved**). It does not assign or certify a TRL, and no "
           "hardware was tested here.", "",
           "## Published requirements used", ""]
    for k, r in req.items():
        out.append(f"- **{k}** — \"{r['quote']}\". {r['document']} ([source]({r['source']})).")
    out += ["", "## Protocol per lens", ""]
    for lens, p in CFG["protocols"].items():
        c = counts.loc[lens] if lens in counts.index else {}
        n = {s: int(c.get(s, 0)) for s in STATE_ORDER}
        out += [f"### {lens} — {p['name']}", "",
                f"- **Systems under test:** {p['systems']}",
                "- **Requirement it rehearses:** " + ("; ".join(
                    f"\"{req[r]['quote']}\"" for r in p["requirement"]) or "—"),
                "- **NASA shortfalls addressed (ledger):** " + ("; ".join(
                    f"{g} {gaps[g][0]}" if g in gaps else g for g in p["shortfalls"]) or "—"),
                f"- **Reproduced at a TRANSFERS site:** {p['field_credit']}",
                f"- **Measure:** {p['measure']}",
                f"- **Not reproduced (facility or unobserved):** {p['not_credited']}",
                "- **Test-matrix coverage:** " + (
                    "— (stop rule FAIL: no site is published for this lens)"
                    if not p["requirement"] else
                    f"{n['TRANSFERS']} variable(s) transfer, {n['NO-ANALOG']} are not "
                    f"reproduced on Earth, {n['UNOBSERVED']} unobserved (of {sum(n.values())}; "
                    "best state over the lens' targets"
                    + (f"; {p['coverage_note']}" if p.get("coverage_note") else "") + ")")]
        if lens == "X1" and x1m is not None:
            e = x1m[x1m["body"].eq("Earth")]
            out.append(f"- **Mars Life Explorer reading:** of the {len(e)} cells kept, "
                       f"{int(e['within_1m'].sum())} have modelled ice-bearing ground within "
                       f"1 m and {int(e['within_2m'].sum())} within the 2 m drill reach "
                       "(Stefan thaw depth from reanalysis; not observed in situ).")
        out.append("")
    out += ["## Protocol per showcase site", ""]
    kept = crit[crit["group"].eq("Engine match")].set_index("id")
    ref = crit[crit["group"].eq("Moon target")].iloc[0]
    for c in cards:
        lenses = [x for x in (c["lenses_engine_confirmed"] + ","
                              + c["lenses_engine_semiquant"]).split(",") if x]
        out += [f"### {c['name']}", "",
                f"Evidence: engine-confirmed **{c['lenses_engine_confirmed'] or '—'}**"
                + (f", engine-semiquant **{c['lenses_engine_semiquant']}**"
                   if c["lenses_engine_semiquant"] else "")
                + f" · {c['n_cells']} cell(s), span {c['max_span_km']:.0f} km · showcase rule "
                f"{c['showcase']}", ""]
        for lens in lenses:
            p = CFG["protocols"][lens]
            out.append(f"- **{lens} {p['name']}.** Test: {p['systems']}. Measure: "
                       f"{p['measure']}. Not reproduced here: {p['not_credited']}.")
        for cid in [x for x in c["cells"].split(",") if x in kept.index]:
            k = kept.loc[cid]
            out.append(f"- **Artemis III slope reading, cell {cid}:** {k['frac_gt8']:.0%} of the "
                       f"footprint is steeper than 8° (Connecting Ridge reference "
                       f"{ref['frac_gt8']:.0%}), {k['frac_gt20']:.1%} is steeper than 20° "
                       f"(reference {ref['frac_gt20']:.1%}). Inside this 4 km footprint a "
                       f"traverse of about {k['km_for_10km_of_target']:.0f} km meets as much "
                       f"terrain steeper than 8° as 10 km on the target (if the share along "
                       f"the path equals the areal share; the neighbouring footprints differ). "
                       f"{CFG['criteria_caveat']}")
        for cid in [x for x in c["cells"].split(",") if x in kept.index]:
            out += _robustness_lines(cid)
        n_fac = len(c["facility"])
        out += [f"- **Facility rows to close elsewhere:** {n_fac} (see `docs/field_facility.md`, "
                "same site).", ""]
    return "\n".join(out) + "\n"


# ============================================================================================
def build(attention_enabled: bool = False) -> dict:
    targets = pd.read_parquet(DERIVED / "targets_L1.parquet")
    earth = pd.read_parquet(DERIVED / "earth_L1.parquet")
    robust = pd.read_parquet(DERIVED / "l1_robust_set.parquet")
    tier1 = pd.read_parquet(DERIVED / "tier1_terrain.parquet",
                            columns=["cell_id", "in_exclusion_buffer", *SCREEN_COLS])
    site_cells = pd.read_parquet(DERIVED / "site_cells.parquet").dropna(subset=["site_id"])
    verdicts = pd.read_parquet(DERIVED / "verdicts.parquet")
    scarcity = pd.read_parquet(DERIVED / "target_scarcity.parquet")
    kept = scarcity[scarcity["lens_id"].eq("L1") & scarcity["target_id"].eq(MOON_TARGET)]
    kept = [c for c in kept["usable_cells"].iloc[0].split(",") if c]
    sites = pd.read_parquet(DERIVED / "sites.parquet")
    names = {c: s.name for s in sites.itertuples() for c in s.cells.split(",")}
    names[MOON_TARGET] = SITES["target_labels"][MOON_TARGET]
    crit = mission_criteria(targets, earth, kept, names=names)
    cov = coverage(verdicts)
    x1m = x1_mission(pd.read_parquet(DERIVED / "x1_checklist.parquet"), verdicts,
                     pd.read_parquet(DERIVED / "targets_X1.parquet"))
    x1e = x1m[x1m["body"].eq("Earth")]
    classic = crit[crit["group"].eq("Classic analog")]
    ref = crit[crit["group"].eq("Moon target")].iloc[0]
    ctrl = robust[robust["cell_id"].isin(classic["id"]) & robust["target_id"].eq(MOON_TARGET)]
    m1 = json.loads((DERIVED / "m1_stop_rule.json").read_text(encoding="utf-8"))
    value = {
        "l1_null": [r | {"bare_land_cells": len(tier1),
                         "extrapolated_cells": round(r["null_rate"] * len(tier1)),
                         "extrapolated_lo": round(r["null_ci_lo"] * len(tier1)),
                         "extrapolated_hi": round(r["null_ci_hi"] * len(tier1))}
                    for r in l1_null_rate(robust)],
        "l1_classic_controls": {"n": len(classic), "n_scored": int(ctrl["cell_id"].nunique()),
                                "robust": int(ctrl["robust"].sum()),
                                "in_range_frac_gt20": int(classic["in_range_frac_gt20"].sum()),
                                "in_range_frac_gt8": int(classic["in_range_frac_gt8"].sum()),
                                "frac_gt8_max": float(classic["frac_gt8"].max()),
                                "frac_gt8_median": float(classic["frac_gt8"].median())},
        "l1_reference": {c: float(ref[c]) for c in ("slope_p50", "frac_gt8", "frac_gt20")},
        "l1_under_sampling": float(ref["frac_gt8"] / classic["frac_gt8"].median()),
        "rediscovery": rediscovery(tier1, earth, robust, site_cells),
        "x1_controls": x1_controls(pd.read_parquet(DERIVED / "x1_checklist.parquet")),
        "x1_mission": {"cells": len(x1e), "within_1m": int(x1e["within_1m"].sum()),
                       "within_2m": int(x1e["within_2m"].sum()),
                       "depth_max_m": float(x1e["depth_to_ice_m"].max())},
        "m1_checks": {"passed": int(sum(bool(x) for x in m1["checks"].values())),
                      "n": len(m1["checks"]), "verdict": m1["verdict"]},
        "coverage": {lens: {s: int((g["state"] == s).sum()) for s in STATE_ORDER}
                     for lens, g in cov.groupby("lens_id")},
        "funnel": {"bare_land_cells": len(tier1),
                   "screened": int(robust[robust["target_id"].eq(MOON_TARGET)
                                          & robust["sample_role"].eq("rank")].shape[0]),
                   "robust_rank_seed": int(scarcity[scarcity["lens_id"].eq("L1")
                                                    & scarcity["target_id"].eq(MOON_TARGET)]
                                           ["n_transfers"].iloc[0]),
                   "usable": len(kept)},
    }
    return {"criteria": crit, "coverage": cov, "value": value, "x1_mission": x1m,
            "task_attention": task_attention(attention_enabled)}


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--no-attention", action="store_true")
    args = ap.parse_args()
    b = build(attention_enabled=not args.no_attention)
    b["criteria"].to_parquet(DERIVED / "mission_criteria.parquet", index=False)
    b["x1_mission"].to_parquet(DERIVED / "x1_mission.parquet", index=False)
    if len(b["task_attention"]):
        b["task_attention"].to_parquet(DERIVED / "task_attention.parquet", index=False)
    generated = dt.datetime.now().strftime("%Y-%m-%d %H:%M")
    (DERIVED / "mission_value.json").write_text(
        json.dumps({"generated": generated, **b["value"]}, indent=1), encoding="utf-8")
    cards = json.loads((DERIVED / "field_facility.json").read_text(encoding="utf-8"))["sites"]
    (io.REPO_ROOT / "docs" / "test_protocols.md").write_text(
        render_protocols(cards, b["criteria"], b["coverage"], generated, b["x1_mission"]),
        encoding="utf-8")
    print(b["criteria"][["group", "id", "slope_p50", "frac_gt8", "frac_gt20",
                         "in_range_frac_gt8", "in_range_frac_gt20"]].to_string(index=False))
    print(json.dumps(b["value"], indent=1)[:2500])
    if len(b["task_attention"]):
        print(b["task_attention"].pivot(index="name", columns="context", values="n_pubs"))


if __name__ == "__main__":
    main()
