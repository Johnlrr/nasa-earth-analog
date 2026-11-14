"""PLAN 2c (A17-A20) — present engine findings as field sites, not 4 km cells.

Nothing here changes a threshold or a verdict: every table is a regrouping of
``verdicts.parquet`` (A15) and ``cell_profiles.parquet`` (A13). All steps are post hoc
(the cell distribution was seen first) and are listed in the A9b Deviations table.

A17 sites       : single-linkage clusters of A13 cells at CLUSTER_KM (one field campaign's
                  driving range); site_id = "site:<smallest cell_id>"; names from
                  config/sites.yaml; Attention by site name (same B8 context), max with member
                  cells; ice-excluded cells are not members.
A18 scarcity    : per lens x target, how many TRANSFERS cells survive the ice filter, how many
                  lie outside known-analog exclusion buffers, in how many sites.
A19 multi-lens  : A13 cells within CLUSTER_KM of an X1 TRANSFERS cell or an M1 seed; the other
                  lens' state is read from verdicts.parquet (no cell-level TRANSFERS ->
                  literature-only, never engine-confirmed).
A20 field/facility cards for showcase sites, chosen by rule:
                  (a) holds a Connecting Ridge TRANSFERS cell whose ice is not excluded and
                      which B10 did not downgrade;
                  (b) has a multi-lens partner; (c) largest site with no cell in an exclusion
                  buffer.

Outputs: data/derived/{sites,site_cells,target_scarcity,multilens}.parquet,
         data/derived/field_facility.json, docs/field_facility.md
Usage  : python scripts/sites.py [--no-attention]
"""

from __future__ import annotations

import argparse
import datetime as dt
import json
import sys
import time

import numpy as np
import pandas as pd

from similitude import io

sys.path.insert(0, str(io.REPO_ROOT / "scripts" / "attention"))
import openalex  # noqa: E402

DERIVED = io.REPO_ROOT / "data" / "derived"
CFG = io.load_yaml(io.CONFIG_DIR / "sites.yaml")
CLUSTER_KM = float(CFG["cluster_km"])
MULTILENS_KM = float(CFG["multilens_km"])
SPAN_WARN_KM = float(CFG["span_warn_km"])
TARGET_LABELS = CFG["target_labels"]
LEDGER_OF = {"L1": "moon", "L2": "moon", "M1": "mars", "X1": "mars"}
#: lenses whose best evidence is engine-semiquant, never engine-confirmed (B6, B16)
SEMIQUANT_LENSES = {"X1"}
EDGE_FRAC = 0.9  # a partner beyond 90 % of the radius is reported as "edge of radius"
LENS_NAMES = {"L1": "Touchdown & Traverse", "L2": "Low-Sun Navigation",
              "X1": "Ice under Dry Overburden", "M1": "Aqueous Minerals"}


# ============================================================================================
# A17 sites
# ============================================================================================
def haversine_km(lat1, lon1, lat2, lon2):
    a1, o1, a2, o2 = map(np.radians, (lat1, lon1, lat2, lon2))
    h = np.sin((a2 - a1) / 2) ** 2 + np.cos(a1) * np.cos(a2) * np.sin((o2 - o1) / 2) ** 2
    return 2 * 6371.0 * np.arcsin(np.sqrt(np.clip(h, 0, 1)))


def cluster_cells(cells: pd.DataFrame, km: float = CLUSTER_KM) -> pd.Series:
    """Single-linkage clusters (connected components of the 'within km' graph) -> site_id."""
    lat, lon = cells["lat"].to_numpy(), cells["lon"].to_numpy()
    n = len(cells)
    d = haversine_km(lat[:, None], lon[:, None], lat[None, :], lon[None, :])
    parent = list(range(n))

    def find(i):
        while parent[i] != i:
            parent[i] = parent[parent[i]]
            i = parent[i]
        return i

    for i, j in zip(*np.nonzero(np.triu(d <= km, k=1)), strict=True):
        parent[find(i)] = find(j)
    roots = [find(i) for i in range(n)]
    ids = cells["cell_id"].astype(str).to_numpy()
    first = {}
    for r, cid in zip(roots, ids, strict=True):
        first[r] = min(first.get(r, cid), cid)
    return pd.Series([f"site:{first[r]}" for r in roots], index=cells.index, name="site_id")


