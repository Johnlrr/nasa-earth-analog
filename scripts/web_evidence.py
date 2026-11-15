# ruff: noqa: E501  (HTML template lines)
"""PLAN 2e — web/evidence.html: the checks and the mission reading, for visitors of the demo.

Static page, generated: every number is read from docs/slide_numbers.json (itself generated from
the pipeline tables) and every requirement from config/mission.yaml. Reuses web/style.css.
Figures are served from figures/ on GitHub Pages (the workflow copies docs/figures there).

Usage: python scripts/web_evidence.py
"""

from __future__ import annotations

import html
import json

from similitude import io

OUT = io.REPO_ROOT / "web" / "evidence.html"


def n(numbers: dict, key: str, fmt: str = "{}", scale: float = 1.0) -> str:
    v = numbers[key]["value"]
    return fmt.format(v * scale if scale != 1.0 else v)


def fig(name: str, alt: str, caption: str) -> str:
    return (f'<figure class="ev-fig"><img src="figures/{name}" alt="{html.escape(alt)}" '
            f"loading=\"lazy\" onerror=\"if(!this.dataset.f){{this.dataset.f=1;"
            f"this.src='../docs/figures/{name}';}}\">"
            f"<figcaption>{caption}</figcaption></figure>")


def build() -> str:
    num = json.loads((io.REPO_ROOT / "docs" / "slide_numbers.json").read_text(
        encoding="utf-8"))["numbers"]
    cfg = io.load_yaml(io.CONFIG_DIR / "mission.yaml")
    req, p = cfg["requirements"], cfg["protocols"]["L1"]
    e = html.escape
    tiles = [
        (n(num, "cr_frac_gt8", "{:.0f} %", 100) + " vs " + n(num, "classic_frac_gt8_median",
                                                              "{:.0f} %", 100),
         "of terrain steeper than 8°: the Connecting Ridge footprint against the median of six "
         "classic analog field sites, same formula on both worlds"),
        (n(num, "prevalence_connecting_ridge_pass") + " vs "
         + n(num, "prevalence_shackleton_rim_pass") + " of "
         + n(num, "prevalence_connecting_ridge_n", "{:,}"),
         "random bare-land cells pass the terrain test for the ridge and for the steep "
         "Shackleton inner wall (exact McNemar p = "
         + n(num, "prevalence_ridge_vs_wall_p_mcnemar_exact", "{:.3f}") + ")"),
        (n(num, "cross_dem_same_verdict") + " of " + n(num, "cross_dem_n"),
         "terrain verdicts unchanged when recomputed from a second, independent Earth DEM "
         "(NASADEM / ArcticDEM)"),
        (n(num, "nasa_slope_max_abs_diff_deg", "{:.4f}°"),
         "largest difference between our slope formula and NASA's PGDA 78 slope rasters on "
         "six south-pole sites"),
    ]
    tile_html = "".join(f'<div class="ev-tile"><p class="ev-num">{e(a)}</p><p>{e(b)}</p></div>'
                        for a, b in tiles)
    return f"""<!doctype html>
<html lang="en" data-type="software" data-radius="soft">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>SIMILITUDE: evidence and mission reading</title>
<meta name="description" content="Checks against known truth and the reading of the results beside published NASA Artemis III requirements.">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Host+Grotesk:wght@400..700&family=JetBrains+Mono:wght@400..500&display=swap" rel="stylesheet">
<link rel="stylesheet" href="style.css">
<style>
.ev {{ max-width: 1040px; margin: 0 auto; padding: 32px var(--gutter) 72px; }}
.ev h1 {{ font-size: var(--fs-title); letter-spacing: var(--track-title); margin: 8px 0 12px; }}
.ev h2 {{ font-size: var(--fs-xl); margin: 44px 0 10px; }}
.ev p, .ev li {{ color: var(--text); line-height: var(--lh); }}
.ev .lead {{ font-size: var(--fs-l); color: var(--muted); max-width: 62ch; }}
.ev-tiles {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(220px, 1fr)); gap: 12px; margin: 24px 0; }}
.ev-tile {{ background: var(--surface); border: 1px solid var(--line); border-radius: var(--radius-m); padding: 16px; }}
.ev-tile p {{ margin: 0; font-size: var(--fs-s); color: var(--muted); }}
.ev-tile .ev-num {{ font-family: var(--font-mono); font-size: var(--fs-xl); color: var(--accent); margin-bottom: 6px; }}
.ev-fig {{ margin: 18px 0 8px; background: #fcfcfb; border-radius: var(--radius-m); padding: 10px; overflow-x: auto; }}
.ev-fig img {{ display: block; width: 100%; min-width: 560px; height: auto; }}
.ev-fig figcaption {{ color: #5c5b55; font-size: var(--fs-xs); padding: 6px 4px 2px; }}
.ev blockquote {{ margin: 12px 0; padding: 10px 14px; border-left: 3px solid var(--accent); background: var(--accent-soft); border-radius: var(--radius-s); }}
.ev .note {{ color: var(--muted); font-size: var(--fs-s); }}
.ev a {{ color: var(--accent); }}
.ev table {{ border-collapse: collapse; width: 100%; font-size: var(--fs-s); margin: 10px 0; }}
.ev th, .ev td {{ text-align: left; padding: 7px 8px; border-bottom: 1px solid var(--line); vertical-align: top; }}
.ev th {{ color: var(--muted); font-weight: 500; }}
</style>
</head>
<body>
<header class="topbar">
  <div class="topbar-in wrap">
    <a class="brand" href="./" aria-label="SIMILITUDE home">
      <span class="brand-mark" aria-hidden="true"></span>
      <span class="brand-name">SIMILITUDE</span>
    </a>
    <p class="brand-line">Evidence and mission reading</p>
    <nav class="topnav" aria-label="Project">
      <a href="./#explorer">Explorer</a>
      <a href="validation_report.md">Validation report</a>
      <a href="test_protocols.md">Test protocols</a>
    </nav>
  </div>
</header>
<main class="ev">
<p class="eyebrow">Famous is not faithful, per test</p>
<h1>Can you trust the terrain verdicts, and what are they worth to a test team?</h1>
<p class="lead">Every number on this page is generated from the pipeline tables. None of these
checks changed a threshold or a verdict; all were run after the results were known and are
listed as deviations in the validation report.</p>
<div class="ev-tiles">{tile_html}</div>

<h2>1. Read beside NASA's Artemis III requirements</h2>
<blockquote>"{e(req['artemis3_landing_slope']['quote'])}" · "{e(req['artemis3_eva_slope']['quote'])}"
<br><span class="note">{e(req['artemis3_landing_slope']['document'])} —
<a href="{e(req['artemis3_landing_slope']['source'])}">NASA NTRS</a></span></blockquote>
<p>With one formula on both worlds, {n(num, 'cr_frac_gt8', '{:.0f} %', 100)} of the Connecting
Ridge footprint is steeper than 8°. In the 4 km footprints of {n(num, 'classic_n')} classic
analog field sites the median is {n(num, 'classic_frac_gt8_median', '{:.0f} %', 100)}, a factor
{n(num, 'classic_under_sampling_factor', '{:.1f}')} lower; in the 12 km blocks around them,
{n(num, 'stability_classic_robust')} of {n(num, 'stability_classic_n')} footprints pass the
terrain test for the ridge. About {n(num, 'traverse_km_da_qaidam', '{:.0f}')} km of traverse at
Da Qaidam meets as much terrain steeper than 8° as 10 km on the ridge; at the median classic
site it takes about {n(num, 'traverse_km_classic_median', '{:.0f}')} km; over the whole 12 km
blocks, {n(num, 'traverse_km_block_da_qaidam', '{:.0f}')} km against
{n(num, 'traverse_km_block_classic_median', '{:.0f}')} km (if the share along the path equals
the areal share; a consistency check, since the engine selects on this share).</p>
{fig('fig_mission_slopes.png', 'Shares of terrain steeper than 8 and 20 degrees for Connecting Ridge, two engine matches and six classic sites',
     e(cfg['criteria_caveat']))}

<h2>2. One Earth footprint for three south-pole sites of PGDA 78</h2>
<p>The Da Qaidam cell is in the robust set of {n(num, 'regions_matched_da_qaidam')} of the 6
PGDA 78 south-pole sites (Connecting Ridge; de Gerlache rim and the peak near Shackleton are exploratory
readings with a medoid reference) and stays there with NASA's NASADEM. It is a known Mars analog
region: {n(num, 'task_attention_da_qaidam_mars')} analog papers in a Mars context,
{n(num, 'task_attention_da_qaidam_moon')} in a Moon context. The Peary Land cell passes the
Moon terrain test and the Mars ice test at one camp, but it is marginal: with a second DEM its
rank in the strictest configuration is {n(num, 'cross_dem_peary_land_rank_full_metric')} where
the rule needs {n(num, 'rank_rule_threshold')}.</p>
{fig('fig_region_matrix.png', 'Six PGDA 78 south-pole sites against two engine matches and six classic analog sites',
     'A match is a 4 km footprint, not a region: of the 9 footprints of the 12 km block around each engine match, 1 passes with both DEMs (at Da Qaidam the cell itself; at Peary Land the footprint 4 km south, not the cell).')}

<h2>3. What a field test can and cannot bring home</h2>
<p>By this engine's measure a terrain site reproduces {n(num, 'coverage_L1_transfers')} of
{n(num, 'coverage_L1_total')} test variables; {n(num, 'coverage_L1_facility')} need a named
facility and {n(num, 'coverage_L1_unobserved')} is unobserved. No Earth site reproduces the
polar Sun: the best one has the Sun below 7° for
{n(num, 'l2_earth_best_lowsun_frac_daylight', '{:.0f} %', 100)} of daylight, the lunar target
for {n(num, 'l2_moon_lowsun_frac_daylight', '{:.0f} %', 100)}.</p>
{fig('fig_transfer_matrix.png', 'Lens by test variable matrix with three states',
     'The mineral lens failed its pre-registered stop rule: no site is published and no verdict is shown.')}
<p>Mars ice, read beside NASA's Mars Life Explorer concept study
("{e(req['mars_ice_access']['quote'])}"): all {n(num, 'x1_mission_cells')} Earth cells the ice
lens keeps have modelled ice-bearing ground within the 2 m drill reach,
{n(num, 'x1_mission_within_1m')} within 1 m. These are modelled thaw depths, not observations;
the ice lens is semi-quantitative.</p>
<table>
<tr><th>Terrain protocol</th><th></th></tr>
<tr><td>Systems to test</td><td>{e(p['systems'])}</td></tr>
<tr><td>What to measure</td><td>{e(p['measure'])}</td></tr>
<tr><td>Reproduced at a matching site</td><td>{e(p['field_credit'])}</td></tr>
<tr><td>Not reproduced</td><td>{e(p['not_credited'])}</td></tr>
</table>
<p class="note">NASA's TRL definitions ask each project for a "documented definition of relevant
environment". A site card is an input to that definition; it assigns no TRL, and no hardware
was tested here.</p>

<h2>4. Known truth</h2>
<ul>
<li>On the Moon, footprints of the Shackleton inner wall pass their own region
{n(num, 'lunar_control_wall_same_pass')} of {n(num, 'lunar_control_wall_same_n')}; footprints
of the other sites, {n(num, 'lunar_control_wall_other_pass')} of
{n(num, 'lunar_control_wall_other_n')}. Ridge, rim and massif sites are not told apart
({n(num, 'lunar_control_no_wall_same_pass')} of {n(num, 'lunar_control_no_wall_same_n')} same
site, {n(num, 'lunar_control_no_wall_other_pass')} of {n(num, 'lunar_control_no_wall_other_n')}
other sites, base rate {n(num, 'lunar_control_all_pass')} of {n(num, 'lunar_control_all_n')}):
the test recognises a terrain class, not a named place.</li>
<li>Ice lens (semi-quantitative): {n(num, 'x1_positive_pass')} of {n(num, 'x1_positive_n')}
polar-desert controls pass, one of them the calibration site;
{n(num, 'x1_decoy_rejected')} of {n(num, 'x1_decoy_n')} wet-permafrost decoys are rejected.</li>
<li>Mineral lens: {n(num, 'm1_checks_passed')} of {n(num, 'm1_checks_n')} pre-registered checks
pass; the stop rule is {n(num, 'm1_stop_rule_verdict')}, so no mineral analog is published.</li>
</ul>
<p class="note">Counts of matching cells come from a 307-cell sample screened towards Connecting
Ridge, not from a census: about {n(num, 'prevalence_connecting_ridge_cells', '{:,}')} bare-land
cells (95 % CI {n(num, 'prevalence_connecting_ridge_cells_lo', '{:,}')}–
{n(num, 'prevalence_connecting_ridge_cells_hi', '{:,}')}) would pass the terrain test for the
ridge, before the ice filter and the visual review. Full tables and the list of every rule
changed after seeing data: <a href="validation_report.md">validation report</a>.</p>
</main>
</body>
</html>
"""


def main() -> None:
    OUT.write_text(build(), encoding="utf-8")
    print(f"wrote {OUT}")


if __name__ == "__main__":
    main()
