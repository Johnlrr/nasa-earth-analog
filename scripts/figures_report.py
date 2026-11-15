"""A9 — figures for docs/validation_report.md, drawn only from pipeline tables.

fig_target_scarcity.png : usable engine-kept cells per lens x target (A18, target_scarcity)
fig_sites_map.png       : engine-kept cells by lens + X1 TRANSFERS cells, showcase sites named
fig_m1_stop_rule.png    : M1 largest matched patch per site vs the pre-registered 0.1 km² rule
fig_mission_slopes.png  : 8° / 20° slope shares vs the Artemis III requirements (PLAN 2d)
fig_transfer_matrix.png : lens x test variable, three states (PLAN 2d)
fig_region_matrix.png   : six PGDA 78 regions x Earth footprints (PLAN 2e, exploratory)

Palette: dataviz reference categorical slots 1-4 in fixed order (L1 blue, L2 orange, L1+L2 aqua,
X1 yellow), validated light mode; slots 3-4 are below 3:1 contrast, so every series also has its
own marker shape and a legend. Land silhouette: ETOPO1 > 0 m via Google Earth Engine, cached in
data/raw/review/land_mask.png (skipped when unavailable).

Usage: python scripts/figures_report.py
"""

from __future__ import annotations

import json
import os

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import pandas as pd  # noqa: E402

from similitude import io  # noqa: E402

DERIVED = io.REPO_ROOT / "data" / "derived"
FIG = io.REPO_ROOT / "docs" / "figures"
LAND = io.REPO_ROOT / "data" / "raw" / "review" / "land_mask.png"
SURFACE, INK, INK2, GRID = "#fcfcfb", "#1f1f1e", "#5c5b55", "#e4e3de"
SERIES = {"L1": "#2a78d6", "L2": "#eb6834", "L1,L2": "#1baf7a", "X1": "#eda100"}
MARKER = {"L1": "o", "L2": "s", "L1,L2": "D", "X1": "^"}


def style(ax):
    ax.set_facecolor(SURFACE)
    for s in ("top", "right"):
        ax.spines[s].set_visible(False)
    for s in ("left", "bottom"):
        ax.spines[s].set_color(GRID)
    ax.tick_params(colors=INK2, labelsize=9)
    ax.xaxis.label.set_color(INK2)
    ax.yaxis.label.set_color(INK2)


def fig_scarcity():
    s = pd.read_parquet(DERIVED / "target_scarcity.parquet")
    s = s.sort_values(["lens_id", "n_usable_not_downgraded"])
    labels = [f"{r.lens_id} · {r.target_label}" for r in s.itertuples()]
    fig, ax = plt.subplots(figsize=(10, 3.2), facecolor=SURFACE)
    style(ax)
    y = range(len(s))
    ax.barh(y, s["n_usable_not_downgraded"], height=0.55, color=SERIES["L1"])
    for yi, v, tot, un in zip(y, s["n_usable_not_downgraded"], s["n_transfers"],
                              s["n_usable_b10_unreviewed"], strict=True):
        txt = f"{v}  (of {tot} TRANSFERS; {un} not yet B10-reviewed)"
        ax.text(v + 1, yi, txt, va="center", fontsize=9, color=INK)
    ax.set_yticks(list(y), labels)
    ax.set_xlabel("usable engine-kept cells (ice filter, not B10-downgraded)")
    ax.grid(axis="x", color=GRID, lw=0.8)
    ax.set_axisbelow(True)
    ax.set_xlim(0, s["n_usable_not_downgraded"].max() * 2.0)
    fig.suptitle("Within 307 scored cells, Connecting Ridge terrain is rare on Earth",
                 x=0.02, ha="left", fontsize=11, color=INK)
    fig.tight_layout()
    fig.savefig(FIG / "fig_target_scarcity.png", dpi=150, facecolor=SURFACE)
    plt.close(fig)


