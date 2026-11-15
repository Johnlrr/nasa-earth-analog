# ruff: noqa: E501  (long literal rows in the web export)
"""Where can a NASA test team actually go? L1 terrain leads in countries open to NASA field work.

The published screen ranked all 196,008 bare-land cells by a coarse sigma against Connecting Ridge
and scored the top 300 (plus seeds and 1,200 random cells). Its two ridge matches lie in Qinghai
(China) and North Greenland; Zanda/Gar and Gêrzê are in Tibet. NASA cannot run a bilateral field
campaign in China (Wolf Amendment), so for a NASA engineer the first question is unanswered:
where, in a country NASA can work in, is there terrain like the Moon Base sites?

This script answers it with the SAME rules and code, changing nothing that was published:
  1. same coarse ranking (scripts/select_tier2.py: diagonal sigma on 4 coarse 90 m descriptors
     against Connecting Ridge) over all tier-1 bare-land cells;
  2. country of each cell from the US State Department LSIB polygons (GEE USDOS/LSIB_SIMPLE/2017);
     a cell is "open" unless it lies in an EXCLUDED country (list below, an assumption stated in
     the output, not a legal opinion);
  3. the top N open cells not scored before (30 km non-max suppression, as in the screen) get the
     same fine L1 descriptors from the same DEM (Copernicus GLO-30, 30 m and 60 m baselines);
  4. the unchanged robust-set rule (native rank >= n/2 in all three configurations) for all six
     PGDA 78 south-pole regions (scripts/l1_regions.score_cells);
  5. every pass is recomputed from a second DEM (NASADEM; ArcticDEM above 60 N) with the same
     rule, and its snow/ice and water share is read from ESA WorldCover.
Cells scored earlier (rank, seed, random null) are re-read, not re-scored, and get a country too.

Post hoc, exploratory: these are leads for a field team, never verdicts (verdicts.parquet is not
touched). Outputs: data/derived/access_screen.parquet (new cells, all regions),
data/derived/access_leads.parquet + web/data/access.json (open-country passes, all sources).
Usage: EE_PROJECT=<project> python scripts/access/access_screen.py [--n 160]
"""

from __future__ import annotations

import argparse
import datetime as dt
import json
import os
import sys
from concurrent.futures import ProcessPoolExecutor

import numpy as np
import pandas as pd

from similitude import io
from similitude.descriptors.terrain import terrain_descriptors

sys.path.insert(0, str(io.REPO_ROOT / "scripts"))
import cross_dem as cd  # noqa: E402
import l1_regions as lr  # noqa: E402
from gee.chip_dem import get_chip  # noqa: E402
from select_tier2 import RANK_COLS, _diagonal_d, _min_scales, _nms_30km  # noqa: E402

DERIVED = io.REPO_ROOT / "data" / "derived"
OUT_NEW, OUT_LEADS = DERIVED / "access_screen.parquet", DERIVED / "access_leads.parquet"
OUT_WEB = io.REPO_ROOT / "web" / "data" / "access.json"
RES_M, FOOTPRINT_M, EARTH_R = 30.0, 4000.0, 6_371_000.0
POOL = 8000  # coarse-ranked cells looked up for a country before filtering
ICE_MAX = 0.2  # same ice rule as the published sites (config/sites.yaml, A13): WorldCover class 70 > 0.2 excludes

# Assumption, stated in every output: NASA cannot run a bilateral campaign in China (Wolf
# Amendment, 2011 and later appropriations); Russia (cooperation suspended outside the ISS) and
# countries under comprehensive US sanctions are also treated as closed. Everything else is open.
# "Aksai Chin" is a separate LSIB name for a China-administered disputed area: closed with China.
EXCLUDED = ["China", "Aksai Chin", "Russia", "Iran", "Korea, North", "Syria", "Cuba", "Belarus",
            "Venezuela"]
REGION_LABEL = {"connecting_ridge": "Connecting Ridge", "shackleton_rim": "Shackleton inner wall",
                "de_gerlache_rim": "de Gerlache rim", "peak_near_shackleton": "Peak near Shackleton",
                "nobile_rim_1": "Nobile rim 1", "malapert_massif": "Malapert massif"}
PUBLISHED = {"connecting_ridge", "shackleton_rim"}  # the other four use a medoid reference


def _ee():
    import ee
    ee.Initialize(project=os.environ["EE_PROJECT"])
    return ee


