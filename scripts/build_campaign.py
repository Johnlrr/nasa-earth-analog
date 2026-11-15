"""Campaign coverage for Connecting Ridge (exploratory, Deviations 35).

Reads results already published and asks the test engineer's question: which test variables does
a field campaign reproduce, at which site and in which weeks, and which go to a named facility?
Nothing is recomputed here; every cell of the matrix comes from a table.

Field variables (terrain and lighting, measurable from orbit):
  slope      L1 robust set on both DEMs                         (l1_robust_set / access_leads)
  routes     planner outcomes within the ridge neighbourhood, V2 threshold (route_v2, both DEMs;
             the registered rule switches cards to V2 because V2 H1 passed)
  low_sun    days with all daylight Sun <= 7 deg                (low_sun_windows, L2 geometry)
  shadow     terrain shadow at 2 deg within the ridge neighbourhood range (L2 descriptor)
  slope_5m   slope match at 5 m (multiscale.json; only where checked)
Always UNOBSERVED: rocks and craters under 60 m. Facility rows: the Moon Transfer Ledger.

Coverage across sites is a union per variable, never a joint test environment; joint coverage is
reported per site.

Outputs: data/derived/campaign_connecting_ridge.json, docs/figures/fig_campaign_coverage.png
"""
from __future__ import annotations

import json

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import pandas as pd  # noqa: E402

from similitude import io  # noqa: E402
from similitude.descriptors.astro import low_sun_windows  # noqa: E402

D = io.REPO_ROOT / "data" / "derived"
FIG = io.REPO_ROOT / "docs" / "figures" / "fig_campaign_coverage.png"
WEB_FIG = io.REPO_ROOT / "web" / "figures" / "fig_campaign_coverage.png"
FIELD = [("slope", "Slope distribution (30 m, two DEMs)"),
         ("routes", "Simulated routes (planner, two DEMs)"),
         ("low_sun", "All-day low Sun (≤ 7°)"),
         ("shadow", "Terrain shadow at 2° in ridge range"),
         ("slope_5m", "Slope distribution at 5 m")]
HAUGHTON = "Haughton impact structure, Devon Island"


def sites() -> list[dict]:
    lw = pd.read_parquet(D / "lighting_windows.parquet").set_index("cell_id")
    t2 = pd.read_parquet(D / "targets_L2.parquet")
    nat = t2[t2.target_id.eq("connecting_ridge")]
    lo, hi = float(nat.shadow_e2.min()), float(nat.shadow_e2.max())
    ms = json.loads((D / "multiscale.json").read_text(encoding="utf-8"))["leads"]
    v2 = pd.read_parquet(D / "route_v2.parquet")

    def rep(cid, grp):
        return bool(v2[(v2.cell_id == cid) & v2.group.eq(grp)].reproduces_v2.iloc[0])

    out = []
    for cid, name in (("E10K_-355_-671", "Argentina lead"),
                      ("E10K_660_-632", "Baffin Island lead")):
        r = lw.loc[cid]
        m5 = ms.get(cid, {}).get("scales", {}).get("5")
        out.append({
            "id": cid, "name": name, "lat": float(r.lat), "lon": float(r.lon), "kind": "lead",
            "slope": bool(r.l1_robust_second_dem),
            "routes": rep(cid, "passer") and rep(cid, "passer_alt"),
            "low_sun": int(r.window_days) > 0, "window_days": int(r.window_days),
            "window": (f"{r.window_from}–{r.window_to}" if int(r.window_days) else None),
            "shadow": bool(lo <= float(r.shadow_e2) <= hi), "shadow_e2": float(r.shadow_e2),
            "slope_5m": (None if m5 is None else bool(m5["holds"])),
        })
    # best classic site for the ridge's routes: Haughton (all footprints of its 12 km block)
    st = pd.read_parquet(D / "site_stability.parquet")
    cl = st[st.group.eq("Classic analog") & st.dem.eq("GLO-30") & st.site.eq(HAUGHTON)]
    rr = v2[v2.group.eq("classic") & v2.cell_id.isin(cl.cell_id)]
    e = pd.read_parquet(D / "earth_L1.parquet").set_index("cell_id")
    sh = float(e.loc["CTRL_haughton_devon", "shadow_e2"])
    w = low_sun_windows(float(cl.lat.mean()))
    out.append({
        "id": "CTRL_haughton_devon", "name": "Haughton (classic site)", "kind": "classic",
        "lat": float(cl.lat.mean()), "lon": float(cl.lon.mean()),
        "slope": bool(cl.robust.any()),
        "routes": bool(rr.reproduces_v2.mean() >= 0.5), "routes_footprints":
            f"{int(rr.reproduces_v2.sum())}/{len(rr)}",
        "low_sun": w["window_days"] > 0, "window_days": int(w["window_days"]), "window": None,
        "shadow": bool(lo <= sh <= hi), "shadow_e2": sh, "slope_5m": None,
    })
    return out, (lo, hi)


