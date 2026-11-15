# Project page — paste-ready (generated from docs/submission_kit.md; do not edit here)

Paste each section into the field of the same name. Fill every ⟨TEAM⟩ before submitting.

## Project name
SIMILITUDE: which Earth test results transfer to the Moon Base and Mars

## Link to Project Demo (7 slides including the title slide, PDF, public)
https://johnlrr.github.io/nasa-earth-analog/SIMILITUDE-slides.pdf

## Link to Final Project (public, no login)
https://johnlrr.github.io/nasa-earth-analog/ (web app) · test-site finder for Artemis regions in
countries open to NASA: https://johnlrr.github.io/nasa-earth-analog/test-sites.html · source, data
tables and validation report: https://github.com/Johnlrr/nasa-earth-analog

## High-Level Project Summary
Space agencies test Moon and Mars hardware at Earth "analog" sites, usually chosen because they
are famous or look right. SIMILITUDE asks the engineer's question instead: which test results
transfer? One formula is run on NASA data from both worlds, per mission test, and every site
gets a card that says what a field test there reproduces, what no Earth site reproduces (and
which facility replaces it) and what cannot be judged. For the Moon Base ridge (Connecting
Ridge), 76 % of the terrain is steeper than 8°; in the footprints of
six classic analog field sites the median is 9 %. From
196,008 bare-land cells we screened 300; two footprints match the ridge in that sample, and one
of them, Da Qaidam (a known Mars analog region), also survives a second, independent NASA
elevation model and matches 3 of 6 south-pole sites. But
Da Qaidam is in China, where NASA cannot run a bilateral campaign. So we ran the same test on
160 more cells in countries open to NASA: 3 usable ridge
leads hold with a second elevation model and the published ice rule, in Argentina, Canada and Chile; the best needs about
8 km of traverse for the slope exposure of 10 km on the ridge, against about 86 km at the median
classic site. Our mineral test did not pass its own pre-registered rule, so we publish no mineral
analog.

## Detailed Project Description
What it does. For four mission tests — Moon terrain for touchdown and traverse, Moon low-Sun
shadows, Mars aqueous minerals, Mars ice under dry soil — SIMILITUDE computes the same
descriptors on the target (NASA LOLA / PGDA 78, MRO CRISM, SWIM) and on Earth (Copernicus DEM,
NASA EMIT, MODIS, ERA5-Land), measures the distance to the target, and tests it against a random
null sample of Earth cells. Each test variable gets one of three verdicts: TRANSFERS (test it in
the field), NO-ANALOG (no Earth site reproduces it; the card names the facility) or UNOBSERVED
(we cannot say).

How we know it is not noise.
- Our slope code reproduces NASA's own slope rasters on six south-pole sites to within
  0.0009°.
- Of 1,000 random bare-land cells, 1 passes the terrain test for the ridge and 9 for
  the steep Shackleton inner wall.
- Recomputed from a second, independent elevation model (NASADEM / ArcticDEM), 102 of 109
  terrain verdicts are unchanged. The ones
  that change are listed and marked marginal, including one of our two ridge matches (Peary
  Land).
- In the 12 km blocks around six classic analog sites, 0 of 54 footprints pass the ridge test.
- Ice test: 2 of 2 polar-desert controls pass, 2 of 2 wet-permafrost decoys are rejected; semi-quantitative.
- Mineral test: 3 of 4 pre-registered checks pass; the rule says FAIL, so nothing is published for it.
- Every rule changed after seeing data is listed in the validation report (Deviations table).

Site finder for test engineers. Pick an Artemis south-pole region (six PGDA 78 regions) and
get matching 4 km footprints in countries open to NASA, each with Sentinel-2 and slope-class
pictures, the share of terrain steeper than 8° and 20°, a second-DEM check and the snow/ice share.
For the steep Shackleton inner wall there are 113 usable open-country leads, most in the Andes. Leads are exploratory: found
after the published results by the unchanged rule, not visited yet. Closed countries are an
assumption for planning (China including Aksai Chin, Russia, countries under comprehensive US
sanctions), not a legal opinion.

What a mission team gets. A test protocol per site (systems to test, what to measure, what
the site does not reproduce), read beside published NASA numbers: Artemis III "Surface slope for
landing (100m): <10 deg" and "Surface slope limit for EVA (2km): <20 deg" (NASA NTRS
20250009323); Mars Life Explorer "land within a vertical meter of Martian mid-latitude ice, drill
for samples to a 2-meter depth". By our measure a terrain site reproduces 1 of 7 test
variables; the card names the facility for
the others. A card is an input to a project's own "documented definition of relevant
environment"; it assigns no TRL.

Limits we state ourselves.
- Counts come from a 307-cell sample screened towards Connecting Ridge, not a census: about 201 bare-land cells (95 % CI
  10–1,093) would pass the terrain test.
- A match is one 4 km footprint, not a region; slopes are computed on a 30 m baseline and compare
  Earth with Moon, not with NASA's landing maps.
- Da Qaidam and Peary Land are known analog regions, not hidden sites; only Zanda/Gar has a low
  literature count.
- No Earth site reproduces the polar Sun: the best has the Sun below 7° for 28 % of daylight,
  the lunar target for 100 %.
- The ice lens is semi-quantitative (reanalysis soil temperature, thresholds set after seeing
  data); metre-scale boulders are below our resolution.

Tools. Python (NumPy, pandas, SciPy, Matplotlib), Google Earth Engine, NASA earthaccess,
OpenAlex API, Leaflet with NASA GIBS for the web map, GitHub Actions and Pages. Code licence
Apache-2.0.

## Use of Super Intelligence (SI)
Factual draft; the team must check it against the official rule (`docs/compliance.md`) before use.

Yes. We used SI assistants (Anthropic Claude models through Claude Code; Google Gemini models
through the Antigravity IDE) throughout: to draft and review planning documents, to write and
test code, to run and check analyses, to search and read the literature, to draft the validation
report, the slide text and this page, and to act as an adversarial reviewer before each merge.
SI assistants also proposed analysis directions that we adopted (presenting results by field
site, reading results beside published NASA requirements, the checks with a second elevation
model and a larger random sample). All data are NASA and partner open data, processed by the open
code in the repository; every threshold, control and rule change is recorded with its date and
reason. No SI-generated images, audio or video are used; the figures are plots of our own data.
Where SI was used is also stated on the web app, on the last slide and in the repository.

Core idea (judging analog sites by which test results transfer, per mission test):
⟨TEAM: state here, truthfully, who originated it and how SI was involved⟩.

## NASA Data
NASA PGDA Product 78 (LRO LOLA south-pole DEMs and slope rasters) · NASA EMIT L2A surface
reflectance · MRO CRISM MICA type spectra (PDS Geosciences) · SWIM subsurface water ice mapping
(Morgan et al. 2021) · MODIS land surface temperature and vegetation · ASTER GED · NASADEM ·
NASA GIBS Blue Marble (web basemap) · NASA NTRS 20250009323 and 20240009596 (Artemis III
landing requirements) · Mars Life Explorer mission concept study · NASA TRL definitions · NASA
SVS 14583 (JETT5) · NASA planetary fact sheets.

## Space Agency Partner Data and Other References
Copernicus DEM GLO-30 and ERA5-Land (ESA / Copernicus) · ESA WorldCover · Sentinel-2 (ESA) ·
TerraClimate · ArcticDEM (PGC) · OpenAlex · OpenStreetMap Nominatim · Viviano-Beck et al. 2014
(CRISM browse products) · Leaflet. Full table with links: README and `ledger/*.yaml` in the
repository.