def name_sites(site_cells: pd.DataFrame, cfg: list[dict]) -> pd.DataFrame:
    """site_id -> name, query, name_source; manual entry wins, else first cell's geocoded place."""
    anchors = {e["anchor"]: e for e in cfg}
    rows = []
    for sid, g in site_cells.groupby("site_id"):
        hit = [anchors[c] for c in g["cell_id"] if c in anchors]
        if len(hit) > 1:
            raise ValueError(f"{sid}: several name anchors {[h['anchor'] for h in hit]}")
        if hit:
            rows.append({"site_id": sid, "name": hit[0]["name"], "query": hit[0]["query"],
                         "name_source": "manual"})
        else:
            first = g.sort_values("cell_id").iloc[0]
            rows.append({"site_id": sid, "name": first["name"], "query": None,
                         "name_source": "reverse-geocode"})
    return pd.DataFrame(rows)


def summarise_sites(site_cells: pd.DataFrame) -> pd.DataFrame:
    def split_union(s):
        return ",".join(sorted({x for v in s for x in str(v).split(",") if x}))

    def span(d):
        if len(d) < 2:
            return 0.0
        lat, lon = d["lat"].to_numpy(), d["lon"].to_numpy()
        return float(haversine_km(lat[:, None], lon[:, None], lat[None, :], lon[None, :]).max())

    g = site_cells.groupby("site_id")
    return pd.DataFrame({
        "lat": g["lat"].mean(), "lon": g["lon"].mean(), "n_cells": g.size(),
        "max_span_km": g[["lat", "lon"]].apply(span).round(0),
        "cells": g["cell_id"].agg(lambda s: ",".join(sorted(s))),
        "lenses": g["lenses"].agg(split_union), "targets": g["targets"].agg(split_union),
        "n_ice_ok": g["ice_check"].agg(lambda s: int((s == "ok").sum())),
        "n_ice_flag": g["ice_check"].agg(lambda s: int(s.str.startswith("flag").sum())),
        "n_ice_excluded": g["ice_check"].agg(lambda s: int(s.str.startswith("excluded").sum())),
        "n_in_exclusion": g["in_exclusion_buffer"].agg(lambda s: int(s.astype(bool).sum())),
    }).reset_index()


# ============================================================================================
# A18 scarcity
# ============================================================================================
def cell_transfers(verdicts: pd.DataFrame, lenses=("L1", "L2")) -> pd.DataFrame:
    v = verdicts[verdicts["lens_id"].isin(lenses) & verdicts["state"].eq("TRANSFERS")]
    return v[v["cell_id"].fillna("").ne("")]


def target_scarcity(verdicts: pd.DataFrame, site_cells: pd.DataFrame,
                    downgraded: set | None = None,
                    reviewed: set | None = None) -> pd.DataFrame:
    """Per lens x target counts. ``reviewed``: (lens, cell) pairs that went through B10; a
    usable cell neither downgraded nor reviewed is counted as B10-unreviewed."""
    downgraded = downgraded or set()
    reviewed = reviewed or set()
    t = cell_transfers(verdicts).merge(
        site_cells[["cell_id", "site_id", "ice_check", "in_exclusion_buffer"]], on="cell_id",
        how="left")
    rows = []
    for (lens, target), g in t.groupby(["lens_id", "target_id"]):
        g = g.drop_duplicates("cell_id")
        usable = g[~g["ice_check"].str.startswith("excluded")]
        clean = usable[~usable["in_exclusion_buffer"].astype(bool)]
        b10 = usable["cell_id"].map(lambda c, lens=lens: (lens, c) in downgraded).astype(bool)
        unrev = usable["cell_id"].map(lambda c, lens=lens: (lens, c) not in reviewed)
        unrev = unrev.astype(bool) & ~b10
        rows.append({"lens_id": lens, "target_id": target,
                     "target_label": TARGET_LABELS.get(target, target), "n_transfers": len(g),
                     "n_ice_ok": int(g["ice_check"].eq("ok").sum()),
                     "n_ice_flag": int(g["ice_check"].str.startswith("flag").sum()),
                     "n_ice_excluded": int(g["ice_check"].str.startswith("excluded").sum()),
                     "n_usable": len(usable), "n_usable_outside_exclusion": len(clean),
                     "n_sites_usable": usable["site_id"].nunique(),
                     "n_usable_b10_downgraded": int(b10.sum()),
                     "n_usable_not_downgraded": int((~b10).sum()),
                     "n_usable_b10_unreviewed": int(unrev.sum()),
                     "usable_cells": ",".join(sorted(usable["cell_id"]))})
    return pd.DataFrame(rows)


