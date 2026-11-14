"""PLAN 2c (A17-A20) — present engine findings as field sites, not 4 km cells.

Nothing here changes a threshold or a verdict: every table is a regrouping of
``verdicts.parquet`` (A15) and ``cell_profiles.parquet`` (A13). All steps are post hoc
(the cell distribution was seen first) and are listed in the A9b Deviations table.

A17 sites       : single-linkage clusters of A13 cells at CLUSTER_KM (one field campaign's
                  driving range); site_id = "site:<smallest cell_id>"; names from
                  config/site_names.yaml; Attention by site name (same B8 context).
A18 scarcity    : per lens x target, how many TRANSFERS cells survive the ice filter, how many
                  lie outside known-analog exclusion buffers, in how many sites.
A19 multi-lens  : A13 cells within CLUSTER_KM of an X1 TRANSFERS cell or an M1 seed; the other
                  lens' state is read from verdicts.parquet (no cell-level TRANSFERS ->
                  literature-only, never engine-confirmed).
A20 field/facility cards for showcase sites, chosen by rule:
                  (a) holds a Connecting Ridge TRANSFERS cell whose ice is not excluded;
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
CLUSTER_KM = 150.0
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

    g = site_cells.groupby("site_id")
    return pd.DataFrame({
        "lat": g["lat"].mean(), "lon": g["lon"].mean(), "n_cells": g.size(),
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


def target_scarcity(verdicts: pd.DataFrame, site_cells: pd.DataFrame) -> pd.DataFrame:
    t = cell_transfers(verdicts).merge(
        site_cells[["cell_id", "site_id", "ice_check", "in_exclusion_buffer"]], on="cell_id",
        how="left")
    rows = []
    for (lens, target), g in t.groupby(["lens_id", "target_id"]):
        g = g.drop_duplicates("cell_id")
        usable = g[~g["ice_check"].str.startswith("excluded")]
        clean = usable[~usable["in_exclusion_buffer"].astype(bool)]
        rows.append({"lens_id": lens, "target_id": target, "n_transfers": len(g),
                     "n_ice_ok": int(g["ice_check"].eq("ok").sum()),
                     "n_ice_flag": int(g["ice_check"].str.startswith("flag").sum()),
                     "n_ice_excluded": int(g["ice_check"].str.startswith("excluded").sum()),
                     "n_usable": len(usable), "n_usable_outside_exclusion": len(clean),
                     "n_sites_usable": usable["site_id"].nunique(),
                     "usable_cells": ",".join(sorted(usable["cell_id"]))})
    return pd.DataFrame(rows)


# ============================================================================================
# A19 multi-lens
# ============================================================================================
def multilens(cells: pd.DataFrame, partners: pd.DataFrame, verdicts: pd.DataFrame,
              km: float = CLUSTER_KM) -> pd.DataFrame:
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
                             "partner_state": state})
    cols = ["cell_id", "site_id", "lenses", "partner_lens", "partner_id", "partner_label",
            "distance_km", "partner_state"]
    return pd.DataFrame(rows, columns=cols)


# ============================================================================================
# A20 showcase + field/facility cards
# ============================================================================================
def showcase_rules(sites: pd.DataFrame, site_cells: pd.DataFrame, verdicts: pd.DataFrame,
                   ml: pd.DataFrame) -> pd.Series:
    t = cell_transfers(verdicts)
    ridge = set(t.loc[t["target_id"].eq("connecting_ridge"), "cell_id"])
    ok_ridge = site_cells[site_cells["cell_id"].isin(ridge)
                          & ~site_cells["ice_check"].str.startswith("excluded")]
    a = set(ok_ridge["site_id"])
    b = set(ml["site_id"])
    clean = sites[sites["n_in_exclusion"].eq(0)]
    c = set(clean.loc[clean["n_cells"].eq(clean["n_cells"].max()), "site_id"]) if len(clean) \
        else set()
    return sites["site_id"].map(lambda s: ",".join(r for r, S in (("a", a), ("b", b), ("c", c))
                                                   if s in S))


def _row(r) -> dict:
    out = {"lens": r["lens_id"], "target": r["target_id"] or None, "variable": r["variable"],
           "value": None if pd.isna(r["value"]) else float(r["value"]), "reason": r["reason"]}
    if isinstance(r.get("facility"), str) and r["facility"]:
        out["facility"] = r["facility"]
    return out


def field_facility(site: dict, cell_ids: list[str], verdicts: pd.DataFrame,
                   partners: pd.DataFrame) -> dict:
    """Field = cell-level TRANSFERS of the site's cells and of engine partners (+ lens-level
    physics that transfers); Facility = NO-ANALOG rows with a facility; Unobserved = rows
    UNOBSERVED. Lens-level TRANSFERS set summaries ("N cells") are never a site's verdict."""
    v = verdicts.fillna({"cell_id": "", "target_id": "", "facility": ""})
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
    facility = [_row(r) for _, r in level[level["state"].eq("NO-ANALOG")].iterrows()]
    unobserved = [_row(r) for _, r in level[level["state"].eq("UNOBSERVED")].iterrows()]
    lit = partners[partners["partner_state"].eq("literature-only")]
    notes = [f"{r.partner_lens} {r.partner_label} at {r.distance_km:.0f} km: literature-only "
             f"(no cell-level TRANSFERS in verdicts.parquet)"
             for r in lit.drop_duplicates("partner_id").itertuples()]
    return {**site, "lenses": lenses, "field": field, "facility": facility,
            "unobserved": unobserved, "literature_notes": notes}