def land_mask():
    if LAND.exists():
        return plt.imread(LAND)
    try:
        import ee
        import requests

        ee.Initialize(project=os.environ["EE_PROJECT"])
        img = ee.Image("NOAA/NGDC/ETOPO1").select("bedrock").gt(0).selfMask()
        url = img.getThumbURL({"region": ee.Geometry.Rectangle([-180, -90, 180, 90], None, False),
                               "dimensions": "1440x720", "format": "png",
                               "palette": ["e6e5e0"], "crs": "EPSG:4326"})
        LAND.parent.mkdir(parents=True, exist_ok=True)
        LAND.write_bytes(requests.get(url, timeout=120).content)
        return plt.imread(LAND)
    except Exception as exc:  # basemap is decoration only
        print(f"land mask unavailable ({type(exc).__name__}); map drawn without it")
        return None


def fig_map():
    cells = pd.read_parquet(DERIVED / "site_cells.parquet")
    cells = cells[cells["site_id"].notna()]
    sites = pd.read_parquet(DERIVED / "sites.parquet")
    show = sites[sites["showcase"].ne("")]
    v = pd.read_parquet(DERIVED / "verdicts.parquet")
    x1 = pd.read_parquet(DERIVED / "x1_checklist.parquet").set_index("cell_id")
    xt = v.loc[v["lens_id"].eq("X1") & v["state"].eq("TRANSFERS")
               & v["cell_id"].fillna("").ne(""), "cell_id"].unique()
    fig, ax = plt.subplots(figsize=(11, 5.6), facecolor=SURFACE)
    style(ax)
    land = land_mask()
    if land is not None:
        ax.imshow(land, extent=(-180, 180, -90, 90), zorder=0)
    for key in ("L1", "L2", "L1,L2"):
        d = cells[cells["lenses"].eq(key)]
        ax.scatter(d["lon"], d["lat"], s=28, marker=MARKER[key], color=SERIES[key],
                   edgecolor=SURFACE, linewidth=0.8, zorder=3,
                   label={"L1": "L1 terrain", "L2": "L2 shadows", "L1,L2": "L1 + L2"}[key]
                   + f" ({len(d)})")
    ax.scatter(x1.loc[xt, "lon"], x1.loc[xt, "lat"], s=46, marker=MARKER["X1"],
               color=SERIES["X1"], edgecolor=INK2, linewidth=0.6, zorder=3,
               label=f"X1 ice configuration, semiquant ({len(xt)})")
    # Zanda and Jebel Akhdar sit next to the Tibet/Oman cell clusters: push their labels clear
    offset = {"Zanda": (-10, 18), "Jebel Akhdar": (-20, -22)}
    for r in show.itertuples():
        label = r.name.split(",")[0].split(" (")[0]
        dx, dy = next((o for k, o in offset.items() if label.startswith(k)), (6, 6))
        ax.annotate(label, (r.lon, r.lat), xytext=(dx, dy), textcoords="offset points",
                    fontsize=8.5, color=INK, zorder=4, ha="right" if dx < 0 else "left",
                    arrowprops=None if (dx, dy) == (6, 6) else {"arrowstyle": "-", "color": INK2,
                                                                 "lw": 0.6})
    ax.set_xlim(-180, 180)
    ax.set_ylim(-60, 90)
    ax.set_xlabel("longitude (°)")
    ax.set_ylabel("latitude (°)")
    ax.grid(color=GRID, lw=0.6)
    ax.set_axisbelow(True)
    ax.legend(loc="lower left", fontsize=8.5, frameon=False, labelcolor=INK)
    ax.set_title("Engine-kept cells (ice-excluded removed) and showcase sites (labelled)",
                 loc="left", fontsize=11, color=INK)
    fig.tight_layout()
    fig.savefig(FIG / "fig_sites_map.png", dpi=150, facecolor=SURFACE)
    plt.close(fig)