# ============================================================================================
# A19 multi-lens
# ============================================================================================
def multilens(cells: pd.DataFrame, partners: pd.DataFrame, verdicts: pd.DataFrame,
              km: float = MULTILENS_KM) -> pd.DataFrame:
    """partners: partner_id, partner_lens, lat, lon, label. State read from verdicts."""
    engine = set(zip(*[verdicts.loc[verdicts["state"].eq("TRANSFERS")
                                    & verdicts["cell_id"].fillna("").ne(""), c]
                       for c in ("lens_id", "cell_id")], strict=True))
    rows = []
    for c in cells.itertuples():
        d = haversine_km(c.lat, c.lon, partners["lat"].to_numpy(), partners["lon"].to_numpy())
        for p, dk in zip(partners.itertuples(), d, strict=True):
            if dk <= km:
                state = ("engine TRANSFERS" if (p.partner_lens, p.partner_id) in engine
                         else "literature-only")
                rows.append({"cell_id": c.cell_id, "site_id": c.site_id, "lenses": c.lenses,
                             "partner_lens": p.partner_lens, "partner_id": p.partner_id,
                             "partner_label": p.label, "distance_km": round(float(dk), 1),
                             "partner_state": state, "edge_of_radius": bool(dk > EDGE_FRAC * km)})
    cols = ["cell_id", "site_id", "lenses", "partner_lens", "partner_id", "partner_label",
            "distance_km", "partner_state", "edge_of_radius"]
    return pd.DataFrame(rows, columns=cols)


# ============================================================================================
# A20 showcase + field/facility cards
# ============================================================================================
def showcase_rules(sites: pd.DataFrame, site_cells: pd.DataFrame, verdicts: pd.DataFrame,
                   ml: pd.DataFrame, downgraded: set | None = None) -> pd.Series:
    downgraded = downgraded or set()
    t = cell_transfers(verdicts)
    t = t[[(lens, c) not in downgraded for lens, c in zip(t["lens_id"], t["cell_id"],
                                                          strict=True)]]
    ridge = set(t.loc[t["target_id"].eq("connecting_ridge"), "cell_id"])
    ok_ridge = site_cells[site_cells["cell_id"].isin(ridge)
                          & ~site_cells["ice_check"].str.startswith("excluded")]
    a = set(ok_ridge["site_id"])
    b = set(ml["site_id"])
    clean = sites[sites["n_in_exclusion"].eq(0)]
    c = ({clean.sort_values(["n_cells", "site_id"], ascending=[False, True])["site_id"].iloc[0]}
         if len(clean) else set())
    return sites["site_id"].map(lambda s: ",".join(r for r, S in (("a", a), ("b", b), ("c", c))
                                                   if s in S))


def b10_downgrades(path=None) -> set[tuple[str, str]]:
    """(lens, cell_id) pairs downgraded to hypothesis by the B10 visual review."""
    path = path or io.CONFIG_DIR / "review_b10.yaml"
    if not path.exists():
        return set()
    out = set()
    for key, d in (io.load_yaml(path).get("features") or {}).items():
        if (d or {}).get("action") == "downgrade" and "-" in key:
            lens, cell = key.split("-", 1)
            out.add((lens, cell))
    return out


def b10_reviewed(path=None) -> set[tuple[str, str]]:
    """(lens, cell_id) pairs that went through the B10 visual review (any action)."""
    path = path or io.CONFIG_DIR / "review_b10.yaml"
    if not path.exists():
        return set()
    return {tuple(k.split("-", 1)) for k in (io.load_yaml(path).get("features") or {})
            if "-" in k}