def countries(cells: pd.DataFrame) -> pd.Series:
    """LSIB country name of each cell centre (spatial join on the GEE server, 400 at a time)."""
    ee = _ee()
    lsib = ee.FeatureCollection("USDOS/LSIB_SIMPLE/2017")
    out = {}
    rows = list(cells[["cell_id", "lat", "lon"]].itertuples(index=False))
    for i in range(0, len(rows), 400):
        pts = ee.FeatureCollection([ee.Feature(ee.Geometry.Point(float(r.lon), float(r.lat)),
                                               {"cell_id": r.cell_id}) for r in rows[i:i + 400]])
        joined = ee.Join.saveFirst("c").apply(
            pts, lsib, ee.Filter.intersects(leftField=".geo", rightField=".geo", maxError=100))
        got = joined.map(lambda f: ee.Feature(None, {
            "cell_id": f.get("cell_id"), "country": ee.Feature(f.get("c")).get("country_na")}))
        for f in got.getInfo()["features"]:
            out[f["properties"]["cell_id"]] = f["properties"].get("country")
    return cells["cell_id"].map(out).fillna("unknown")


def worldcover_shares(cells: pd.DataFrame) -> pd.DataFrame:
    """Snow/ice (class 70) and water (class 80) share inside the 4 km footprint."""
    ee = _ee()
    wc = ee.ImageCollection("ESA/WorldCover/v200").first().select("Map")
    img = wc.eq(70).rename("snow_ice").addBands(wc.eq(80).rename("water"))
    feats = [ee.Feature(ee.Geometry.Point(float(r.lon), float(r.lat)).buffer(FOOTPRINT_M / 2)
                        .bounds(), {"cell_id": r.cell_id}) for r in cells.itertuples()]
    res = img.reduceRegions(ee.FeatureCollection(feats), ee.Reducer.mean(), scale=30).getInfo()
    return pd.DataFrame([{"cell_id": f["properties"]["cell_id"],
                          "snow_ice_frac": f["properties"].get("snow_ice"),
                          "water_frac": f["properties"].get("water")} for f in res["features"]])


def coarse_pool() -> pd.DataFrame:
    """The screen's coarse ranking (select_tier2.main), all tier-1 cells, best POOL kept."""
    tier1 = pd.read_parquet(DERIVED / "tier1_terrain.parquet")
    coarse = pd.read_parquet(DERIVED / "targets_L1_coarse.parquet")
    ref = coarse[(coarse["target_id"] == "connecting_ridge") & coarse["is_reference"]].iloc[0]
    pop = coarse[~coarse["is_reference"].astype(bool)]
    mat = np.where(np.isnan(tier1[RANK_COLS].to_numpy(float)), 1e9, tier1[RANK_COLS].to_numpy(float))
    tier1["d_coarse"] = _diagonal_d(mat, ref[RANK_COLS].to_numpy(float),
                                    pop[RANK_COLS].std().to_numpy(float),
                                    _min_scales({"relief_90m": float(ref["relief_90m"])}))
    tier1["coarse_rank"] = tier1["d_coarse"].rank(method="first").astype(int)
    return tier1.nsmallest(POOL, "d_coarse").reset_index(drop=True)


def _one(row: tuple) -> tuple[dict, dict]:
    cell_id, lat, lon, zone = row
    base = {"cell_id": cell_id, "lat": lat, "lon": lon, "sample_role": "access",
            "in_exclusion_buffer": bool(zone), "L_m": RES_M}
    try:
        dem, meta = get_chip(lat, lon, chip_m=10_000, res_m=RES_M)
        nodata = float(meta.get("nodata_frac", 1.0))
        c = dem.shape[0] // 2
        h = int(FOOTPRINT_M / RES_M / 2)
        elev = float(np.nanmean(dem[c - h:c + h, c - h:c + h]))
        d30 = terrain_descriptors(dem, RES_M, 30.0, radius_m=EARTH_R, footprint_m=FOOTPRINT_M)
        d60 = terrain_descriptors(dem, RES_M, 60.0, radius_m=EARTH_R, footprint_m=FOOTPRINT_M)
        return ({**base, "qa_flag": "ok" if nodata < 0.05 else "nodata", "elev_m": elev, **d30},
                {"cell_id": cell_id, **d60})
    except Exception as exc:  # recorded, never silently dropped
        return ({**base, "qa_flag": f"error:{str(exc)[:120]}"}, {"cell_id": cell_id})


def _alt_one(r: tuple) -> tuple[dict, dict]:
    cell_id, lat, lon = r
    s = cd.source_for(lat)
    try:
        dem = cd.alt_chip(lat, lon, s)
        ok = float(np.isnan(dem).mean()) < 0.05
        a = terrain_descriptors(dem, RES_M, 30.0, radius_m=EARTH_R, footprint_m=FOOTPRINT_M)
        b = terrain_descriptors(dem, RES_M, 60.0, radius_m=EARTH_R, footprint_m=FOOTPRINT_M)
    except Exception as exc:
        print(f"  second DEM {cell_id}: {type(exc).__name__} {str(exc)[:80]}")
        ok, a, b = False, {}, {}
    return {"cell_id": cell_id, "alt_ok": ok, "alt_source": s, **a}, {"cell_id": cell_id, **b}


