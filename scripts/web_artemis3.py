"""A6: web/data/artemis3.json for web/artemis3.html, from artemis3_lens.json,
artemis3_campaigns.json and mars_base_lens.json (no number is computed in the page).

Usage: python scripts/web_artemis3.py
       (after artemis3_lens.py, campaign_cover.py, mars_base_lens.py)
"""
from __future__ import annotations

import json

from similitude import io

D = io.REPO_ROOT / "data" / "derived"
OUT = io.REPO_ROOT / "web" / "data" / "artemis3.json"


def main() -> None:
    a3 = json.loads((D / "artemis3_lens.json").read_text())
    camp = json.loads((D / "artemis3_campaigns.json").read_text())
    mb = json.loads((D / "mars_base_lens.json").read_text())
    regions = []
    for rid, r in a3["regions"].items():
        ref = r["reference"]
        regions.append({
            "id": rid, "name": r["name"], "pgda": r["pgda"],
            "ref": {k: ref[k] for k in ("lat", "lon", "slope_p50", "frac_gt8", "frac_gt20")},
            "n_neighbours": r["n_neighbours"], "nasa_slope_diff": r["nasa_check"]["abs_diff_p50"],
            "null": r["null"], "null_ci": r["null_ci"], "classic": r["classic"],
            "classic_per_site": r["classic_per_site"],
            "open_matches": r["open_matches"],
            "campaign": {k: camp[rid][k] for k in ("sites", "field_rows_covered",
                                                   "field_rows_total", "uncovered", "facilities")}})
    out = {"prereg": a3["prereg"], "sanity_tau": [a3["sanity_site01_route_tau"], a3["v2_tau"]],
           "regions": regions, "not_run": a3["not_run"],
           "mars_base": {k: mb[k] for k in ("prereg", "n_neighbours", "null_terrain",
                                            "null_terrain_share", "classic_terrain",
                                            "null_terrain_and_x1", "terrain_countries",
                                            "exploratory_thin_threshold")}
           | {"target": {k: mb["target"][k] for k in ("name", "dtm", "slope_p50", "frac_gt8")}}}
    OUT.write_text(json.dumps(out, indent=1, ensure_ascii=False), encoding="utf-8")
    print(f"wrote {OUT.relative_to(io.REPO_ROOT)}: {len(regions)} regions")


if __name__ == "__main__":
    main()