def site_evidence(sites: pd.DataFrame, members: pd.DataFrame, verdicts: pd.DataFrame,
                  ml: pd.DataFrame, attention_max: int,
                  downgraded: set | None = None,
                  reviewed: set | None = None) -> pd.DataFrame:
    """Per-site evidence by the 2c contract (config/sites.yaml); B10 downgrades cap a lens.
    An X1 partner only ever adds X1 to ``lenses_engine_semiquant``."""
    downgraded = downgraded or set()
    reviewed = b10_reviewed() if reviewed is None else reviewed
    t = cell_transfers(verdicts, lenses=("L1", "L2", "X1", "M1"))
    t = t.merge(members[["cell_id", "site_id"]], on="cell_id")
    ok = ~pd.Series([(lens, c) in downgraded for lens, c in zip(t["lens_id"], t["cell_id"],
                                                                strict=True)], index=t.index)
    own = t[ok].groupby("site_id")["lens_id"].agg(lambda s: set(s)).to_dict()
    hyp = t[~ok].groupby("site_id")["lens_id"].agg(lambda s: set(s)).to_dict()
    eng = ml[ml["partner_state"].eq("engine TRANSFERS")].groupby("site_id")["partner_lens"]
    eng = eng.agg(lambda s: set(s)).to_dict()
    lit = ml[ml["partner_state"].eq("literature-only")].groupby("site_id")["partner_lens"]
    lit = lit.agg(lambda s: set(s)).to_dict()
    out = sites.copy()
    confirmed = [own.get(s, set()) | eng.get(s, set()) for s in out["site_id"]]
    out["lenses_engine_confirmed"] = [",".join(sorted(c - SEMIQUANT_LENSES)) for c in confirmed]
    out["lenses_engine_semiquant"] = [",".join(sorted(c & SEMIQUANT_LENSES)) for c in confirmed]
    tt = t[t["lens_id"].isin(["L1", "L2"])]
    seen = pd.Series([(lens, c) in reviewed for lens, c in zip(tt["lens_id"], tt["cell_id"],
                                                               strict=True)], index=tt.index,
                     dtype=bool)
    unrev = tt[~seen].groupby("site_id")["cell_id"].agg(
        lambda s: ",".join(sorted(set(s))))
    out["b10_unreviewed_cells"] = out["site_id"].map(unrev).fillna("")
    out["lenses_literature_only"] = [",".join(sorted(lit.get(s, set()) - c))
                                     for s, c in zip(out["site_id"], confirmed, strict=True)]
    out["lenses_hypothesis"] = [",".join(sorted(hyp.get(s, set()) - c))
                                for s, c in zip(out["site_id"], confirmed, strict=True)]

    def hidden(r):
        if r["n_in_exclusion"] > 0:
            return "no: inside known-analog buffer"
        if pd.isna(r["attention_n"]):
            return "unknown: attention not known"
        return "yes" if r["attention_n"] <= attention_max else "no: attention above threshold"

    out["hidden_status"] = out.apply(hidden, axis=1)
    return out


def ledger_sources() -> dict:
    """(ledger body, variable) -> source URL/DOI from ledger/<body>.yaml (B7)."""
    out = {}
    for body in ("moon", "mars"):
        for it in io.load_yaml(io.REPO_ROOT / "ledger" / f"{body}.yaml")["items"]:
            out[(body, it.get("variable", it["id"]))] = it.get("source")
    return out


def _row(r, sources: dict | None = None) -> dict:
    tgt = r["target_id"] or None
    out = {"lens": r["lens_id"], "target": tgt,
           "target_label": TARGET_LABELS.get(tgt, tgt) if tgt else None,
           "variable": r["variable"],
           "value": None if pd.isna(r["value"]) else float(r["value"]), "reason": r["reason"]}
    if isinstance(r.get("facility"), str) and r["facility"]:
        out["facility"] = r["facility"]
        if sources is not None:
            # lens-level rows come from the Transfer Ledger (B7); target-level NO-ANALOG rows
            # (e.g. L2 sun geometry) are computed by the engine itself
            out["source"] = sources.get((LEDGER_OF.get(r["lens_id"]), r["variable"])) or (
                "engine: data/derived/verdicts.parquet (A15) / fidelity.parquet" if tgt else None)
    return out


