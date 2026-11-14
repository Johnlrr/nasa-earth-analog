"""A13 — profile every cell the engine keeps for L1/L2 (cell-level TRANSFERS in verdicts.parquet).

For each cell: a place name (reverse-geocode, same call and cache as discovery B9), Attention
(same OpenAlex query as B8, scripts/attention/openalex.py), ``ice_frac`` (ESA WorldCover v200
class 70 = permanent snow/ice, mean over the footprint) and a summer-median Sentinel-2 RGB chip.

Thresholds committed in PLAN 2b before any result was seen:
    ice_frac > 0.2        -> excluded (not a terrain candidate: the surface is ice, not regolith)
    0.05 <= ice_frac <= 0.2 -> flag
Class 70 only catches perennial ice; L2 seasonal snow is reported through ``snow_free_frac``.

Inputs : data/derived/verdicts.parquet, earth_L1.parquet, earth_L2.parquet
Outputs: data/derived/cell_profiles.parquet (one row per cell; also the GEE/geocode cache)
         earth_L1.parquet / earth_L2.parquet: columns name (filled only where empty), ice_frac,
         review_note for the profiled cells
         data/raw/review/l1_contact_sheet.png (+ chips in data/raw/review/s2/)
Usage  : python scripts/l1_profile.py [--no-sheet] [--refresh]
"""

from __future__ import annotations

import argparse
import datetime as dt
import json
import os
import sys
import time

import numpy as np
import pandas as pd
import requests

from similitude import io
from similitude.discovery import footprint_box

sys.path.insert(0, str(io.REPO_ROOT / "scripts" / "discovery"))
sys.path.insert(0, str(io.REPO_ROOT / "scripts" / "attention"))
import openalex  # noqa: E402
from run_discovery import GEOCODE_CACHE, reverse_geocode  # noqa: E402

DERIVED = io.REPO_ROOT / "data" / "derived"
REVIEW = io.REPO_ROOT / "data" / "raw" / "review"
PROFILES = DERIVED / "cell_profiles.parquet"
LENSES = ("L1", "L2")
ICE_EXCLUDE = 0.2
ICE_FLAG = 0.05
S2_YEARS = (2022, 2024)
S2_MAX_CLOUD = 20


# ============================================================================================
# Pure helpers (tested)
# ============================================================================================
def profiled_cells(verdicts: pd.DataFrame, lenses=LENSES) -> pd.DataFrame:
    """Cells with a cell-level TRANSFERS row for any of ``lenses``; lenses/targets joined."""
    v = verdicts[verdicts["lens_id"].isin(lenses) & verdicts["state"].eq("TRANSFERS")
                 & verdicts["cell_id"].fillna("").ne("")]
    g = v.groupby("cell_id")
    return pd.DataFrame({
        "lenses": g["lens_id"].agg(lambda s: ",".join(sorted(set(s)))),
        "targets": g.apply(lambda d: ",".join(sorted(f"{a}:{b}" for a, b in
                                                     set(zip(d["lens_id"], d["target_id"],
                                                             strict=True)))),
                           include_groups=False),
    }).reset_index()


def ice_check(ice_frac: float | None) -> str:
    if ice_frac is None or pd.isna(ice_frac):
        return "not assessed"
    if ice_frac > ICE_EXCLUDE:
        return "excluded: perennial ice"
    if ice_frac >= ICE_FLAG:
        return "flag: some ice"
    return "ok"


def review_note(row) -> str:
    notes = [f"ice {ice_check(row['ice_frac'])}"]
    if pd.isna(row.get("name")):
        notes.append("name pending (geocoder unreachable)")
    if pd.isna(row.get("attention_n")):
        notes.append("attention unknown")
    if bool(row.get("in_exclusion_buffer")):
        notes.append("inside known-analog exclusion buffer")
    if "L2" in str(row.get("lenses", "")) and pd.notna(row.get("snow_free_frac")):
        notes.append(f"snow_free_frac {row['snow_free_frac']:.2f}")
    return "; ".join(notes)


