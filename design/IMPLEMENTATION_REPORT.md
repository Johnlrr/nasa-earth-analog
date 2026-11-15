Taste final invocation: **GATE: OFF (no build active)**. This is a tooling-state result, not a design pass; see the gate record below.

# Implementation report — SIMILITUDE expedition

## Delivered

The optional Mission and mission-choice views lead into the existing real Explorer. Direct access remains available in the header and at `explorer.html`. Moon/Mars task choices use the canonical L1/L2/M1/X1 definitions. Sites remains a separate regional showcase.

One existing engine state drives the active lens, actual Leaflet markers, result rows, selected feature, measured comparison and Analog Test Card. Comparison presents source Earth/target/z fields with units and readable labels; missing measurements remain unavailable. M1 validation examples remain distinct from its zero qualified cells. L2 terrain-shadow ranking remains distinct from Sun geometry. Limits are visible before the expanded source record. No generated landscape, confidence conversion, scoring change, data rebuild or new framework was introduced.

The former campaign page is preserved as `campaign.html`, including saved drafts and both HTML/JSON exports. The earlier full page is preserved as `legacy-explorer.html`. The existing scientific evidence page is unchanged.

## Design and implementation

Graphite and mineral amber, local Chivo/Chivo Mono, flat ruled surfaces, map-first working area. Real NASA Earthrise is the entry image; LRO Moon and Viking Mars are explicitly contextual. No fabricated site-image pair. The single target-to-map entrance uses interruptible CSS; reduced motion removes it. Native disclosures, native dialog, visible keyboard focus and linked map/list highlights provide the interaction system. Leaflet 1.9.4 is now local for the new UI, with its BSD license; GIBS imagery keeps its attribution and failure notice.

Two polish passes addressed tablet text/image overlap, mobile image flow, map fitting after a hidden intro, map zoom limits on narrow screens, score explanation beside results, human-readable measurement labels and focus restoration on return. Actual after images were inspected, not only generated.

Files: `web/index.html`, `explorer.html`, `expedition.css`, `expedition.js`; thin bridge and presentation guards in `app.js`; preserved `campaign.html`/`legacy-explorer.html`; local `vendor/leaflet` and `media/expedition`; `tests/expedition.test.cjs` and live browser fixtures in `tests/browser/`.

## Verification

- Node: **9/9 passed**, including the existing campaign/export contract checks and source/missing-measurement comparison checks.
- Live browser journey: **57/57 passed**. Covers every lens, real map/list counts, list and keyboard marker selection, source descriptor values, validation classification, evidence and back navigation, focus return, map viewport retention, incompatible selection clearing, chooser→engine, history, modal, 1440/768/390/320 overflow, local images, controlled network failure, true empty dataset, delayed response and missing numeric values.
- Ruff: passed. JavaScript syntax: passed. Git whitespace check: passed.
- Static site assembly: passed with the existing `scripts/build_site.py`; deployment excludes local QA captures.
- Python pytest: cannot collect in the current Python environment because `numpy` is missing. No backend or scientific-data files were changed (`git diff --name-only -- web/data config src scripts` empty).

## Evidence and sources

Before: `web/.taste-skill/before/` (home at 1440/768/390 and prior Explorer desktop). After: `web/.taste-skill/after/` (Mission and Explorer at 1440/768/390, chooser, measured comparison and dossier; live QA screenshots). Local-only screenshot fixtures embed the actual app, not a UI reconstruction.

Exact NASA source URLs, agency credits, processing/context labels and usage guidance are recorded in `web/media/expedition/credits.json`. No new client assets are required for the shipped UI. The original same-scale study imagery remains in the preserved campaign; no unregistered pair was promoted to selected-site evidence.

## Tooling limits and deferrals

Installed Taste 2.5.1 has no Explorer `--app` mode. Its own headless runner was used for rendered inspection and live interaction fixtures. The user brief takes priority over marketing-only rules requiring full-screen sections, decorative effects and no image captions; scientific attribution and useful labels stay visible. Gate/performance final results are recorded below. Reduced-motion and campaign results appear below.

No GSAP, WebGL, forced pinned story, global scan/progress animation, registered-image reveal or scientific pipeline changes. NASA basemap tiles still require external network; a failed tile request leaves candidates and evidence usable. Local preview must use the existing site build script to include document/figure links.

### Additional final checks

Reduced-motion browser run: 57/57 passed with the OS media preference emulated. Preserved campaign route: 23/23 browser checks passed, including local draft persistence, adding/removing evidence, empty objectives, escaped user notes, HTML/JSON download blobs and dataset hash, mobile menu state and controlled data-load failure. The existing 5 campaign contract tests are included in the Node total above.

Senior-design review: the initial tablet photo intersected the headline; moving the photo crop and giving phone photography its own in-flow frame restored readability. Flat rows and the dominant actual map provide hierarchy; two planet choices are genuine alternatives, not filler cards. Selected state uses text/shape as well as color. Data limits and score explanation now sit with the decision. Horizontal tabs/tables remain deliberate scroll regions on phones; comparison scroll regions accept keyboard focus. Initial page load leaves focus with the browser; deliberate navigation moves focus, and returning to results restores the selected row.

### Final tooling record

- Copy lint: 0 FAIL / 0 WARN for the shipped intro.
- Performance spot check: one local CPU-browser run at each of 1440 and 390, **0 FAIL / 5 WARN** in the tool's aggregate summary. It reports no broken requests and layout shift 0.002 / 0.000. This is a local spot check, not field performance or a multi-run benchmark. Warnings concern 212.8 KiB of local fonts, Leaflet-created tile images without HTML size attributes, and the 1900 px hero rendition used on phones (the image is only about 84 KiB). Kept for correct fonts, unmodified Leaflet behavior and one verified image source. Report: `web/.taste-skill/after/perf.json`.
- Contrast: chosen normal-text pairs measured 7.77:1 or higher; action-button text 9.34:1. Values: `web/.taste-skill/after/contrast.json`.
- First root-level Taste gate: **GATE: FAIL 13 (round 1 of 3)**. Recorded in `.taste-skill/expedition-gate.txt`. Fixed its actionable focus-ring suppression and the unequal caption alignment afterwards. Other reported rules concern the user-required headline, absence of a decorative dealt moment, whole-screen footer/section rhythm, 48 px equal gutters versus the kit's 64–120 px range, its `.wrap` class requirement, an intentional inset caption and the accessibility skip link. No false PASS or blanket waiver was recorded.
- Final gate invocation from `web/` returned **GATE: OFF (no build active)** because the active marker is at repository root. Per the installed skill's OFF instruction, that invocation was not rerun. The final UI was still inspected in its own screenshot runner at all three required widths; functional browser checks, reduced-motion checks and performance checks ran independently. No final gate pass is claimed.
- No submitted scientific score/classification data, source pipeline or thresholds changed. No deployment, commit or push was performed.

To preview the final assembled app, run `python scripts/build_site.py --serve 8000` from the repository root. Open `/` for Mission or `/explorer.html` for direct access. Screenshots remain local under `web/.taste-skill/after/`; they are excluded from production assembly.

## Similarities follow-up

See `SIMILARITIES_REPORT.md` for the subsequently implemented two-terrain composition, exact footprint/target selector, detailed numeric bars, engineering gaps and planetary-reference table, with 15 Node and 24 new browser checks.