def field_facility(site: dict, cell_ids: list[str], verdicts: pd.DataFrame,
                   partners: pd.DataFrame, sources: dict | None = None,
                   downgraded: set | None = None) -> dict:
    """Field = cell-level TRANSFERS of the site's cells and of engine partners (+ lens-level
    physics that transfers); Facility = NO-ANALOG rows with a facility; Unobserved = rows
    UNOBSERVED. Lens-level TRANSFERS set summaries ("N cells") are never a site's verdict.
    Cells downgraded by B10 for a lens are left out of Field (they are only a hypothesis)."""
    downgraded = downgraded or set()
    v = verdicts.fillna({"cell_id": "", "target_id": "", "facility": ""})
    keep = pd.Series([(lens, c) not in downgraded for lens, c in zip(v["lens_id"], v["cell_id"],
                                                                     strict=True)],
                     index=v.index, dtype=bool)
    v = v[keep]
    own = v[v["cell_id"].isin(cell_ids) & v["state"].eq("TRANSFERS")]
    eng = partners[partners["partner_state"].eq("engine TRANSFERS")]
    part = v[v["cell_id"].isin(eng["partner_id"]) & v["state"].eq("TRANSFERS")
             & v["lens_id"].isin(eng["partner_lens"])]
    lenses = sorted(set(own["lens_id"]) | set(part["lens_id"]))
    targets = set(own["target_id"]) | set(part["target_id"])

    field = []
    for _, g in pd.concat([own, part]).groupby(["lens_id", "target_id", "variable"]):
        best = g.loc[g["value"].astype(float).idxmax()]
        field.append({**_row(best), "n_cells": int(g["cell_id"].nunique()),
                      "best_cell": best["cell_id"]})
    level = v[v["lens_id"].isin(lenses) & v["cell_id"].eq("")
              & (v["target_id"].eq("") | v["target_id"].isin(targets))]
    physics = level[level["state"].eq("TRANSFERS") & level["target_id"].eq("")]
    field += [{**_row(r), "n_cells": None, "best_cell": None} for _, r in physics.iterrows()]
    facility = [_row(r, sources) for _, r in level[level["state"].eq("NO-ANALOG")].iterrows()]
    unobserved = [_row(r) for _, r in level[level["state"].eq("UNOBSERVED")].iterrows()]
    lit = partners[partners["partner_state"].eq("literature-only")]
    notes = [f"{r.partner_lens} {r.partner_label} at {r.distance_km:.0f} km"
             f"{' (edge of radius)' if getattr(r, 'edge_of_radius', False) else ''}: "
             f"literature-only (no cell-level TRANSFERS in verdicts.parquet)"
             for r in lit.drop_duplicates("partner_id").itertuples()]
    return {**site, "lenses": lenses, "field": field, "facility": facility,
            "unobserved": unobserved, "literature_notes": notes}


