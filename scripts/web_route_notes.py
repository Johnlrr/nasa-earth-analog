"""Carry the registered route-test result (V2 threshold, config/prereg_v2_mars.yaml) to the web.

- web/data/candidates.geojson: sites whose member cells include a Connecting Ridge slope match
  get a `route_test` sentence (reproduces the ridge's simulated routes on one/two DEMs, or not).
- web/data/access.json: Connecting Ridge leads get route fields from the V2 threshold.
Run after scripts/v2_mars.py and after any regeneration of either web file.
"""
from __future__ import annotations

import json

import pandas as pd

from similitude import io

D = io.REPO_ROOT / "data" / "derived"
WEB = io.REPO_ROOT / "web" / "data"


def main() -> None:
    v = pd.read_parquet(D / "route_v2.parquet")
    pas = v[v.group.eq("passer")].set_index("cell_id")
    alt = v[v.group.eq("passer_alt")].set_index("cell_id")

    def sentence(cid: str) -> str:
        a = bool(pas.loc[cid, "reproduces_v2"])
        b = bool(alt.loc[cid, "reproduces_v2"]) if cid in alt.index else None
        if a and b:
            return "reproduces the ridge's simulated traverse routes on two DEMs"
        if a:
            return "reproduces the ridge's simulated traverse routes on one DEM only"
        return "does NOT reproduce the ridge's simulated traverse routes (slope match only)"

    g = json.loads((WEB / "candidates.geojson").read_text(encoding="utf-8"))
    n = 0
    for f in g["features"]:
        p = f["properties"]
        if p.get("feature_type") != "site":
            continue
        cells = [c for c in (p.get("member_cells") or []) if c in pas.index]
        txt = "; ".join(f"{c} {sentence(c)}" for c in cells)
        p["route_test"] = (("Traverse test (pre-registered, 30 m planner): the ridge match "
                            + txt + ".") if cells else None)
        n += bool(cells)
    (WEB / "candidates.geojson").write_text(json.dumps(g, indent=1, ensure_ascii=False),
                                            encoding="utf-8")

    aw = json.loads((WEB / "access.json").read_text(encoding="utf-8"))
    m = 0
    for reg in aw["regions"]:
        if reg["id"] != "connecting_ridge":
            continue
        for lead in reg["leads"]:
            c = lead["cell_id"]
            if c in pas.index:
                lead["route_reproduces"] = bool(pas.loc[c, "reproduces_v2"])
                lead["route_reproduces_second_dem"] = (bool(alt.loc[c, "reproduces_v2"])
                                                       if c in alt.index else None)
                lead["route_D"] = round(float(pas.loc[c, "D_route_v2"]), 3)
                m += 1
    (WEB / "access.json").write_text(json.dumps(aw, indent=1, ensure_ascii=False),
                                     encoding="utf-8")
    print(f"sites with a route note: {n}; ridge leads updated: {m}")


if __name__ == "__main__":
    main()