def second_dem(cells: pd.DataFrame, ctx: dict) -> pd.DataFrame:
    """Same descriptors and rule from NASADEM / ArcticDEM (cross_dem.alt_chip), all regions.
    GEE requests are I/O bound: fetched on 8 threads (same chips, same order of results)."""
    from concurrent.futures import ThreadPoolExecutor

    _ee()  # initialise once before the threads start
    rows = list(cells[["cell_id", "lat", "lon"]].itertuples(index=False, name=None))
    with ThreadPoolExecutor(max_workers=8) as ex:
        res = list(ex.map(_alt_one, rows))
    e30, e60 = pd.DataFrame([x for x, _ in res]), pd.DataFrame([y for _, y in res])
    good = e30[e30["alt_ok"]].reset_index(drop=True)
    if not len(good):
        return pd.DataFrame(columns=["cell_id", "target_id", "robust_alt"])
    sc = lr.score_cells(ctx, good, e60)
    return (sc[["cell_id", "target_id", "robust"]].rename(columns={"robust": "robust_alt"})
            .merge(good[["cell_id", "alt_source", "frac_gt8", "frac_gt20"]].rename(
                columns={"frac_gt8": "frac_gt8_alt", "frac_gt20": "frac_gt20_alt"}), on="cell_id"))


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--n", type=int, default=160, help="new open-country cells to score")
    ap.add_argument("--workers", type=int, default=12)
    ap.add_argument("--web-only", action="store_true", help="rewrite access.json from the saved tables")
    a = ap.parse_args()
    if a.web_only:
        new = pd.read_parquet(OUT_NEW)
        doc = json.loads(OUT_WEB.read_text(encoding="utf-8"))
        write_web(pd.read_parquet(OUT_LEADS), new, lr.context(), doc["pool"]["open_not_scored_before"],
                  doc["pool"]["coarse_ranked"])
        return

    pool = coarse_pool()
    earth = pd.read_parquet(DERIVED / "earth_L1.parquet")
    null2 = pd.read_parquet(DERIVED / "earth_L1_null2.parquet")
    scored_before = set(earth["cell_id"]) | set(null2["cell_id"])
    prev = pd.read_parquet(DERIVED / "l1_regions.parquet")  # earlier cells x six regions
    lookup = pd.concat([pool[["cell_id", "lat", "lon"]],
                        prev[["cell_id", "lat", "lon"]].drop_duplicates("cell_id")],
                       ignore_index=True).drop_duplicates("cell_id")
    print(f"country lookup for {len(lookup)} cells ...")
    lookup["country"] = countries(lookup).to_numpy()
    cmap = dict(zip(lookup["cell_id"], lookup["country"], strict=True))
    pool["country"] = pool["cell_id"].map(cmap)
    open_pool = pool[~pool["country"].isin(EXCLUDED + ["unknown"])
                     & ~pool["cell_id"].isin(scored_before)]
    pick = _nms_30km(open_pool.head(1200), "d_coarse").nsmallest(a.n, "d_coarse")
    print(f"open pool {len(open_pool)} of {len(pool)}; scoring {len(pick)} new cells "
          f"(coarse rank {int(pick['coarse_rank'].min())}-{int(pick['coarse_rank'].max())})")

    rows = list(pick[["cell_id", "lat", "lon", "in_exclusion_buffer"]].itertuples(index=False,
                                                                                 name=None))
    with ProcessPoolExecutor(max_workers=a.workers) as ex:
        out = list(ex.map(_one, rows, chunksize=2))
    e30 = pd.DataFrame([x for x, _ in out])
    e60 = pd.DataFrame([y for _, y in out])
    print(f"descriptors: {e30['qa_flag'].str.slice(0, 12).value_counts().to_dict()}")
    ok = e30[e30["qa_flag"].eq("ok")].reset_index(drop=True)

    ctx = lr.context()
    sc = lr.score_cells(ctx, ok, e60)
    keep = ["cell_id", "lat", "lon", "elev_m", "frac_gt8", "frac_gt20", "slope_p50",
            "in_exclusion_buffer"]
    new = (sc.merge(ok[keep], on="cell_id")
           .merge(pick[["cell_id", "coarse_rank", "d_coarse", "country"]], on="cell_id")
           .assign(source="access screen (new)"))
    new.to_parquet(OUT_NEW, index=False)

    # earlier cells in open countries that already pass (re-read, not re-scored)
    old = prev[prev["robust"]].copy()
    old["country"] = old["cell_id"].map(cmap)
    old = old[~old["country"].isin(EXCLUDED + ["unknown"])]
    fine = pd.concat([earth, null2], ignore_index=True).drop_duplicates("cell_id")
    old = old.merge(fine[["cell_id", "frac_gt8", "frac_gt20", "slope_p50"]], on="cell_id",
                    how="left")
    old["source"] = old["sample_role"].map({"rank": "published screen", "seed": "seed",
                                            "control": "classic analog site", "extra": "extra point",
                                            "null": "random sample", "null2": "random sample"})
    leads = pd.concat([new[new["robust"]], old], ignore_index=True)
    print(f"open-country passes: {len(leads)} rows, {leads['cell_id'].nunique()} cells")

    cells = leads.drop_duplicates("cell_id")[["cell_id", "lat", "lon"]].reset_index(drop=True)
    if len(cells):
        alt = second_dem(cells, ctx)
        leads = leads.merge(alt, on=["cell_id", "target_id"], how="left")
        leads = leads.merge(worldcover_shares(cells), on="cell_id", how="left")
    leads.to_parquet(OUT_LEADS, index=False)
    write_web(leads, new, ctx, len(open_pool), len(pool))