def apply_profiles(earth: pd.DataFrame, prof: pd.DataFrame) -> pd.DataFrame:
    """Write name (only where empty), ice_frac and review_note onto the profiled cells."""
    out = earth.copy()
    p = prof.set_index("cell_id")
    for col in ("ice_frac", "review_note"):
        if col not in out:
            out[col] = np.nan if col == "ice_frac" else None
    hit = out["cell_id"].isin(p.index)
    ids = out.loc[hit, "cell_id"]
    out.loc[hit, "ice_frac"] = ids.map(p["ice_frac"]).astype(float).values
    out.loc[hit, "review_note"] = ids.map(p["review_note"]).values
    empty = hit & (out["name"].isna() | out["name"].astype(str).str.strip().eq(""))
    out.loc[empty, "name"] = out.loc[empty, "cell_id"].map(p["name"]).values
    return out


# ============================================================================================
# External sources
# ============================================================================================
def _ee():
    import ee

    ee.Initialize(project=os.environ["EE_PROJECT"])
    return ee


def _box(ee, r):
    x0, y0, x1, y1 = footprint_box(r.lat, r.lon, r.footprint_km)
    return ee.Geometry.Rectangle([x0, y0, x1, y1], None, False)


def ice_fraction(ee, cells: pd.DataFrame) -> dict:
    """WorldCover class 70 mean over each footprint, native 10 m."""
    wc = ee.ImageCollection("ESA/WorldCover/v200").first().select("Map").eq(70).rename("ice")
    fc = ee.FeatureCollection([ee.Feature(_box(ee, r), {"cell_id": r.cell_id})
                               for r in cells.itertuples()])
    res = wc.reduceRegions(fc, ee.Reducer.mean(), scale=10, tileScale=4).getInfo()
    return {f["properties"]["cell_id"]: f["properties"].get("mean") for f in res["features"]}


def s2_chip(ee, r, path) -> bool:
    """Summer-median Sentinel-2 L2A true colour over the footprint (local summer by hemisphere)."""
    if path.exists():
        return True
    months = (6, 8) if r.lat >= 0 else (12, 2)  # calendarRange wraps when start > end
    col = (ee.ImageCollection("COPERNICUS/S2_SR_HARMONIZED")
           .filterBounds(_box(ee, r))
           .filterDate(f"{S2_YEARS[0]}-01-01", f"{S2_YEARS[1] + 1}-01-01")
           .filter(ee.Filter.calendarRange(months[0], months[1], "month"))
           .filter(ee.Filter.lt("CLOUDY_PIXEL_PERCENTAGE", S2_MAX_CLOUD)))
    # EPSG:3857 so a km-square footprint stays square at high latitude (4326 squashes it)
    url = col.median().getThumbURL({"region": _box(ee, r), "dimensions": 256, "format": "png",
                                    "crs": "EPSG:3857",
                                    "bands": ["B4", "B3", "B2"], "min": 0, "max": 3000})
    resp = requests.get(url, timeout=120)
    if not resp.ok:
        return False
    path.write_bytes(resp.content)
    return True


def geocode_all(cells: pd.DataFrame) -> list[tuple]:
    """Discovery's reverse_geocode with its cache; once the geocoder is unreachable, cached cells
    still get a name and the rest stay (None, None, None) so a later rerun fills them."""
    cache = json.loads(GEOCODE_CACHE.read_text(encoding="utf-8")) if GEOCODE_CACHE.exists() else {}
    out, online = [], True
    try:
        for r in cells.itertuples():
            if not online and f"{r.lat:.3f},{r.lon:.3f}" not in cache:
                out.append((None, None, None))
                continue
            try:
                out.append(reverse_geocode(r.lat, r.lon, cache))
            except requests.RequestException as exc:
                print(f"geocoder unreachable ({type(exc).__name__}); using cache only")
                online = False
                out.append((None, None, None))
    finally:
        GEOCODE_CACHE.write_text(json.dumps(cache), encoding="utf-8")
    return out


