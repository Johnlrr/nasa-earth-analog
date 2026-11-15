"""PLAN 2e — L1 checked against known truth, and read for all six PGDA 78 regions.

Uses the unchanged robust-set rule of A12 (native rank >= n/2 under three configurations) and
reproduces l1_robust_set.parquet exactly for the two published targets before anything else.

nasa_slope_check : our slope formula at 5 m against NASA's own PGDA 78 slope rasters, and the
                   same shares at 30 m (how much the 8 deg / 20 deg shares depend on baseline).
lunar_control    : leave-one-out on the Moon. Every population footprint is scored as if it
                   were an Earth cell against each region's reference; does the test recognise
                   footprints of the same region and reject the others?
regions          : the scored Earth cells against all six regions (the four regions without a
                   published reference use their medoid population footprint). Exploratory:
                   these rows are NOT verdicts and never enter verdicts.parquet.
prevalence       : pass rate of random bare land (200 pre-registered null cells + 800 more drawn
                   by the same rule, scripts/null_expand.py) for each region.

All post hoc (Deviations 28). Outputs: data/derived/l1_regions.json, l1_lunar_control.parquet,
l1_regions.parquet, l1_prevalence.parquet, nasa_slope_check.parquet
Usage: python scripts/l1_regions.py
"""

from __future__ import annotations

import json
import sys

import numpy as np
import pandas as pd
from scipy import stats

from similitude import io
from similitude.fidelity import (
    _min_scale,
    fit_population,
    mahalanobis_d,
    native_population,
    native_rank,
)

sys.path.insert(0, str(io.REPO_ROOT / "scripts"))
import l1_robust as a12  # noqa: E402
from run_all import load  # noqa: E402

DERIVED = io.REPO_ROOT / "data" / "derived"
PUBLISHED = ["connecting_ridge", "shackleton_rim"]
META = ["footprint_id", "target_id", "is_reference", "lat", "lon", "body", "footprint_m"]


# ============================================================================================
def context() -> dict:
    lens = io.load_lenses()["L1"]
    names = lens["descriptors"]
    earth, targets = load("L1")
    e60 = pd.read_parquet(a12.EARTH_L60)
    t60 = targets[META].merge(pd.read_parquet(a12.TARGETS_L60), on="footprint_id", how="inner")
    pop_ids = set(targets[~targets["is_reference"].astype(bool)]["footprint_id"])
    ctx = {"lens": lens, "names": names, "targets": targets, "targets60": t60, "earth": earth,
           "earth60": earth[["cell_id"]].merge(e60, on="cell_id", how="left"),
           "pop_ids": pop_ids,
           "cfg": {"i": ("targets", names, "diag"), "ii": ("targets", a12.SUBSET_II, "auto"),
                   "iii": ("targets60", names, "diag")}}
    ctx["refs"] = region_refs(ctx)
    return ctx


def region_refs(ctx: dict) -> dict:
    """Reference footprint per region: the published one, else the region's medoid footprint
    (smallest median distance to its sibling footprints, configuration (i))."""
    t, lens, names = ctx["targets"], ctx["lens"], ctx["names"]
    pop = t[t["footprint_id"].isin(ctx["pop_ids"])]
    refs = {}
    for site in sorted(t["target_id"].unique()):
        ref = t[t["target_id"].eq(site) & t["is_reference"].astype(bool)]
        if len(ref):
            refs[site] = ref["footprint_id"].iloc[0]
            continue
        sib = pop[pop["target_id"].eq(site)]
        best = (np.inf, None)
        for _, r in sib.iterrows():
            ms = np.array([_min_scale(lens, n, r[n]) for n in names])
            m = fit_population(pop[pop["footprint_id"].ne(r["footprint_id"])][names].to_numpy(
                float), ms, mode="diag")
            others = sib[sib["footprint_id"].ne(r["footprint_id"])][names].to_numpy(float)
            d = float(np.median(mahalanobis_d(others, r[names].to_numpy(float), m)))
            best = min(best, (d, r["footprint_id"]))
        refs[site] = best[1]
    return refs


