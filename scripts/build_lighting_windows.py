"""I1 (exploratory, Deviations 32): when does a ridge match also have the polar low Sun?

For every Earth cell that passes L1 for Connecting Ridge (the V1 passer group), the L2 sun model
(``low_sun_hours`` geometry, same 7 deg threshold) is read as a calendar: window days are days on
which ALL daylight has the Sun at or below 7 deg. Terrain-shadow fractions at 2/5/7 deg are
computed from the same DEM chip as L1 and set beside the ridge's. Joined with V1 route outcomes
and the access screen. Geometry only: no surface brightness, no snow state, no refraction.

Outputs: data/derived/lighting_windows.parquet, data/derived/lighting_windows.json; adds the route
         and window fields to the Connecting Ridge leads in web/data/access.json (run again after
         scripts/access/access_screen.py, which rewrites that file)
Usage  : python scripts/build_lighting_windows.py   (after scripts/route_validity.py)
"""
from __future__ import annotations

import json
import sys

import pandas as pd

from similitude import io
from similitude.descriptors.astro import low_sun_windows
from similitude.descriptors.terrain import terrain_descriptors

sys.path.insert(0, str(io.REPO_ROOT / "scripts"))
from gee.chip_dem import get_chip  # noqa: E402

DERIVED = io.REPO_ROOT / "data" / "derived"
EQUINOX = pd.Timestamp("2027-03-20")  # model day 0
CLOSED = {"China", "Russia"}  # same planning assumption as scripts/access/access_screen.py


def model_date(day: int | None) -> str | None:
    return None if day is None else (EQUINOX + pd.Timedelta(days=int(day))).strftime("%d %b")


def main() -> None:
    g = pd.read_csv(DERIVED / "route_groups.csv")
    rv = pd.read_parquet(DERIVED / "route_validity.parquet")
    acc = pd.read_parquet(DERIVED / "access_leads.parquet").drop_duplicates("cell_id")
    t2 = pd.read_parquet(DERIVED / "targets_L2.parquet")
    ridge = t2[t2["target_id"].eq("connecting_ridge") & t2["is_reference"].astype(bool)].iloc[0]
    passers = g[g["group"].eq("passer")]
    rows = []
    for r in passers.itertuples():
        dem, _ = get_chip(r.lat, r.lon, chip_m=10_000, res_m=30.0)
        sh = terrain_descriptors(dem, 30.0, 30.0, radius_m=6_371_000.0, footprint_m=4000.0)
        w = low_sun_windows(r.lat)
        v1 = rv[(rv["cell_id"] == r.cell_id) & rv["group"].eq("passer")].iloc[0]
        v1b = rv[(rv["cell_id"] == r.cell_id) & rv["group"].eq("passer_alt")]
        a = acc[acc["cell_id"].eq(r.cell_id)]
        country = a["country"].iloc[0] if len(a) else ("China" if r.cell_id == "E10K_453_921"
                                                       else None)
        rows.append({
            "cell_id": r.cell_id, "lat": r.lat, "lon": r.lon, "country": country,
            "open_country": country is not None and country not in CLOSED,
            "in_exclusion_buffer": bool(a["in_exclusion_buffer"].iloc[0]) if len(a) else None,
            "l1_robust_second_dem": bool(a["robust_alt"].iloc[0]) if len(a) else None,
            "snow_ice_frac": float(a["snow_ice_frac"].iloc[0]) if len(a) else None,
            "route_D": float(v1["D_route"]), "route_reproduces": bool(v1["reproduces"]),
            "route_reproduces_second_dem": bool(v1b["reproduces"].iloc[0]) if len(v1b) else None,
            **w,
            "window_from": model_date(w["window_first_day"]),
            "window_to": model_date(w["window_last_day"]),
            "shadow_e2": sh["shadow_e2"], "shadow_e5": sh["shadow_e5"],
            "shadow_e7": sh["shadow_e7"],
            "ridge_shadow_e2": float(ridge["shadow_e2"]),
            "ridge_shadow_e5": float(ridge["shadow_e5"]),
        })
    out = pd.DataFrame(rows)
    out["both_tests_and_window"] = (out["route_reproduces"]
                                    & out["route_reproduces_second_dem"].fillna(False)
                                    & (out["window_days"] > 0) & out["open_country"])
    out.to_parquet(DERIVED / "lighting_windows.parquet", index=False)
    cols = ["cell_id", "country", "route_reproduces", "route_reproduces_second_dem",
            "window_days", "window_from", "window_to", "window_lowsun_min_per_day",
            "shadow_e2", "ridge_shadow_e2", "both_tests_and_window"]
    print(out[cols].round(3).to_string())
    (DERIVED / "lighting_windows.json").write_text(json.dumps(
        json.loads(out.round(4).to_json(orient="records")), indent=2))
    web = io.REPO_ROOT / "web" / "data" / "access.json"
    acc_web = json.loads(web.read_text(encoding="utf-8"))
    by_id = out.set_index("cell_id")
    for reg in acc_web["regions"]:
        if reg["id"] != "connecting_ridge":
            continue
        for lead in reg["leads"]:
            if lead["cell_id"] not in by_id.index:
                continue
            r = by_id.loc[lead["cell_id"]]
            lead["route_reproduces"] = bool(r.route_reproduces)
            lead["route_reproduces_second_dem"] = (None if pd.isna(r.route_reproduces_second_dem)
                                                   else bool(r.route_reproduces_second_dem))
            lead["route_D"] = round(float(r.route_D), 3)
            lead["window_days"] = int(r.window_days)
            lead["window_from"] = r.window_from if isinstance(r.window_from, str) else None
            lead["window_to"] = r.window_to if isinstance(r.window_to, str) else None
    web.write_text(json.dumps(acc_web, indent=1, ensure_ascii=False), encoding="utf-8")


if __name__ == "__main__":
    main()
