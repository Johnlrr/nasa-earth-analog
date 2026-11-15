# ruff: noqa: E501  (the slide HTML and CSS templates keep one element per line)
"""Build the 7-slide demo deck (slides/deck.html) with every number filled from docs/slide_numbers.json.

    python scripts/slides/build_deck.py [--team "Team name"]
    node scripts/slides/render_deck.mjs          # deck.html -> SIMILITUDE-slides.pdf + PNG previews

A number is written as {{key}} or {{key:fmt}}; an unknown key stops the build, so no number on a
slide can drift from the pipeline tables (same rule as docs/slides_draft.md). Formats: pct0 / pct1
(share -> percent), int (thousands separator), km0 (one km figure), raw.
"""

from __future__ import annotations

import argparse
import html
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
NUMBERS = ROOT / "docs" / "slide_numbers.json"
OUT = ROOT / "slides" / "deck.html"
SITE_URL = "https://johnlrr.github.io/nasa-earth-analog/"
REPO_URL = "https://github.com/Johnlrr/nasa-earth-analog"


def fmt(v, kind: str) -> str:
    if kind == "pct0":
        return f"{round(float(v) * 100):d} %"
    if kind == "pct1":
        return f"{float(v) * 100:.1f} %"
    if kind == "int":
        return f"{int(round(float(v))):,}"
    if kind == "km0":
        return f"{round(float(v)):d} km"
    if kind == "f2":
        return f"{float(v):.2f}"
    if kind == "raw":
        return str(v)
    raise ValueError(f"unknown format {kind}")


def fill(text: str, numbers: dict) -> tuple[str, set[str]]:
    used: set[str] = set()

    def sub(m: re.Match) -> str:
        key, kind = m.group(1), m.group(2) or "raw"
        if key not in numbers:
            raise KeyError(f"slide number key not in slide_numbers.json: {key}")
        used.add(key)
        v = numbers[key]
        v = v["value"] if isinstance(v, dict) else v
        return html.escape(fmt(v, kind))

    return re.sub(r"\{\{([A-Za-z0-9_]+)(?::([a-z0-9]+))?\}\}", sub, text), used