def _rank(ctx: dict, ref_id: str, cfg: str, cand: pd.DataFrame,
          loo_ids: np.ndarray | None = None) -> tuple[np.ndarray, int]:
    """Native rank of candidate rows against one reference under one configuration.

    ``loo_ids``: candidates are themselves population footprints; each is removed from the
    native population before it is ranked (leave-one-out).
    """
    table, names, mode = ctx["cfg"][cfg]
    tt = ctx[table]
    t = tt[tt["footprint_id"].eq(ref_id)].iloc[0]
    pop = tt[tt["footprint_id"].isin(ctx["pop_ids"]) & tt["footprint_id"].ne(ref_id)]
    tv = t[names].to_numpy(float)
    ms = np.array([_min_scale(ctx["lens"], n, t[n]) for n in names])
    m = fit_population(pop[names].to_numpy(float), ms, mode=mode)
    nat = native_population(pop, t)
    d_nat = mahalanobis_d(nat[names].to_numpy(float), tv, m)
    d = mahalanobis_d(cand[names].to_numpy(float), tv, m)
    if loo_ids is None:
        return native_rank(d, d_nat), len(nat)
    nat_ids = nat["footprint_id"].to_numpy()
    nr = [native_rank(np.array([dc]), d_nat[nat_ids != cid])[0]
          for cid, dc in zip(loo_ids, d, strict=True)]
    return np.array(nr), len(nat) - 1


def score_cells(ctx: dict, e30: pd.DataFrame, e60: pd.DataFrame,
                regions: list[str] | None = None) -> pd.DataFrame:
    """Robust-set membership of Earth cells (rows of e30 / e60, same cell_id order not needed)."""
    e60 = e30[["cell_id"]].merge(e60, on="cell_id", how="left")
    out = []
    for site in regions or list(ctx["refs"]):
        row = {"cell_id": e30["cell_id"].to_numpy(), "target_id": site}
        ok = np.ones(len(e30), bool)
        for k in ctx["cfg"]:
            nr, n = _rank(ctx, ctx["refs"][site], k, e60 if k == "iii" else e30)
            row[f"nr_{k}"], row[f"n_{k}"] = nr, n
            row[f"in_{k}"] = nr >= n / 2
            ok &= row[f"in_{k}"]
        row["robust"] = ok
        out.append(pd.DataFrame(row))
    return pd.concat(out, ignore_index=True)


def lunar_control(ctx: dict) -> pd.DataFrame:
    """Leave-one-out on the Moon: population footprints scored against every region."""
    t = ctx["targets"]
    rows = []
    for site, ref_id in ctx["refs"].items():
        ref = t[t["footprint_id"].eq(ref_id)].iloc[0]
        cand = native_population(
            t[t["footprint_id"].isin(ctx["pop_ids"]) & t["footprint_id"].ne(ref_id)], ref)
        ok = np.ones(len(cand), bool)
        for k, (table, _, _) in ctx["cfg"].items():
            ct = ctx[table].set_index("footprint_id").loc[cand["footprint_id"]].reset_index()
            nr, n = _rank(ctx, ref_id, k, ct, loo_ids=cand["footprint_id"].to_numpy())
            ok &= nr >= n / 2
        g = pd.DataFrame({"candidate_region": cand["target_id"].to_numpy(), "ok": ok})
        for region, d in g.groupby("candidate_region"):
            rows.append({"reference_region": site, "candidate_region": region,
                         "n": len(d), "n_pass": int(d["ok"].sum())})
    return pd.DataFrame(rows)