def render_md(cards: list[dict], scarcity: pd.DataFrame, generated: str) -> str:
    out = ["# Field / Facility split for showcase sites (PLAN 2c, A18–A20)", "",
           f"Generated {generated} by `scripts/sites.py` from `verdicts.parquet` (A15) and "
           "`cell_profiles.parquet` (A13); contract and showcase rule in `config/sites.yaml`. "
           "Post hoc grouping: no threshold or verdict changed. Sites are single-linkage "
           f"clusters of engine-kept cells at {CLUSTER_KM:.0f} km, without ice-excluded cells. "
           "Showcase: (a) a Connecting Ridge TRANSFERS cell not downgraded by B10, "
           "(b) a multi-lens partner, "
           "(c) the largest site outside exclusion buffers.", "",
           "## Target scarcity (A18)", "",
           "Both columns of a comparison must use the same filter (e.g. *usable* vs *usable*). "
           "The comparison also reflects how unusual each lunar target is within its own "
           "population (native rank threshold n/2), not only rarity on Earth. Counts are of the "
           "scored sample: 300 rank cells = top 300 of 196,008 bare-land cells by a coarse "
           "sigma against Connecting Ridge on coarse slope/relief, plus seeds (screened "
           "towards Connecting Ridge at 90 m, not on the fine-scale full metric that binds "
           "it). The Shackleton inner wall is a steep comparison slope, not a Moon Base site.",
           "",
           "| Lens | Target | TRANSFERS cells | ice ok / flag / excluded | usable | usable outside "
           "known-analog buffers | sites | usable, not B10-downgraded (incl. unreviewed) | "
           "of which B10-unreviewed |",
           "|---|---|---|---|---|---|---|---|---|"]
    for r in scarcity.itertuples():
        out.append(f"| {r.lens_id} | {r.target_label} | {r.n_transfers} | {r.n_ice_ok} / "
                   f"{r.n_ice_flag} / {r.n_ice_excluded} | {r.n_usable} | "
                   f"{r.n_usable_outside_exclusion} | {r.n_sites_usable} | "
                   f"{r.n_usable_not_downgraded} | {r.n_usable_b10_unreviewed} |")
    for c in cards:
        att = "unknown" if c["attention_n"] is None else c["attention_n"]
        span = (f" · **spans {c['max_span_km']:.0f} km: a region, not one camp**"
                if c["max_span_km"] > SPAN_WARN_KM else f" · span {c['max_span_km']:.0f} km")
        out += ["", f"## {c['name']}", "",
                f"`{c['site_id']}` · {c['lat']:.2f}, {c['lon']:.2f} · {c['n_cells']} member "
                f"cell(s){span} · ice ok/flag {c['n_ice_ok']}/{c['n_ice_flag']} · in "
                f"known-analog buffer {c['n_in_exclusion']} · Attention {att} · hidden: "
                f"{c['hidden_status']} · showcase rule {c['showcase']}", "",
                f"Engine-confirmed: **{c['lenses_engine_confirmed'] or '—'}**"
                + (f" · engine-semiquant: **{c['lenses_engine_semiquant']}**"
                   if c["lenses_engine_semiquant"] else "")
                + (f" · not yet visually reviewed (B10): {c['b10_unreviewed_cells']}"
                   if c["b10_unreviewed_cells"] else "")
                + (f" · literature-only: {c['lenses_literature_only']}"
                   if c["lenses_literature_only"] else "")
                + (f" · hypothesis (B10 review downgrade, not a finding): "
                   f"{c['lenses_hypothesis']}" if c["lenses_hypothesis"] else "")]
        if c.get("note"):
            out += ["", f"> {c['note']}"]
        if c.get("l2_snow_free_frac"):
            out += ["", "L2 cells, snow-free fraction of the year (MODIS; seasonal snow is the "
                    "risk that downgraded Gêrzê): " + ", ".join(
                        f"{k} {v:.2f}" for k, v in c["l2_snow_free_frac"].items())]
        out += ["", "**Field — test here (transfers)**", ""]
        for f in c["field"]:
            who = f" · {f['n_cells']} cell(s), best {f['best_cell']}" if f["n_cells"] else ""
            out.append(f"- {f['lens']} {LENS_NAMES.get(f['lens'], '')} · "
                       f"{f['target_label'] or 'all targets'} · `{f['variable']}`{who}: "
                       f"{f['reason']}")
        out += ["", "**Facility — cannot test here**", ""]
        out += [f"- {f['lens']} · {f['target_label'] or 'all targets'} · `{f['variable']}` → "
                f"{f.get('facility', '—')}"
                + ("" if not f.get("source") else f" ([source]({f['source']}))"
                   if str(f["source"]).startswith("http") else f" (source: {f['source']})")
                for f in c["facility"]]
        out += ["", "**Unobserved — this engine cannot say**", ""]
        out += [f"- {f['lens']} · `{f['variable']}`: {f['reason']}" for f in c["unobserved"]]
        if c["literature_notes"]:
            out += ["", "**Literature-only neighbours (not engine-confirmed)**", ""]
            out += [f"- {n}" for n in c["literature_notes"]]
    return "\n".join(out) + "\n"