CSS = """
@page { size: 1920px 1080px; margin: 0; }
:root {
  --bg: #f7f6f1; --panel: #ffffff; --ink: #161c1a; --muted: #565c56; --line: #dcdbd3;
  --accent: #2e6b58; --t: #2a7bd5; --n: #e2662f; --u: #a9a8a0; --soft: #eceae2;
}
* { box-sizing: border-box; }
html, body { margin: 0; background: #888; }
body { font-family: "Host Grotesk", "Segoe UI", system-ui, sans-serif; color: var(--ink); }
.slide {
  width: 1920px; height: 1080px; position: relative; overflow: hidden; background: var(--bg);
  padding: 84px 104px 72px; display: flex; flex-direction: column; page-break-after: always;
  break-after: page; margin: 0 auto 24px;
}
@media print { html, body { background: var(--bg); } .slide { margin: 0; } }
.eyebrow { font: 500 22px/1.2 "JetBrains Mono", monospace; letter-spacing: .1em; text-transform: uppercase;
  color: var(--accent); margin: 0 0 18px; }
h1 { font-size: 64px; line-height: 1.05; letter-spacing: -0.03em; font-weight: 600; margin: 0 0 28px; max-width: 1500px; }
h1.cover { font-size: 150px; letter-spacing: -0.045em; margin-bottom: 26px; }
.lead { font-size: 34px; line-height: 1.4; color: var(--ink); margin: 0; max-width: 1300px; }
.muted { color: var(--muted); }
.num { font: 600 76px/1 "Host Grotesk", sans-serif; letter-spacing: -0.03em; }
.mono { font-family: "JetBrains Mono", monospace; }
.foot { position: absolute; left: 104px; right: 104px; bottom: 34px; display: flex; justify-content: space-between;
  font: 400 17px/1.3 "JetBrains Mono", monospace; color: var(--muted); }
.row { display: flex; gap: 48px; align-items: stretch; }
.col { display: flex; flex-direction: column; }
.grow { flex: 1; min-width: 0; }
.fig { background: #fcfcfa; border: 1px solid var(--line); border-radius: 14px; padding: 14px; display: flex;
  align-items: center; justify-content: center; }
.fig img { max-width: 100%; max-height: 100%; display: block; }
.stat { border-left: 6px solid var(--accent); padding: 4px 0 4px 26px; margin: 0 0 30px; }
.stat p { margin: 10px 0 0; font-size: 26px; line-height: 1.35; color: var(--muted); }
ul.pts { margin: 0; padding: 0; list-style: none; display: grid; gap: 18px; }
ul.pts li { font-size: 27px; line-height: 1.38; padding-left: 30px; position: relative; }
ul.pts li::before { content: ""; position: absolute; left: 0; top: 14px; width: 12px; height: 12px; border-radius: 3px;
  background: var(--accent); }
.verdicts { display: flex; gap: 14px; flex-wrap: wrap; }
.v { font: 600 24px/1 "JetBrains Mono", monospace; letter-spacing: .04em; padding: 12px 16px; border-radius: 8px; color: #fff; }
.v.t { background: var(--t); } .v.n { background: var(--n); } .v.u { background: var(--u); color: var(--ink); }
.tiles { display: grid; grid-template-columns: repeat(3, 1fr); gap: 22px; }
.tile { background: var(--panel); border: 1px solid var(--line); border-radius: 16px; padding: 26px 28px; }
.tile .num { font-size: 58px; }
.tile h3 { margin: 12px 0 6px; font-size: 25px; line-height: 1.25; font-weight: 600; }
.tile p { margin: 0; font-size: 21px; line-height: 1.38; color: var(--muted); }
.tile.fail { border: 2px solid var(--n); background: #fff6f1; }
.tile.fail .num { color: var(--n); }
.flow { display: grid; grid-template-columns: 1fr 70px 1.1fr 70px 1fr; align-items: center; gap: 0; }
.box { background: var(--panel); border: 1px solid var(--line); border-radius: 16px; padding: 28px 32px; min-height: 270px; }
.box h3 { margin: 0 0 12px; font: 600 21px/1.2 "JetBrains Mono", monospace; letter-spacing: .08em; text-transform: uppercase; color: var(--accent); }
.box p { margin: 0 0 12px; font-size: 29px; line-height: 1.35; }
.arrow { text-align: center; font-size: 46px; color: var(--accent); }
.lenses { display: grid; grid-template-columns: repeat(5, 1fr); gap: 16px; margin-top: 26px; }
.lens { background: var(--panel); border: 1px solid var(--line); border-radius: 14px; padding: 24px 22px 26px; }
.lens b { font: 600 20px/1 "JetBrains Mono", monospace; background: var(--ink); color: #fff; padding: 6px 8px; border-radius: 5px; }
.lens h4 { margin: 16px 0 8px; font-size: 28px; }
.lens p { margin: 0; font-size: 22px; line-height: 1.33; color: var(--muted); }
.lens.off { background: var(--soft); }
.funnel { display: flex; gap: 10px; align-items: stretch; margin: 0 0 28px; }
.funnel div { background: var(--panel); border: 1px solid var(--line); border-radius: 12px; padding: 14px 18px; flex: 1; }
.funnel div:last-child { background: var(--accent); border-color: var(--accent); color: #fff; }
.funnel b { display: block; font-size: 40px; letter-spacing: -0.02em; }
.funnel span { font-size: 19px; line-height: 1.3; }
.quote { font-size: 24px; line-height: 1.4; border-left: 4px solid var(--line); padding-left: 20px; color: var(--muted); margin: 0; }
.qr { width: 190px; height: 190px; background: #fff; border: 1px solid var(--line); border-radius: 12px; padding: 10px; }
.qr img, .qr svg { width: 100%; height: 100%; display: block; }
.links { font: 500 24px/1.5 "JetBrains Mono", monospace; }
.small { font-size: 20px; line-height: 1.4; color: var(--muted); }
"""