def nasa_slope_check() -> pd.DataFrame | None:
    """Our slope statistics at 5 m against NASA's PGDA 78 slope raster, central 4 km footprint."""
    import rasterio
    from targets import moon_terrain as mt

    from similitude.descriptors import terrain as T

    rows = []
    for code, name in mt.SITES.items():
        dem_path = mt.DATA_RAW / f"{code}_final_adj_5mpp_surf.tif"
        slp_path = mt.DATA_RAW / f"{code}_final_adj_5mpp_slp.tif"
        if not (dem_path.exists() and slp_path.exists()):
            return None
        with rasterio.open(dem_path) as ds:
            dem = ds.read(1).astype(float)
        with rasterio.open(slp_path) as ds:
            slp = ds.read(1).astype(float)
        c, h = dem.shape[0] // 2, int(round(mt.FOOTPRINT_M / 5.0 / 2))
        d, s = dem[c - h:c + h, c - h:c + h], slp[c - h:c + h, c - h:c + h]
        ours = T.slope_stats(d, 5.0)
        at30 = T.slope_stats(T.aggregate_to_baseline(d, 5.0, 30.0), 30.0)
        rows.append({
            "region": name, "pgda_site": code,
            "slope_p50_ours_5m": float(ours["slope_p50"]), "slope_p50_nasa": float(np.nanmedian(s)),
            "frac_gt8_ours_5m": float(ours["frac_gt8"]), "frac_gt8_nasa": float(np.nanmean(s > 8)),
            "frac_gt20_ours_5m": float(ours["frac_gt20"]),
            "frac_gt20_nasa": float(np.nanmean(s > 20)),
            "frac_gt8_ours_30m": float(at30["frac_gt8"]),
            "frac_gt20_ours_30m": float(at30["frac_gt20"])})
    return pd.DataFrame(rows)


def _ci(k: int, n: int) -> tuple[float, float]:
    ci = stats.binomtest(k, n).proportion_ci(confidence_level=0.95, method="exact")
    return float(ci.low), float(ci.high)


def prevalence(ctx: dict, scored: pd.DataFrame, null2: pd.DataFrame | None,
               bare_land_cells: int) -> pd.DataFrame:
    """Pass rate of random bare land per region: pre-registered null, extension, combined.

    The random cells were drawn from bare land minus the screened (rank) cells, so the estimate
    is stratified: passing cells known in the screened stratum + rate x the unscreened rest.
    """
    role = ctx["earth"].set_index("cell_id")["sample_role"]
    n1 = scored[scored["cell_id"].map(role).eq("null")]
    rank = scored[scored["cell_id"].map(role).eq("rank")]
    unscreened = bare_land_cells - int(rank["cell_id"].nunique())
    rows = []
    for site in ctx["refs"]:
        a = n1[n1["target_id"].eq(site)]
        k1, m1 = int(a["robust"].sum()), len(a)
        k2 = m2 = 0
        if null2 is not None:
            b = null2[null2["target_id"].eq(site)]
            k2, m2 = int(b["robust"].sum()), len(b)
        lo, hi = _ci(k1 + k2, m1 + m2)
        known = int(rank[rank["target_id"].eq(site)]["robust"].sum())
        rows.append({"target_id": site, "published": site in PUBLISHED,
                     "screened_pass": known, "unscreened_cells": unscreened,
                     "null_pass": k1, "null_n": m1, "null2_pass": k2, "null2_n": m2,
                     "pass": k1 + k2, "n": m1 + m2, "rate": (k1 + k2) / (m1 + m2),
                     "ci_lo": lo, "ci_hi": hi,
                     "cells": known + round((k1 + k2) / (m1 + m2) * unscreened),
                     "cells_lo": known + round(lo * unscreened),
                     "cells_hi": known + round(hi * unscreened)})
    return pd.DataFrame(rows)