def fig_m1():
    j = json.loads((DERIVED / "m1_stop_rule.json").read_text(encoding="utf-8"))
    rule = 0.1
    rows = []
    for k, val in j["largest_patch_km2"].items():
        role = "control" if k.startswith("ctl_lake") else ("decoy" if k.startswith("ctl_")
                                                           else "seed")
        rows.append((k.replace("ctl_", "").replace("seed_", "").replace("__", " "), role, val))
    d = pd.DataFrame(rows, columns=["site", "role", "km2"]).sort_values("km2")
    floor = 1e-3
    colors = {"control": SERIES["L1"], "decoy": SERIES["L2"], "seed": SERIES["L1,L2"]}
    fig, ax = plt.subplots(figsize=(8, 3.8), facecolor=SURFACE)
    style(ax)
    y = range(len(d))
    ax.barh(y, [max(v, floor) for v in d["km2"]], height=0.55,
            color=[colors[r] for r in d["role"]], left=0)
    for yi, v in zip(y, d["km2"], strict=True):
        ax.text(max(v, floor) * 1.15, yi, "0" if v == 0 else f"{v:.3g}", va="center",
                fontsize=8.5, color=INK)
    ax.set_xscale("log")
    ax.set_xlim(floor * 0.8, 100)
    ax.axvline(rule, color=INK2, lw=1.2, ls="--")
    ax.text(rule * 1.1, len(d) - 0.4, "pass ≥ 0.1 km² (pre-registered)", fontsize=8.5,
            color=INK2, va="top")
    ax.set_yticks(list(y), d["site"])
    ax.set_xlabel("largest matched patch vs Jezero margin (km², log; 0 drawn at 0.001)")
    handles = [plt.Rectangle((0, 0), 1, 1, color=c) for c in colors.values()]
    ax.legend(handles, ["positive control", "decoy", "seed"], loc="lower right", fontsize=8.5,
              frameon=False, labelcolor=INK)
    ax.set_title(f"M1 stop rule: {j['verdict']} — Lake Salda is not reproduced at pixel scale",
                 loc="left", fontsize=11, color=INK)
    fig.tight_layout()
    fig.savefig(FIG / "fig_m1_stop_rule.png", dpi=150, facecolor=SURFACE)
    plt.close(fig)


def fig_mission_slopes():
    """Artemis III slope readings: Moon target, engine matches, classic lunar-analog controls."""
    c = pd.read_parquet(DERIVED / "mission_criteria.parquet").iloc[::-1].reset_index(drop=True)
    color = {"Moon target": INK, "Engine match": SERIES["L1"], "Classic analog": SERIES["L2"]}
    label = [str(n if isinstance(n, str) and n else i).split(",")[0][:34]
             for n, i in zip(c["name"], c["id"], strict=True)]
    fig, axes = plt.subplots(1, 2, figsize=(11, 4.2), facecolor=SURFACE, sharey=True)
    panels = [("frac_gt8", "share of 4 km footprint steeper than 8° (30 m baseline)", 0),
              ("frac_gt20", "share steeper than 20° (30 m baseline)", 1)]
    for ax, (col, title, nd) in zip(axes, panels, strict=True):
        style(ax)
        lo, hi = c[f"range_lo_{col}"].iloc[0], c[f"range_hi_{col}"].iloc[0]
        ax.axvspan(100 * lo, 100 * hi, color=GRID, zorder=0)
        y = range(len(c))
        ax.barh(y, 100 * c[col], height=0.6, color=[color[g] for g in c["group"]], zorder=2)
        for yi, v in zip(y, c[col], strict=True):
            ax.text(100 * v + 1, yi, f"{100 * v:.{nd}f} %", va="center", fontsize=8.5,
                    color=INK, zorder=3)
        ax.set_yticks(list(y), label)
        ax.set_xlim(0, 100)
        ax.set_xlabel(title)
        ax.grid(axis="x", color=GRID, lw=0.6)
        ax.set_axisbelow(True)
    handles = [plt.Rectangle((0, 0), 1, 1, color=v) for v in color.values()]
    handles.append(plt.Rectangle((0, 0), 1, 1, color=GRID))
    n_fp = int(c["n_target_footprints"].iloc[0])
    axes[1].legend(handles, [*color.keys(), f"range of the {n_fp} Connecting Ridge footprints"],
                   loc="lower right", fontsize=8.5, frameon=False, labelcolor=INK)
    fig.suptitle("Consistency check, same formula on both worlds: the footprints of six classic "
                 "analog sites are flatter than Connecting Ridge", x=0.01, ha="left",
                 fontsize=11, color=INK)
    fig.text(0.01, 0.005, "8° and 20° are the values of NASA's Artemis III landing-map contour "
             "and EVA slope limit; NASA does not state its slope baseline, so this compares "
             "Earth with Moon only. The engine selects on these shares.", fontsize=7.5,
             color=INK2, ha="left", va="bottom")
    fig.tight_layout(rect=(0, 0.04, 1, 1))
    fig.savefig(FIG / "fig_mission_slopes.png", dpi=150, facecolor=SURFACE)
    plt.close(fig)