SLIDES = r"""
<section class="slide" id="s1">
  <p class="eyebrow">NASA Space Apps Challenge 2026 · Moon Base and Mars analog sites</p>
  <h1 class="cover">Famous ≠ faithful.</h1>
  <p class="lead" style="font-size:40px;max-width:1560px"><b>SIMILITUDE</b> helps Artemis test engineers pick an Earth field site the way a wind-tunnel engineer checks a model:
    not “does it look like the Moon?” but <b>which test results transfer</b>, and we test our own answer against a pre-registered traverse simulation.</p>
  <div class="row" style="margin-top:60px;gap:28px">
    <div class="tile" style="flex:1"><span class="num">{{cr_frac_gt8:pct0}}</span><p style="font-size:24px">of the Moon Base ridge (Connecting Ridge) is steeper than 8°</p></div>
    <div class="tile" style="flex:1"><span class="num" style="color:var(--n)">{{classic_frac_gt8_median:pct0}}</span><p style="font-size:24px">median at six famous analog field sites, same formula</p></div>
    <div class="tile" style="flex:1"><span class="num">{{v1_passer_reproduce}} / {{v1_passer_n}}</span><p style="font-size:24px">slope matches also reproduce the ridge's simulated traverse outcomes (pre-registered test)</p></div>
  </div>
  <div style="margin-top:34px" class="verdicts">
    <span class="v t">TRANSFERS · test it in the field</span>
    <span class="v n">NO-ANALOG · use a named facility</span>
    <span class="v u">UNOBSERVED · we cannot say</span>
  </div>
  <div class="row" style="margin-top:auto;align-items:flex-end">
    <div class="grow">
      <p class="small" style="margin:0">Challenge: Identify Earth Locations that Analog the Permanent Moon Base Locations and Mars</p>
      <p class="small" style="margin:6px 0 0">__TEAM_LINE__</p>
    </div>
    <div class="links" style="text-align:right">__SITE_URL__</div>
  </div>
</section>

<section class="slide" id="s2">
  <p class="eyebrow">1 · The problem</p>
  <h1>Six famous analog field sites are too flat for the Moon Base ridge</h1>
  <div class="row grow">
    <div class="col" style="width:560px">
      <div class="stat"><span class="num">{{cr_frac_gt8:pct0}}</span>
        <p>of the Connecting Ridge footprint (Artemis south pole) is steeper than 8°</p></div>
      <div class="stat" style="border-color:var(--n)"><span class="num">{{classic_frac_gt8_median:pct0}}</span>
        <p>median across the footprints of {{classic_n}} classic analog field sites — none within the ridge's range</p></div>
      <p class="quote">Haughton Crater has {{attention_haughton_devon}} analog papers, yet its footprint sits in the flat group of the chart.
        Fame is not fidelity for this test.</p>
    </div>
    <div class="fig grow"><img src="../docs/figures/fig_mission_slopes.png" alt="Share of terrain steeper than 8 and 20 degrees"></div>
  </div>
  <p class="small" style="margin:20px 0 0">Same formula and 30 m baseline on both worlds; 8° and 20° are the values in NASA's Artemis III landing and EVA
    slope requirements (NTRS 20250009323). This compares Earth with the Moon, not with NASA's landing maps.</p>
</section>

<section class="slide" id="s3">
  <p class="eyebrow">2 · How it works</p>
  <h1>One formula, two worlds, a verdict for every test variable</h1>
  <div class="flow">
    <div class="box"><h3>Target · Moon / Mars</h3>
      <p>LRO LOLA south-pole DEMs (PGDA 78)</p><p>MRO CTX Jezero DTM · CRISM · SWIM ice</p></div>
    <div class="arrow">→</div>
    <div class="box" style="border:2px solid var(--accent)"><h3>Same code on both sides</h3>
      <p>Descriptors at a common baseline</p><p>Distance to the target, tested against a random null sample of Earth cells</p></div>
    <div class="arrow">→</div>
    <div class="box"><h3>Per test variable</h3>
      <div class="verdicts" style="flex-direction:column;align-items:flex-start;gap:10px">
        <span class="v t">TRANSFERS</span><span class="v n">NO-ANALOG → facility</span><span class="v u">UNOBSERVED</span></div></div>
  </div>
  <div style="margin-top:22px;margin-left:0" class="small">Earth side: Copernicus DEM, NASA EMIT, MODIS, ERA5-Land, ESA WorldCover · {{verdict_rows_total:int}} verdict rows in total</div>
  <div class="lenses">
    <div class="lens"><b>L1</b><h4>Touchdown &amp; traverse</h4><p>Moon · slopes and roughness</p></div>
    <div class="lens"><b>L2</b><h4>Low-Sun navigation</h4><p>Moon · long shadows</p></div>
    <div class="lens off"><b>M1</b><h4>Aqueous minerals</h4><p>Mars · failed its own stop rule: no site published</p></div>
    <div class="lens"><b>X1</b><h4>Ice under dry soil</h4><p>Mars · semi-quantitative</p></div>
    <div class="lens" style="border:2px solid var(--accent)"><b>T-Mars</b><h4>Rover terrain</h4><p>Jezero delta front · classic Mars sites {{mars_classic_share:pct0}} vs random {{mars_null_share:pct0}} (p = {{mars_p}})</p></div>
  </div>
  <div class="tile" style="margin-top:auto;display:flex;gap:30px;align-items:center;background:var(--soft);border:0">
    <span class="mono" style="font-size:22px;color:var(--accent);white-space:nowrap">A CELL COUNTS ONLY IF</span>
    <p style="font-size:25px;color:var(--ink)">it passes the lens gates (bare ground, NDVI ≤ 0.15), lies within 2σ of the target and at or above the 90th
      percentile of the random null sample. Moon terrain verdicts must also hold in all three test configurations. Controls and decoys are scored the same way.</p>
  </div>
</section>

<section class="slide" id="s4">
  <p class="eyebrow">3 · Evidence</p>
  <h1>Six checks against known truth, and our own tests, pass or fail</h1>
  <div class="tiles">
    <div class="tile"><span class="num">{{nasa_slope_max_abs_diff_deg}}°</span><h3>Matches NASA's own product</h3>
      <p>largest difference between our slope code and NASA's PGDA 78 slope rasters, six south-pole sites</p></div>
    <div class="tile"><span class="num">{{prevalence_connecting_ridge_pass}} vs {{prevalence_shackleton_rim_pass}}</span><h3>Selective</h3>
      <p>of {{prevalence_connecting_ridge_n:int}} random bare-land cells pass for the ridge vs the steep Shackleton wall (exact McNemar p = {{prevalence_ridge_vs_wall_p_mcnemar_exact}})</p></div>
    <div class="tile"><span class="num">{{cross_dem_same_verdict}} / {{cross_dem_n}}</span><h3>Stable across elevation models</h3>
      <p>terrain verdicts unchanged when recomputed from a second, independent DEM (NASADEM / ArcticDEM)</p></div>
    <div class="tile"><span class="num">{{stability_classic_robust}} / {{stability_classic_n}}</span><h3>Classic sites do not pass</h3>
      <p>footprints in the 12 km blocks around six classic analog sites pass the ridge test</p></div>
    <div class="tile"><span class="num">{{lunar_control_wall_same_pass}} / {{lunar_control_wall_same_n}}</span><h3>Known truth on the Moon</h3>
      <p>Shackleton-wall footprints match their own reference ({{lunar_control_wall_other_pass}} / {{lunar_control_wall_other_n}} for other sites): it finds a terrain class, not a named place</p></div>
    <div class="tile"><span class="num">{{x1_positive_pass}} / {{x1_positive_n}} · {{x1_decoy_rejected}} / {{x1_decoy_n}}</span><h3>Ice test (semi-quantitative)</h3>
      <p>polar-desert controls pass, wet-permafrost decoys rejected; our own Pamir–Changtang guess: {{x1_pamir_changtang_pass}} / {{x1_pamir_changtang_total}}</p></div>
  </div>
  <div class="row" style="margin-top:22px;gap:22px">
  <div class="tile" style="flex:1;display:flex;gap:26px;align-items:center;border:2px solid var(--accent)">
    <span class="num" style="font-size:44px;line-height:1.1">{{v1_h1_verdict}}<br>→ {{v2_h1_verdict}}</span>
    <p style="font-size:20px;color:var(--ink)"><b>Our method, tested by a 30 m traverse planner (pre-registered twice):</b> with 8 lunar neighbours the threshold was loose (p = {{v1_h1_p}}).
      With {{v2_n_moon_native}} non-overlapping neighbours, registered before the rerun, slope matches reproduce the ridge's routes {{v2_passer_reproduce}}/{{v2_passer_n}} vs random land {{v2_null_share:pct0}} (p = {{v2_h1_p}}).
      Classic sites {{v2_classic_share:pct0}}: not beaten (p = {{v2_h1b_p}}).</p>
  </div>
  <div class="tile fail" style="flex:1;display:flex;gap:26px;align-items:center">
    <span class="num">{{m1_stop_rule_verdict}}</span>
    <p style="font-size:21px;color:var(--ink)"><b>Mineral test:</b> {{m1_checks_passed}} of {{m1_checks_n}} pre-registered checks pass, but the Lake Salda pair reaches only
      {{salda_relocated_largest_patch_km2}} km² (rule: 0.1 km²). The rule says fail, so we publish <b>no mineral analog</b>.</p>
  </div>
  </div>
</section>

<section class="slide" id="s5">
  <p class="eyebrow">4 · What the data found</p>
  <h1>Two open-country sites pass both terrain tests, on two DEMs</h1>
  <div class="row grow">
    <div class="col" style="width:860px">
      <div class="funnel">
        <div><b>{{v1_passer_n}}</b><span>slope matches for the ridge</span></div>
        <div><b>{{i1_three_tests_n}}</b><span>also reproduce its traverse routes, on two DEMs</span></div>
        <div><b>{{i1_open_all_tests_n}}</b><span>open to NASA, outside known analog areas</span></div>
      </div>
      <ul class="pts">
        <li><b>Argentina</b> ({{i1_argentina_lat:f2}}, {{i1_argentina_lon:f2}}): the only one of {{prevalence_connecting_ridge_n:int}} <i>random</i> cells to pass, not picked by us.
          Terrain shadow {{i1_argentina_shadow_e2:pct0}} (ridge neighbourhood {{i1_ridge_native_shadow_e2_min:pct0}}–{{i1_ridge_native_shadow_e2_max:pct0}}). Low Sun only ~{{i1_argentina_lowsun_min_per_day:int}} min a day.</li>
        <li><b>Baffin Island, Canada</b> ({{i1_baffin_lat:f2}}, {{i1_baffin_lon:f2}}): from {{i1_baffin_window_from}} to {{i1_baffin_window_to}} ({{i1_baffin_window_days}} days) every daylight minute has the Sun below 7°,
          ~{{i1_baffin_window_lowsun_h:int}} h a day. Slopes still match at 5 m (ArcticDEM 2 m: {{ms_baffin_frac_gt8_5m:pct0}} vs {{ms_ridge_frac_gt8_5m:pct0}} above 8°). Caveats: snow season; more shadow and climb than the ridge.</li>
        <li><b>Dropped by the traverse test:</b> the Chile lead (Atacama analog area) and Da Qaidam (China). Across all {{atlas_n_regions}} Artemis regions only the ridge
          has such a site: all {{atlas_shackleton_slope_two_dems}} slope leads for the Shackleton wall fail the route test ({{atlas_shackleton_routes_two_dems}} pass).</li>
      </ul>
      <p class="small" style="margin-top:16px">Leads, not verdicts: found after the published results, not yet visited; the low-Sun calendar is exploratory. Planning screen, not legal advice:
        China (Wolf Amendment), Russia, comprehensively sanctioned states left out.</p>
    </div>
    <div class="col grow" style="gap:14px">
      __LEAD_PICS__
    </div>
  </div>
</section>

<section class="slide" id="s6">
  <p class="eyebrow">5 · Limits we state ourselves</p>
  <h1>What a 4 km footprint from orbit cannot tell you</h1>
  <div class="row grow" style="gap:56px">
    <div class="col grow">
      <ul class="pts">
        <li><b>A sample, not a census:</b> {{l1_cells_scored_rank_seed}} scored cells. The random sample suggests about {{prevalence_connecting_ridge_cells:int}} cells on Earth
          would pass the terrain test (95 % CI {{prevalence_connecting_ridge_cells_lo:int}}–{{prevalence_connecting_ridge_cells_hi:int}}).</li>
        <li><b>A footprint, not a region:</b> 30 m slope baseline; boulders and craters under 60 m are unobserved. The traverse test is a planner simulation, not a rover.</li>
        <li><b>Gravity, vacuum, radiation, dust:</b> no Earth site reproduces them; each card names the facility instead.</li>
        <li><b>Ice lens is semi-quantitative</b> (reanalysis soil temperature, thresholds set after seeing data). <b>Mineral lens publishes nothing.</b></li>
        <li><b>Slope match ≠ route match:</b> only {{v2_passer_reproduce}} of {{v2_passer_n}} slope matches also reproduce routes, so each card reports both. The route test passes against random land only narrowly (p = {{v2_h1_p}}) and does not beat classic sites ({{v2_classic_share:pct0}} of their footprints reproduce routes).</li>
        <li>Every rule changed after seeing data is listed in the validation report.</li>
      </ul>
    </div>
    <div class="col" style="width:600px">
      <div class="tile" style="padding:34px">
        <p class="small" style="margin:0 0 14px">Sun below 7° for a share of daylight, over a year</p>
        <div class="row" style="gap:40px">
          <div><span class="num" style="color:var(--n)">{{l2_earth_best_lowsun_frac_daylight:pct0}}</span><p class="small">best Earth site</p></div>
          <div><span class="num">{{l2_moon_lowsun_frac_daylight:pct0}}</span><p class="small">lunar south-pole target</p></div>
        </div>
        <p style="font-size:25px;line-height:1.35;margin:18px 0 0">Over a year no Earth site matches. In a season one can: Baffin has {{i1_baffin_window_days}} days with all daylight below 7°.</p>
      </div>
    </div>
  </div>
</section>

<section class="slide" id="s7">
  <p class="eyebrow">6 · What a test team gets</p>
  <h1>A campaign, not a site: which test rows each site covers</h1>
  <div class="row grow">
    <div class="fig" style="width:800px;align-self:flex-start"><img src="../docs/figures/fig_campaign_coverage.png" alt="Campaign coverage matrix for Connecting Ridge"></div>
    <div class="col grow">
      <ul class="pts">
        <li><b>Two leads cover {{camp_two_leads}} of {{camp_n_field}}</b> field rows (slope, routes, low Sun, shadow, 5 m slope); Baffin alone {{camp_baffin_joint}} together,
          in its winter window. The best classic site alone covers {{camp_best_classic_alone}}. {{camp_n_facility}} rows go to named facilities (offload rig for 0.165 g, thermal-vacuum…); rocks need a survey.</li>
        <li>Rows map to NASA Civil Space Shortfalls <b>#0805</b> (surface mobility) and <b>#1101</b> (precision landing).</li>
        <li><b>Mars rover terrain, same code:</b> Jezero delta front (CTX DTM): classic Mars-analog footprints {{mars_classic_share:pct0}} vs random land {{mars_null_share:pct0}} (p = {{mars_p}}, pre-registered).</li>
        <li><b>Mars ice, beside Mars Life Explorer</b> (2 m drill): permafrost within 2 m at {{x1_mission_within_2m}} of {{x1_mission_cells}} ice-lens cells (semi-quantitative).</li>
      </ul>
      <div class="row" style="margin-top:auto;gap:28px;align-items:center">
        <div class="qr" id="qr" data-url="__SITE_URL__"></div>
        <div class="links">__SITE_URL__<br><span class="small">Site finder for six Artemis regions · no TRL assigned<br>Code, data, report (Apache-2.0): __REPO_URL__</span></div>
      </div>
    </div>
  </div>
  <p class="small" style="margin:18px 0 0">Data: NASA LRO LOLA / PGDA 78, MRO CRISM (MICA), NASA EMIT ({{emit_footprints_m1}} footprints), SWIM, MODIS, ASTER GED, NASADEM; Copernicus DEM ({{l1_chips}} chips), ESA WorldCover, Sentinel-2, ERA5-Land, TerraClimate, ArcticDEM, OpenAlex.
    SI use: code, analysis checks and slide text were drafted with SI assistants (Anthropic Claude, Google Gemini) under team review; every number is read from the pipeline tables.</p>
</section>
"""