def attention(cells: pd.DataFrame, att: pd.DataFrame) -> pd.DataFrame:
    """B8 query for cells not yet in attention.parquet; register names for future B8 reruns.
    A cell without a place name is skipped (its attention stays unknown, never 'hidden')."""
    cells = cells[cells["name"].notna()]
    have = set(att["key"])
    todo = cells[~cells["cell_id"].isin(have)]
    rows, today = [], dt.date.today().isoformat()
    for r in todo.itertuples():
        e = {"key": r.cell_id, "name": r.name, "place": r.place}
        q = openalex.build_query(e)
        try:
            n = openalex.count(q)
        except openalex.BudgetExhausted as exc:
            print(f"OpenAlex budget exhausted, {len(todo) - len(rows)} cells left: {exc}")
            break
        rows.append({"key": r.cell_id, "name": r.name, "query": q, "n_pubs": n,
                     "source": "OpenAlex", "date": today})
        print(f"  {r.cell_id:18s} {n!s:>5}  {q[:80]}")
        time.sleep(1.1)
    if rows:
        att = pd.concat([att, pd.DataFrame(rows)], ignore_index=True)
        att["n_pubs"] = att["n_pubs"].astype("Int64")
        att.to_parquet(DERIVED / "attention.parquet", index=False)
    cn = DERIVED / "candidate_names.csv"
    old = pd.read_csv(cn) if cn.exists() else pd.DataFrame(columns=["key", "name", "place"])
    new = cells.rename(columns={"cell_id": "key"})[["key", "name", "place"]]
    new = new[~new["key"].isin(old["key"])]
    if len(new):
        pd.concat([old, new], ignore_index=True).to_csv(cn, index=False)
    return att


# ============================================================================================
# Contact sheet
# ============================================================================================
def contact_sheet(prof: pd.DataFrame, chips_dir, out_path, ncol: int = 12) -> None:
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    p = prof.sort_values(["lenses", "targets", "name", "cell_id"]).reset_index(drop=True)
    nrow = int(np.ceil(len(p) / ncol))
    fig, axes = plt.subplots(nrow, ncol, figsize=(ncol * 2.2, nrow * 2.75))
    colour = {"ok": "#2e7d32", "flag: some ice": "#ef6c00", "excluded: perennial ice": "#c62828",
              "not assessed": "#757575"}
    for ax, (_, r) in zip(np.ravel(axes), p.iterrows(), strict=False):
        chip = chips_dir / f"{r['cell_id']}.png"
        if chip.exists():
            ax.imshow(plt.imread(chip))
        else:
            ax.text(0.5, 0.5, "no S2 chip", ha="center", va="center", transform=ax.transAxes)
        att = "?" if pd.isna(r["attention_n"]) else int(r["attention_n"])
        ice = "n/a" if pd.isna(r["ice_frac"]) else f"{r['ice_frac']:.2f}"
        nm = "(name pending)" if pd.isna(r["name"]) else str(r["name"])[:30]
        ax.set_title(f"{r['cell_id']} [{r['lenses']}]\n{nm}\n"
                     f"ice {ice} · att {att}", fontsize=6.5)
        for s in ax.spines.values():
            s.set_edgecolor(colour[r["ice_check"]])
            s.set_linewidth(3)
        ax.set_xticks([])
        ax.set_yticks([])
    for ax in np.ravel(axes)[len(p):]:
        ax.axis("off")
    fig.suptitle(f"A13 — L1/L2 engine-kept cells ({len(p)}): Sentinel-2 L2A summer median "
                 f"{S2_YEARS[0]}–{S2_YEARS[1]}, footprint box. Border: green ok, orange ice "
                 f"0.05–0.2 (flag), red > 0.2 (excluded)", fontsize=10)
    fig.tight_layout(rect=(0, 0, 1, 0.985))
    fig.savefig(out_path, dpi=110)
    plt.close(fig)