def fig_transfer_matrix():
    """The test-transfer matrix: one cell per lens x test variable, three states, text in cell."""
    import sys

    sys.path.insert(0, str(io.REPO_ROOT / "scripts"))
    import mission_value as mv

    cov = mv.coverage(pd.read_parquet(DERIVED / "verdicts.parquet"))
    cov = cov[cov["lens_id"].ne("M1")]  # stop rule FAIL: M1 publishes no site, no cells drawn
    lenses = ["L1", "L2", "M1", "X1"]
    order = cov.assign(r=cov["state"].map({s: i for i, s in enumerate(mv.STATE_ORDER)}))
    variables = list(order.sort_values(["r", "variable"])["variable"].drop_duplicates())
    state = {(r.lens_id, r.variable): (r.state, isinstance(r.facility, str) and bool(r.facility))
             for r in cov.itertuples()}
    look = {"TRANSFERS": (SERIES["L1"], "field", SURFACE),
            "NO-ANALOG": (SERIES["L2"], "facility", INK), "UNOBSERVED": ("#c9c8c2", "?", INK)}
    fig, ax = plt.subplots(figsize=(8.2, 0.34 * len(variables) + 1.6), facecolor=SURFACE)
    ax.set_facecolor(SURFACE)
    for yi, var in enumerate(variables):
        for xi, lens in enumerate(lenses):
            if (lens, var) not in state:
                continue
            s, has_facility = state[(lens, var)]
            col, txt, ink = look[s]
            if s == "NO-ANALOG" and not has_facility:
                txt = "no analog"
            ax.add_patch(plt.Rectangle((xi + 0.04, yi + 0.08), 0.92, 0.84, color=col))
            ax.text(xi + 0.5, yi + 0.5, txt, ha="center", va="center", fontsize=8, color=ink)
    xm = lenses.index("M1")
    ax.add_patch(plt.Rectangle((xm + 0.04, 0.08), 0.92, len(variables) - 0.16, color=GRID))
    ax.text(xm + 0.5, len(variables) / 2, "stop rule FAIL: no site published, no verdict shown",
            rotation=90, ha="center", va="center", fontsize=8.5, color=INK2)
    ax.set_xlim(0, len(lenses))
    ax.set_ylim(len(variables), 0)
    ax.set_xticks([i + 0.5 for i in range(len(lenses))],
                  ["L1 terrain\n(Moon)", "L2 low Sun\n(Moon)", "M1 minerals\n(Mars)",
                   "X1 ice\n(Mars)"])
    ax.xaxis.tick_top()
    ax.set_yticks([i + 0.5 for i in range(len(variables))],
                  [v.replace("_", " ")[:44] + (" *" if v == "day_night_cycle" else "")
                   for v in variables])
    ax.tick_params(length=0, colors=INK2, labelsize=8.5)
    for s in ax.spines.values():
        s.set_visible(False)
    handles = [plt.Rectangle((0, 0), 1, 1, color=look[s][0]) for s in mv.STATE_ORDER]
    ax.legend(handles, ["TRANSFERS: test it in the field",
                        "NO-ANALOG: not reproduced on Earth; the card names the facility",
                        "UNOBSERVED: this engine cannot say",
                        ], loc="upper center",
              bbox_to_anchor=(0.5, -0.02), ncol=1, fontsize=8.5, frameon=False, labelcolor=INK)
    fig.suptitle("Test-transfer matrix: which rows of a field test come home valid",
                 x=0.01, ha="left", fontsize=11, color=INK)
    fig.text(0.01, 0.005, "* planet-level ledger row (a Mars sol is 24.6 h): the polar ice sites "
             "do not reproduce it in the midnight-sun field season.", fontsize=7.5, color=INK2,
             ha="left", va="bottom")
    fig.tight_layout()
    fig.savefig(FIG / "fig_transfer_matrix.png", dpi=150, facecolor=SURFACE)
    plt.close(fig)