# ============================================================================================
def site_attention(sites: pd.DataFrame, members: pd.DataFrame, enabled: bool) -> pd.DataFrame:
    """B8 query on the site name (named sites), cached in attention.parquet; site Attention =
    max(site-name count, member-cell counts) so a hand-picked name cannot lower it."""
    att = pd.read_parquet(DERIVED / "attention.parquet")
    cache = {r.key: r for r in att.itertuples() if pd.notna(r.n_pubs)}
    rows, today, n_vals = [], dt.date.today().isoformat(), {}
    for s in sites[sites["query"].notna()].itertuples():
        q = f"({s.query}) AND {openalex.CONTEXT}"
        hit = cache.get(s.site_id)
        if hit is not None and hit.query == q:
            n_vals[s.site_id] = int(hit.n_pubs)
            continue
        if not enabled:
            continue
        try:
            n = openalex.count(q)
        except openalex.BudgetExhausted as exc:
            print(f"OpenAlex budget exhausted; site Attention left unknown: {str(exc)[:80]}")
            enabled = False
            continue
        if n is not None:
            n_vals[s.site_id] = n
            rows.append({"key": s.site_id, "name": s.name, "query": q, "n_pubs": n,
                         "source": "OpenAlex", "date": today})
        time.sleep(1.1)
    if rows:
        att = att[~att["key"].isin([r["key"] for r in rows])]
        att = pd.concat([att, pd.DataFrame(rows)], ignore_index=True)
        att["n_pubs"] = att["n_pubs"].astype("Int64")
        att.to_parquet(DERIVED / "attention.parquet", index=False)
    out = sites.copy()
    out["attention_site_name"] = out["site_id"].map(n_vals).astype("Int64")
    cell_max = members.groupby("site_id")["attention_n"].max()
    out["attention_cells_max"] = out["site_id"].map(cell_max).astype("Int64")
    # unknown site-name count -> site Attention unknown (a cell count of 0 says nothing)
    out["attention_n"] = [pd.NA if pd.isna(a) else (a if pd.isna(c) else max(a, c))
                          for a, c in zip(out["attention_site_name"], out["attention_cells_max"],
                                          strict=True)]
    out["attention_n"] = out["attention_n"].astype("Int64")
    return out


def load_partners() -> pd.DataFrame:
    v = pd.read_parquet(DERIVED / "verdicts.parquet")
    x1 = pd.read_parquet(DERIVED / "x1_checklist.parquet").set_index("cell_id")
    xt = v.loc[v["lens_id"].eq("X1") & v["state"].eq("TRANSFERS")
               & v["cell_id"].fillna("").ne(""), "cell_id"].unique()
    xp = pd.DataFrame({"partner_id": xt, "partner_lens": "X1",
                       "lat": x1.loc[xt, "lat"].to_numpy(), "lon": x1.loc[xt, "lon"].to_numpy(),
                       "label": [f"{c} ({x1.loc[c, 'name']})" if isinstance(x1.loc[c, "name"],
                                                                            str) else c
                                 for c in xt]})
    seeds = io.load_yaml(io.CONFIG_DIR / "seeds_m1.yaml")["seeds"]
    mp = pd.DataFrame([{"partner_id": s["id"], "partner_lens": "M1", "lat": s["lat"],
                        "lon": s["lon"], "label": f"seed {s['name']}"} for s in seeds])
    return pd.concat([xp, mp], ignore_index=True)