def write_web(leads: pd.DataFrame, new: pd.DataFrame, ctx: dict, n_open: int, n_pool: int) -> None:
    lens = io.load_lenses()["L1"]
    leads = leads[~leads["country"].isin(EXCLUDED + ["unknown"])]
    t = ctx["targets"].set_index("footprint_id")
    regions = []
    for site, ref in ctx["refs"].items():
        tr = t.loc[ref]
        d = leads[leads["target_id"].eq(site)].copy()
        d["stable"] = d["robust_alt"].map({True: "yes", False: "no"}).fillna("not checked")
        d["ice_excluded"] = d["snow_ice_frac"].fillna(0) > ICE_MAX
        d["usable"] = d["stable"].eq("yes") & ~d["ice_excluded"]
        d["traverse_km"] = 10.0 * float(tr["frac_gt8"]) / d["frac_gt8"].clip(lower=1e-6)
        d = d.sort_values(["usable", "stable", "frac_gt8"], ascending=[False, False, False])
        regions.append({
            "id": site, "label": REGION_LABEL.get(site, site), "reference": "published"
            if site in PUBLISHED else "medoid (exploratory)",
            "target_frac_gt8": round(float(tr["frac_gt8"]), 4),
            "target_frac_gt20": round(float(tr["frac_gt20"]), 4),
            "new_scored": int(new["target_id"].eq(site).sum()),
            "new_pass": int((new["target_id"].eq(site) & new["robust"]).sum()),
            "leads": [{k: (None if (isinstance(v, float) and not np.isfinite(v)) else v)
                       for k, v in {
                "cell_id": r.cell_id, "lat": round(float(r.lat), 4), "lon": round(float(r.lon), 4),
                "country": r.country, "source": r.source,
                "frac_gt8": round(float(r.frac_gt8), 4), "frac_gt20": round(float(r.frac_gt20), 4),
                "traverse_km": round(float(r.traverse_km), 1),
                "second_dem": r.stable, "second_dem_source": getattr(r, "alt_source", None),
                "snow_ice_frac": None if pd.isna(r.snow_ice_frac) else round(float(r.snow_ice_frac), 3),
                "water_frac": None if pd.isna(r.water_frac) else round(float(r.water_frac), 3),
                "known_analog_area": bool(r.in_exclusion_buffer),
                "ice_excluded": bool(r.ice_excluded), "usable": bool(r.usable),
            }.items()} for r in d.itertuples()],
        })
    doc = {"generated": dt.datetime.now().strftime("%Y-%m-%d %H:%M"),
           "status": "exploratory leads (post hoc), not verdicts",
           "rule": "unchanged L1 robust set: native rank >= n/2 in all three configurations",
           "dem": "Copernicus GLO-30; second DEM NASADEM (60S-60N) or ArcticDEM (>60N)",
           "usable_rule": f"holds with the second DEM and WorldCover snow/ice share <= {ICE_MAX} (the published sites' ice rule)",
           "excluded_countries": EXCLUDED,
           "excluded_reason": ("China: Wolf Amendment bars NASA bilateral activity; Russia and "
                               "countries under comprehensive US sanctions treated as closed. "
                               "An assumption for planning, not a legal opinion."),
           "pool": {"coarse_ranked": n_pool, "open_not_scored_before": n_open,
                    "new_scored": int(new["cell_id"].nunique())},
           "lens_descriptors": lens["descriptors"], "regions": regions}
    OUT_WEB.write_text(json.dumps(doc, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"wrote {OUT_WEB.relative_to(io.REPO_ROOT)}")
    for r in regions:
        st = sum(1 for x in r["leads"] if x["second_dem"] == "yes")
        us = sum(1 for x in r["leads"] if x["usable"])
        print(f"  {r['label']:24s} leads {len(r['leads']):3d}  stable with 2nd DEM {st:3d}  usable {us:3d}  "
              f"(new: {r['new_pass']}/{r['new_scored']})")


if __name__ == "__main__":
    main()