def build() -> dict:
    ctx = context()
    scored = score_cells(ctx, ctx["earth"], ctx["earth60"])
    old = pd.read_parquet(DERIVED / "l1_robust_set.parquet")
    for site in PUBLISHED:  # the generalised code must reproduce the published sets exactly
        a = set(old[old["target_id"].eq(site) & old["robust"]]["cell_id"])
        b = set(scored[scored["target_id"].eq(site) & scored["robust"]]["cell_id"])
        if a != b:
            raise SystemExit(f"robust set of {site} not reproduced")
    info = ctx["earth"][["cell_id", "lat", "lon", "sample_role", "in_exclusion_buffer"]]
    scored = scored.merge(info, on="cell_id")
    null2 = None
    p30, p60 = DERIVED / "earth_L1_null2.parquet", DERIVED / "earth_L1_null2_L60.parquet"
    if p30.exists() and p60.exists():
        e30 = pd.read_parquet(p30)
        e30 = e30[e30["qa_flag"].eq("ok")].reset_index(drop=True)
        null2 = score_cells(ctx, e30, pd.read_parquet(p60)).merge(
            e30[["cell_id", "lat", "lon", "sample_role", "in_exclusion_buffer"]], on="cell_id")
    bare = len(pd.read_parquet(DERIVED / "tier1_terrain.parquet", columns=["cell_id"]))
    prev = prevalence(ctx, scored, null2, bare)
    ctrl = lunar_control(ctx)
    same = ctrl[ctrl["reference_region"].eq(ctrl["candidate_region"])]
    other = ctrl[ctrl["reference_region"].ne(ctrl["candidate_region"])]
    cand = scored[scored["sample_role"].isin(["rank", "seed"])]
    wall = "shackleton_rim"
    nw_same, nw_other = (d[d["reference_region"].ne(wall)] for d in (same, other))
    summary = {
        "refs": ctx["refs"],
        "lunar_control": {"same_pass": int(same["n_pass"].sum()), "same_n": int(same["n"].sum()),
                          "other_pass": int(other["n_pass"].sum()),
                          "other_n": int(other["n"].sum()),
                          "all_pass": int(ctrl["n_pass"].sum()), "all_n": int(ctrl["n"].sum()),
                          "no_wall_same_pass": int(nw_same["n_pass"].sum()),
                          "no_wall_same_n": int(nw_same["n"].sum()),
                          "no_wall_other_pass": int(nw_other["n_pass"].sum()),
                          "no_wall_other_n": int(nw_other["n"].sum())},
        "regions_rank_seed_robust": {s: int(d["robust"].sum())
                                     for s, d in cand.groupby("target_id")},
        "prevalence": prev.to_dict("records"),
    }
    # the two rates are measured on the same random cells: exact McNemar on discordant cells
    allc = pd.concat([scored, null2], ignore_index=True) if null2 is not None else scored
    rnd = allc[allc["sample_role"].isin(["null", "null2"]) & allc["target_id"].isin(PUBLISHED)]
    pv = rnd.pivot(index="cell_id", columns="target_id", values="robust")
    if pv.isna().any().any():
        raise SystemExit("a random cell lacks a verdict for one of the published targets")
    pv = pv.astype(bool)
    b = int((pv["connecting_ridge"] & ~pv[wall]).sum())
    c = int((~pv["connecting_ridge"] & pv[wall]).sum())
    summary["ridge_vs_wall"] = {
        "ridge_only": b, "wall_only": c, "both": int((pv["connecting_ridge"] & pv[wall]).sum()),
        "p_mcnemar_exact": float(stats.binomtest(min(b, c), b + c, 0.5).pvalue) if b + c else 1.0}
    return {"scored": pd.concat([scored, null2], ignore_index=True) if null2 is not None
            else scored, "control": ctrl, "prevalence": prev, "summary": summary}


def main() -> None:
    b = build()
    b["control"].to_parquet(DERIVED / "l1_lunar_control.parquet", index=False)
    b["scored"].to_parquet(DERIVED / "l1_regions.parquet", index=False)
    b["prevalence"].to_parquet(DERIVED / "l1_prevalence.parquet", index=False)
    chk = nasa_slope_check()
    if chk is not None:
        chk.to_parquet(DERIVED / "nasa_slope_check.parquet", index=False)
        b["summary"]["nasa_slope_max_abs_diff_deg"] = float(
            (chk["slope_p50_ours_5m"] - chk["slope_p50_nasa"]).abs().max())
        b["summary"]["nasa_frac_max_abs_diff"] = float(max(
            (chk["frac_gt8_ours_5m"] - chk["frac_gt8_nasa"]).abs().max(),
            (chk["frac_gt20_ours_5m"] - chk["frac_gt20_nasa"]).abs().max()))
    (DERIVED / "l1_regions.json").write_text(json.dumps(b["summary"], indent=1),
                                             encoding="utf-8")
    c = b["control"].assign(txt=lambda d: d["n_pass"].astype(str) + "/" + d["n"].astype(str))
    print(c.pivot(index="reference_region", columns="candidate_region", values="txt"))
    print(b["prevalence"].round(4).to_string(index=False))
    print(json.dumps({k: v for k, v in b["summary"].items() if k != "prevalence"}, indent=1))


if __name__ == "__main__":
    main()