def fig_region_matrix():
    """Six PGDA 78 regions x Earth footprints: the binding native rank and the robust verdict."""
    s = pd.read_parquet(DERIVED / "l1_regions.parquet")
    crit = pd.read_parquet(DERIVED / "mission_criteria.parquet")
    crit = crit[crit["group"].ne("Moon target")]
    regions = ["connecting_ridge", "de_gerlache_rim", "peak_near_shackleton", "nobile_rim_1",
               "malapert_massif", "shackleton_rim"]
    labels = ["Connecting\nRidge", "de Gerlache\nrim *", "peak near\nShackleton *",
              "Nobile\nrim 1 *", "Malapert\nmassif *", "Shackleton\ninner wall"]
    fig, ax = plt.subplots(figsize=(9.2, 0.46 * len(crit) + 1.9), facecolor=SURFACE)
    ax.set_facecolor(SURFACE)
    for yi, r in enumerate(crit.itertuples()):
        for xi, reg in enumerate(regions):
            d = s[s["cell_id"].eq(r.id) & s["target_id"].eq(reg)]
            if d.empty:
                continue
            d = d.iloc[0]
            frac = min(d["nr_i"] / d["n_i"], d["nr_ii"] / d["n_ii"], d["nr_iii"] / d["n_iii"])
            ok = bool(d["robust"])
            ax.add_patch(plt.Rectangle((xi + 0.04, yi + 0.08), 0.92, 0.84,
                                       color=SERIES["L1"] if ok else GRID))
            ax.text(xi + 0.5, yi + 0.5, f"{100 * frac:.0f} %" + (" ✓" if ok else ""),
                    ha="center", va="center", fontsize=8.5, color=SURFACE if ok else INK2)
    ax.set_xlim(0, len(regions))
    ax.set_ylim(len(crit), 0)
    ax.set_xticks([i + 0.5 for i in range(len(regions))], labels)
    ax.xaxis.tick_top()
    ax.set_yticks([i + 0.5 for i in range(len(crit))],
                  [f"{str(n).split(',')[0][:30]}" for n in crit["name"]])
    ax.tick_params(length=0, colors=INK2, labelsize=8.5)
    for sp in ax.spines.values():
        sp.set_visible(False)
    fig.suptitle("Which Artemis III candidate region does each Earth footprint stand in for?",
                 x=0.01, ha="left", fontsize=11, color=INK)
    fig.text(0.01, 0.005, "Cell value: the lowest of the three native ranks, as a share of the "
             "lunar population (the rule needs 50 % in all three; ✓ = in the robust set).\n"
             "* medoid reference, exploratory: not a published verdict. First two rows: the "
             "engine's ridge matches; other rows: classic analog field sites.", fontsize=7.5,
             color=INK2, ha="left", va="bottom")
    fig.tight_layout(rect=(0, 0.07, 1, 1))
    fig.savefig(FIG / "fig_region_matrix.png", dpi=150, facecolor=SURFACE)
    plt.close(fig)


def main() -> None:
    FIG.mkdir(parents=True, exist_ok=True)
    fig_scarcity()
    fig_map()
    fig_m1()
    fig_mission_slopes()
    fig_transfer_matrix()
    fig_region_matrix()
    print(f"figures -> {FIG}")


if __name__ == "__main__":
    main()