# ============================================================================================
def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--no-sheet", action="store_true", help="skip Sentinel-2 chips/contact sheet")
    ap.add_argument("--refresh", action="store_true", help="recompute ice_frac for every cell")
    args = ap.parse_args()

    cells = profiled_cells(pd.read_parquet(DERIVED / "verdicts.parquet"))
    e1 = pd.read_parquet(DERIVED / "earth_L1.parquet")
    e2 = pd.read_parquet(DERIVED / "earth_L2.parquet")
    geo = e1[["cell_id", "lat", "lon", "footprint_km", "in_exclusion_buffer"]].drop_duplicates(
        "cell_id")
    cells = cells.merge(geo, on="cell_id", how="left").merge(
        e2[["cell_id", "snow_free_frac"]].drop_duplicates("cell_id"), on="cell_id", how="left")
    if cells["lat"].isna().any():
        raise SystemExit(f"cells missing from earth_L1: {cells[cells['lat'].isna()]['cell_id']}")
    print(f"A13: {len(cells)} cells "
          f"(L1 {cells['lenses'].str.contains('L1').sum()}, "
          f"L2 {cells['lenses'].str.contains('L2').sum()})")

    # names (same Nominatim call + cache as discovery)
    named = geocode_all(cells)
    cells["name"] = [None if d is None else (f"{d} ({c})" if c else d) for d, _, c in named]
    cells["place"] = [p for _, p, _ in named]
    cells["country"] = [c for _, _, c in named]

    # attention (B8 query)
    att = attention(cells, pd.read_parquet(DERIVED / "attention.parquet"))
    a = att.drop_duplicates("key", keep="last").set_index("key")
    cells["attention_n"] = cells["cell_id"].map(a["n_pubs"]).astype("Int64")
    cells["attention_query"] = cells["cell_id"].map(a["query"])

    # ice fraction (cached in cell_profiles.parquet)
    prev = pd.read_parquet(PROFILES).set_index("cell_id") if PROFILES.exists() else None
    known = {} if (prev is None or args.refresh) else prev["ice_frac"].dropna().to_dict()
    todo = cells[~cells["cell_id"].isin(known)]
    ee = None
    if len(todo):
        ee = _ee()
        known.update(ice_fraction(ee, todo))
    cells["ice_frac"] = cells["cell_id"].map(known).astype(float)
    cells["ice_check"] = cells["ice_frac"].map(ice_check)
    cells["review_note"] = cells.apply(review_note, axis=1)
    cells["profile_complete"] = (cells["name"].notna()
                                 & cells["attention_query"].notna() & cells["ice_frac"].notna())
    cells.to_parquet(PROFILES, index=False)

    for lens_id, e in (("L1", e1), ("L2", e2)):
        apply_profiles(e, cells).to_parquet(DERIVED / f"earth_{lens_id}.parquet", index=False)

    if not args.no_sheet:
        chips = REVIEW / "s2"
        chips.mkdir(parents=True, exist_ok=True)
        ee = ee or _ee()
        missing = [r.cell_id for r in cells.itertuples() if not s2_chip(ee, r, chips /
                                                                         f"{r.cell_id}.png")]
        if missing:
            print(f"no S2 chip for {len(missing)} cells: {missing[:10]}")
        contact_sheet(cells, chips, REVIEW / "l1_contact_sheet.png")
        print(f"contact sheet -> {REVIEW / 'l1_contact_sheet.png'}")

    print(cells["ice_check"].value_counts().to_string())
    print(f"attention unknown: {int(cells['attention_n'].isna().sum())}; "
          f"profile complete: {int(cells['profile_complete'].sum())}/{len(cells)}")
    show = cells[cells["ice_check"].ne("ok") | cells["lenses"].str.contains("L2")]
    print(show[["cell_id", "lenses", "name", "ice_frac", "attention_n", "review_note"]]
          .round(3).to_string(index=False))


if __name__ == "__main__":
    main()