def render_md(cards: list[dict], scarcity: pd.DataFrame, generated: str) -> str:
    out = ["# Field / Facility split for showcase sites (PLAN 2c, A18–A20)", "",
           f"Generated {generated} by `scripts/sites.py` from `verdicts.parquet` (A15) and "
           "`cell_profiles.parquet` (A13). Post hoc grouping: no threshold or verdict changed. "
           "Sites are single-linkage clusters of engine-kept cells at "
           f"{CLUSTER_KM:.0f} km; showcase rule: (a) Connecting Ridge cell with usable ice, "
           "(b) multi-lens partner, (c) largest site outside exclusion buffers.", "",
           "## Target scarcity (A18)", "",
           "| Lens | Target | TRANSFERS cells | ice ok / flag / excluded | usable | usable outside "
           "known-analog buffers | sites |", "|---|---|---|---|---|---|---|"]
    for r in scarcity.itertuples():
        out.append(f"| {r.lens_id} | {r.target_id} | {r.n_transfers} | {r.n_ice_ok} / "
                   f"{r.n_ice_flag} / {r.n_ice_excluded} | {r.n_usable} | "
                   f"{r.n_usable_outside_exclusion} | {r.n_sites_usable} |")
    for c in cards:
        att = "unknown" if c["attention_n"] is None else c["attention_n"]
        out += ["", f"## {c['name']}", "",
                f"`{c['site_id']}` · {c['lat']:.2f}, {c['lon']:.2f} · {c['n_cells']} cells · "
                f"lenses {', '.join(c['lenses'])} · ice ok/flag/excluded {c['n_ice_ok']}/"
                f"{c['n_ice_flag']}/{c['n_ice_excluded']} · in known-analog buffer "
                f"{c['n_in_exclusion']} · Attention (site name) {att} · showcase rule "
                f"{c['showcase']}", "", "**Field — test here (transfers)**", ""]
        for f in c["field"]:
            who = f" · {f['n_cells']} cell(s), best {f['best_cell']}" if f["n_cells"] else ""
            out.append(f"- {f['lens']} {LENS_NAMES.get(f['lens'], '')} · "
                       f"{f['target'] or 'all targets'} · `{f['variable']}`{who}: {f['reason']}")
        out += ["", "**Facility — cannot test here**", ""]
        out += [f"- {f['lens']} · {f['target'] or 'all targets'} · `{f['variable']}` → "
                f"{f.get('facility', '—')}" for f in c["facility"]]
        out += ["", "**Unobserved — this engine cannot say**", ""]
        out += [f"- {f['lens']} · `{f['variable']}`: {f['reason']}" for f in c["unobserved"]]
        if c["literature_notes"]:
            out += ["", "**Literature-only neighbours (not engine-confirmed)**", ""]
            out += [f"- {n}" for n in c["literature_notes"]]
    return "\n".join(out) + "\n"


# ============================================================================================
def site_attention(sites: pd.DataFrame, enabled: bool) -> pd.DataFrame:
    """B8 query on the site name (manual sites only); cached in attention.parquet."""
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
            break
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
    out["attention_n"] = out["site_id"].map(n_vals).astype("Int64")
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


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--no-attention", action="store_true")
    args = ap.parse_args()

    verdicts = pd.read_parquet(DERIVED / "verdicts.parquet")
    prof = pd.read_parquet(DERIVED / "cell_profiles.parquet")
    prof["site_id"] = cluster_cells(prof)
    names = name_sites(prof, io.load_yaml(io.CONFIG_DIR / "site_names.yaml")["sites"])
    sites = summarise_sites(prof).merge(names, on="site_id")
    sites = site_attention(sites, enabled=not args.no_attention)

    ml = multilens(prof, load_partners(), verdicts)
    sites["showcase"] = showcase_rules(sites, prof, verdicts, ml)
    scarcity = target_scarcity(verdicts, prof)

    cols = ["cell_id", "site_id", "lat", "lon", "lenses", "targets", "name", "ice_check",
            "in_exclusion_buffer"]
    prof[cols].to_parquet(DERIVED / "site_cells.parquet", index=False)
    sites.to_parquet(DERIVED / "sites.parquet", index=False)
    scarcity.to_parquet(DERIVED / "target_scarcity.parquet", index=False)
    ml.to_parquet(DERIVED / "multilens.parquet", index=False)

    cards = []
    show = sites[sites["showcase"].ne("")].sort_values(["showcase", "n_cells"],
                                                       ascending=[True, False])
    for s in show.to_dict("records"):
        s = {k: (None if pd.isna(v) else v) if not isinstance(v, str) else v
             for k, v in s.items()}
        cells = s["cells"].split(",")
        cards.append(field_facility(s, cells, verdicts, ml[ml["site_id"].eq(s["site_id"])]))
    generated = dt.datetime.now().strftime("%Y-%m-%d %H:%M")
    (DERIVED / "field_facility.json").write_text(
        json.dumps({"generated": generated, "cluster_km": CLUSTER_KM, "sites": cards},
                   ensure_ascii=False, indent=1, default=str), encoding="utf-8")
    md = io.REPO_ROOT / "docs" / "field_facility.md"
    md.write_text(render_md(cards, scarcity, generated), encoding="utf-8")

    print(f"{len(prof)} cells -> {len(sites)} sites; showcase {len(show)}")
    print(scarcity.drop(columns="usable_cells").to_string(index=False))
    print(show[["site_id", "name", "n_cells", "lenses", "n_ice_excluded", "n_in_exclusion",
                "attention_n", "showcase"]].to_string(index=False))
    print(ml.drop(columns=["lenses"]).sort_values("distance_km").to_string(index=False))


if __name__ == "__main__":
    main()
