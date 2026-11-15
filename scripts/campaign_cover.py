"""A5: campaign cards for the Artemis III regions (exploratory composition of tested rows).

For each region of artemis3_lens.json, the field rows an Earth site can cover are
  terrain   slope AND simulated-route match (pre-registered A3 test, GLO-30)
  low_sun   a seasonal window with every daylight minute of the Sun below 7 deg (geometric model)
and the remaining rows go to named facilities (gravity offload, vacuum, thermal, dust) as in the
Connecting Ridge card (Deviations 35). Sites are chosen by greedy set cover; ties are broken by
the longer low-Sun window, then by the smaller route distance.

Outputs: data/derived/artemis3_campaigns.json
Usage  : python scripts/campaign_cover.py   (after scripts/artemis3_lens.py)
"""
from __future__ import annotations

import json

from similitude import io

D = io.REPO_ROOT / "data" / "derived"
FIELD_ROWS = ("terrain", "low_sun")
FACILITY_ROWS = {"partial gravity": "offload rig (1/6 g)",
                 "vacuum and thermal": "thermal-vacuum chamber",
                 "lunar dust": "regolith-simulant facility",
                 "rocks and craters < 60 m": "field survey at the chosen site"}


def greedy_cover(sites: list[dict], rows: tuple[str, ...]) -> tuple[list[dict], set[str]]:
    """Pick sites until every coverable row is covered. Each site: {'id', 'rows', 'window', 'd'}."""
    left, chosen = set(rows), []
    pool = list(sites)
    while left:
        best = max(pool, key=lambda s: (len(left & s["rows"]), s.get("window", 0), -s.get("d", 0)),
                   default=None)
        if best is None or not (left & best["rows"]):
            break
        chosen.append(best)
        left -= best["rows"]
        pool.remove(best)
    return chosen, left


def main() -> None:
    a3 = json.loads((D / "artemis3_lens.json").read_text())
    out = {}
    for rid, r in a3["regions"].items():
        sites = [{"id": m["cell_id"], "country": m["country"], "lat": m["lat"], "lon": m["lon"],
                  "rows": {"terrain"} | ({"low_sun"} if m["low_sun_window_days"] > 0 else set()),
                  "window": m["low_sun_window_days"], "d": m["D_route"],
                  "frac_gt20": m["frac_gt20"]} for m in r["open_matches"]]
        chosen, uncovered = greedy_cover(sites, FIELD_ROWS)
        out[rid] = {"name": r["name"], "n_candidate_sites": len(sites),
                    "sites": [{k: s[k] for k in ("id", "country", "lat", "lon", "window", "d",
                                                 "frac_gt20")} | {"rows": sorted(s["rows"])}
                              for s in chosen],
                    "field_rows_covered": len(FIELD_ROWS) - len(uncovered),
                    "field_rows_total": len(FIELD_ROWS), "uncovered": sorted(uncovered),
                    "facilities": FACILITY_ROWS}
    (D / "artemis3_campaigns.json").write_text(json.dumps(out, indent=2))
    for rid, c in out.items():
        print(rid, c["field_rows_covered"], "/", c["field_rows_total"],
              [(s["country"], s["window"]) for s in c["sites"]])


if __name__ == "__main__":
    main()