QR_JS = """
<script src="https://cdnjs.cloudflare.com/ajax/libs/qrcode-generator/1.4.4/qrcode.min.js"></script>
<script>
(function () {
  var el = document.getElementById('qr');
  try {
    var q = qrcode(0, 'M'); q.addData(el.getAttribute('data-url')); q.make();
    el.innerHTML = q.createSvgTag({ cellSize: 6, margin: 0, scalable: true });
  } catch (e) { el.style.display = 'none'; }
  document.documentElement.setAttribute('data-qr', el.innerHTML ? 'ok' : 'none');
})();
</script>
"""


def lead_pictures() -> str:
    """Slide 5 pictures: the open-country ridge leads that pass slope (two DEMs), the
    pre-registered traverse test (two DEMs) and lie outside known analog areas."""
    acc = json.loads((ROOT / "web" / "data" / "access.json").read_text(encoding="utf-8"))
    reg = next(r for r in acc["regions"] if r["id"] == "connecting_ridge")
    lw = json.loads((ROOT / "data" / "derived" / "lighting_windows.json").read_text(encoding="utf-8"))
    ok = {r["cell_id"] for r in lw if r["route_reproduces"] and r["route_reproduces_second_dem"]
          and r["open_country"] and r["l1_robust_second_dem"] and not r["in_exclusion_buffer"]}
    leads = [x for x in reg["leads"] if x["cell_id"] in ok and x.get("images")]
    if not leads:
        return ('<div class="fig grow"><img src="../docs/figures/fig_region_matrix.png" '
                'alt="Six PGDA 78 south-pole sites against Earth footprints"></div>')
    out = []
    for b in sorted(leads, key=lambda x: x["lat"]):
        out.append('<div class="row" style="gap:12px;align-items:center">'
                   f'<div class="fig" style="flex:1;padding:6px"><img style="max-height:300px" src="../web/{b["images"]["s2"]}" alt="Sentinel-2 true colour"></div>'
                   f'<div class="fig" style="flex:1;padding:6px"><img style="max-height:300px" src="../web/{b["images"]["slope"]}" alt="Slope classes"></div>'
                   f'<p class="small" style="width:150px;margin:0"><b>{html.escape(b["country"])}</b><br>{b["lat"]:.2f}, {b["lon"]:.2f}<br>4 km</p></div>')
    out.append('<p class="small" style="margin:0">Left: Sentinel-2 true colour. Right: slope classes from the same 30 m DEM — '
               '<span style="color:#3f9a64">■</span> under 8°, <span style="color:#d08a2e">■</span> 8–20°, '
               '<span style="color:#d0563f">■</span> over 20°.</p>')
    return "".join(out)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--team", default="", help="team name for the cover (left out when empty)")
    a = ap.parse_args()
    numbers = json.loads(NUMBERS.read_text(encoding="utf-8"))["numbers"]
    val = {k: (v["value"] if isinstance(v, dict) else v) for k, v in numbers.items()}
    # statements written as words on slide 5 must still hold in the tables
    assert val["cross_dem_da_qaidam_robust"] is True, "slide 5: Da Qaidam no longer holds with the second DEM"
    assert val["cross_dem_peary_land_rank_full_metric"] < val["rank_rule_threshold"], "slide 5: Peary Land wording"
    body, used = fill(SLIDES, numbers)
    team = (f"Team {html.escape(a.team)} · " if a.team else "") + "NASA Space Apps Challenge 2026, Ho Chi Minh City"
    body = body.replace("__LEAD_PICS__", lead_pictures())
    body = (body.replace("__TEAM_LINE__", team).replace("__SITE_URL__", SITE_URL)
            .replace("__REPO_URL__", REPO_URL))
    n_slides = body.count('<section class="slide"')
    assert n_slides == 7, n_slides  # Space Apps limit: seven slides including the title slide
    doc = ("<!doctype html><html lang=\"en\"><head><meta charset=\"utf-8\">"
           "<title>SIMILITUDE: demo slides</title>"
           "<link href=\"https://fonts.googleapis.com/css2?family=Host+Grotesk:wght@400..700"
           "&family=JetBrains+Mono:wght@400..600&display=swap\" rel=\"stylesheet\">"
           f"<style>{CSS}</style></head><body>{body}{QR_JS}</body></html>")
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(doc, encoding="utf-8")
    print(f"{OUT.relative_to(ROOT)}: {n_slides} slides, {len(used)} keyed numbers")


if __name__ == "__main__":
    main()