def build(verdicts: pd.DataFrame, prof: pd.DataFrame, partners: pd.DataFrame,
          attention_enabled: bool = False, attention_max: int = 10,
          cluster_km: float = CLUSTER_KM, multilens_km: float = MULTILENS_KM,
          downgraded: set | None = None, reviewed: set | None = None) -> dict:
    """All 2c tables. Ice-excluded cells are listed but are not site members (contract).
    ``reviewed`` defaults to the pairs in config/review_b10.yaml."""
    reviewed = b10_reviewed() if reviewed is None else reviewed
    prof = prof.copy()
    member = ~prof["ice_check"].astype(str).str.startswith("excluded")
    prof["site_id"] = None
    prof.loc[member, "site_id"] = cluster_cells(prof[member].reset_index(drop=True),
                                                     km=cluster_km).to_numpy()
    members = prof[member].copy()
    names = name_sites(members, CFG["sites"])
    sites = summarise_sites(members).merge(names, on="site_id")
    sites = site_attention(sites, members, enabled=attention_enabled)
    ml = multilens(members, partners, verdicts, km=multilens_km)
    sites["showcase"] = showcase_rules(sites, members, verdicts, ml, downgraded)
    sites = site_evidence(sites, members, verdicts, ml, attention_max, downgraded, reviewed)
    notes = {e["anchor"]: e.get("note") for e in CFG["sites"]}
    sites["note"] = [next((" ".join(str(notes[c]).split()) for c in s.split(",")
                           if notes.get(c)), None) for s in sites["cells"]]
    return {"prof": prof, "members": members, "sites": sites, "multilens": ml,
            "scarcity": target_scarcity(verdicts, prof, downgraded, reviewed)}


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--no-attention", action="store_true")
    args = ap.parse_args()
    from similitude.discovery import ATTENTION_MAX

    verdicts = pd.read_parquet(DERIVED / "verdicts.parquet")
    prof = pd.read_parquet(DERIVED / "cell_profiles.parquet")
    down = b10_downgrades()
    t = build(verdicts, prof, load_partners(), attention_enabled=not args.no_attention,
              attention_max=ATTENTION_MAX, downgraded=down)
    prof, sites, ml, scarcity = t["prof"], t["sites"], t["multilens"], t["scarcity"]

    cols = ["cell_id", "site_id", "lat", "lon", "lenses", "targets", "name", "ice_check",
            "in_exclusion_buffer", "attention_n"]
    prof[cols].to_parquet(DERIVED / "site_cells.parquet", index=False)
    sites.to_parquet(DERIVED / "sites.parquet", index=False)
    scarcity.to_parquet(DERIVED / "target_scarcity.parquet", index=False)
    ml.to_parquet(DERIVED / "multilens.parquet", index=False)

    sources = ledger_sources()
    snow = pd.read_parquet(DERIVED / "earth_L2.parquet").set_index("cell_id")["snow_free_frac"]
    l2 = set(cell_transfers(verdicts, lenses=("L2",))["cell_id"])
    cards = []
    show = sites[sites["showcase"].ne("")].sort_values(["showcase", "n_cells"],
                                                       ascending=[True, False])
    for s in show.to_dict("records"):
        s = {k: (None if pd.isna(v) else v) if not isinstance(v, str) else v
             for k, v in s.items()}
        s["l2_snow_free_frac"] = {c: round(float(snow[c]), 3) for c in s["cells"].split(",")
                                  if c in l2 and c in snow.index and pd.notna(snow[c])}
        cards.append(field_facility(s, s["cells"].split(","), verdicts,
                                    ml[ml["site_id"].eq(s["site_id"])], sources, down))
    generated = dt.datetime.now().strftime("%Y-%m-%d %H:%M")
    (DERIVED / "field_facility.json").write_text(
        json.dumps({"generated": generated, "contract": "config/sites.yaml",
                    "cluster_km": CLUSTER_KM, "target_labels": TARGET_LABELS, "sites": cards},
                   ensure_ascii=False, indent=1, default=str), encoding="utf-8")
    md = io.REPO_ROOT / "docs" / "field_facility.md"
    md.write_text(render_md(cards, scarcity, generated), encoding="utf-8")

    print(f"{len(prof)} cells ({len(t['members'])} members) -> {len(sites)} sites; "
          f"showcase {len(show)}")
    print(scarcity.drop(columns="usable_cells").to_string(index=False))
    print(show[["name", "n_cells", "max_span_km", "lenses_engine_confirmed",
                "lenses_engine_semiquant", "lenses_hypothesis",
                "attention_n", "hidden_status", "showcase"]].to_string(index=False))


if __name__ == "__main__":
    main()