def main() -> None:
    ss, (lo, hi) = sites()
    ledger = json.loads((io.REPO_ROOT / "web" / "data" / "ledger.json").read_text(
        encoding="utf-8"))["moon"]
    fac = [{"variable": it["variable"], "facility": it["facility"]} for it in ledger["items"]]
    gaps = [{"id": g["id"], "name": g["name"]} for g in ledger["nasa_gaps"]
            if g["id"] in ("ESDMD #0805", "ESDMD #1101")]
    keys = [k for k, _ in FIELD]

    def cov(group):
        return sum(any(s[k] for s in group) for k in keys)

    leads = [s for s in ss if s["kind"] == "lead"]
    classic = [s for s in ss if s["kind"] == "classic"]
    per_site = {s["name"]: sum(bool(s[k]) for k in keys) for s in ss}
    res = {
        "status": "exploratory (Deviations 35): composed from published tables, not a new test",
        "target": "connecting_ridge", "field_variables": [lbl for _, lbl in FIELD],
        "ridge_shadow_range": [round(lo, 3), round(hi, 3)],
        "sites": ss, "per_site_joint": per_site,
        "campaign_two_leads": cov(leads), "campaign_with_haughton": cov(ss),
        "best_classic_alone": cov(classic), "n_field": len(keys),
        "unobserved": ["rocks and craters under 60 m (site survey)"],
        "facility_rows": fac, "n_facility": len(fac), "nasa_shortfalls": gaps,
    }
    (D / "campaign_connecting_ridge.json").write_text(json.dumps(res, indent=2), encoding="utf-8")

    # figure: rows = variables (field, then facility), columns = sites
    cols = [s["name"] for s in ss]
    rows = [lbl for _, lbl in FIELD] + ["Rocks, craters < 60 m",
                                        f"{len(fac)} rows: gravity, vacuum, thermal, dust…"]
    col = {"T": "#2a7bd5", "F": "#e2662f", "N": "#f6dccd", "U": "#a9a8a0", "-": "#eceae2"}
    fig, ax = plt.subplots(figsize=(7.2, 4.6), dpi=220)
    for i, _rlab in enumerate(rows):
        for j, s in enumerate(ss):
            if i < len(keys):
                v = s[keys[i]]
                c, t = (("-", "not checked") if v is None else (("T", "yes") if v else ("N", "no")))
                if keys[i] == "low_sun" and v:
                    t = f"{s['window_days']} d"
                if keys[i] == "routes" and s["kind"] == "classic":
                    t += f" ({s['routes_footprints']})"
            elif i == len(keys):
                c, t = "U", "survey"
            else:
                c, t = "F", "named facility"
            ax.add_patch(plt.Rectangle((j, -i - 1), 0.96, 0.9, color=col[c]))
            ax.text(j + 0.48, -i - 0.55, t, ha="center", va="center", fontsize=9,
                    color="white" if c in "TF" else "#161c1a")
    ax.set_xlim(0, len(cols))
    ax.set_ylim(-len(rows) - 0.1, 0.4)
    ax.set_yticks([-i - 0.55 for i in range(len(rows))])
    ax.set_yticklabels(rows, fontsize=9)
    ax.set_xticks([j + 0.48 for j in range(len(cols))])
    ax.set_xticklabels(cols, fontsize=9.5)
    ax.xaxis.tick_top()
    ax.axhline(-len(keys) - 0.05, color="#161c1a", lw=0.8)
    for sp in ax.spines.values():
        sp.set_visible(False)
    ax.tick_params(length=0)
    ax.set_title(f"Field rows covered: two leads {res['campaign_two_leads']}/{len(keys)}, "
                 f"best classic site alone {res['best_classic_alone']}/{len(keys)}",
                 fontsize=10.5, pad=26, loc="left")
    fig.tight_layout()
    FIG.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(FIG, bbox_inches="tight", pad_inches=0.05)
    WEB_FIG.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(WEB_FIG, bbox_inches="tight", pad_inches=0.05)
    print(json.dumps({k: res[k] for k in ("per_site_joint", "campaign_two_leads",
                                          "campaign_with_haughton", "best_classic_alone",
                                          "n_field", "n_facility")}, indent=1))


if __name__ == "__main__":
    main()
