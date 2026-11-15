# Implementation plan — one expedition, one Explorer

Source: design/ART_DIRECTION.md, EXPERIENCE.md, MOTION.md, REFERENCES.md and the user's instruction to implement the attached prompt. Read all four in full and inspected all six supplied local images, including current-ui.png.

## Inventory and preserved contracts

Vanilla HTML/CSS/JS; Leaflet 1.9.4; NASA GIBS/Blue Marble. app.js owns features, lens, selectedId, metadata and ledger. Canonical lenses L1, L2, M1, X1; SITES is a grouped showcase. Existing data paths: data/candidates.geojson, data/lenses.json, data/ledger.json; optional ?data= override and explicitly marked mock fallback. M1 has no qualified cells in the current web catalog; controls and decoys stay separate. L2 ranks/colors the shadow component; full Sun-geometry sigma remains separate. Rankings, score bands, verdict rows, descriptor values, provenance and limitations are unchanged.

## Direction and references

Planetary editorial entry, then a graphite scientific instrument: #101719 ground, #192225 surfaces, #f1eee6 text, #aab6b6 secondary, #e8bb82 action; original band colors kept separate. Chivo reading/display and Chivo Mono identifiers, both already local. Minimal borders/radii; map dominates. Actual data values, no decorative radar/percent-confidence conversion. Typography 14–16 px UI, 44–76 px intro. One CSS transition on entering the map, interruptible and absent under reduced motion.

Web references inspected as source pages, not live browser scene replays: NASA Eyes (spatial exploration of real data → persistent map); Rocani Outreach case study (narrative chapters → short intro, no speculative storyline/3D); Pudding homepage (question-driven explanations → measured feature rows); Apple iPhone overview (clear focal hierarchy → image with one primary action). Local screenshots supply visual composition: act-01 planetary scale, act-02 mission choice, act-03 dominant map, act-04 aligned measurements, act-05 evidence depth. Their speculative labels, HUDs and document collages are not scientific content or production assets.

## Work

- [x] Preserve current campaign and legacy explorer routes as campaign.html and legacy-explorer.html.
- [x] Add shared intro/chooser/Explorer markup for index.html and explorer.html (direct default).
- [x] Expose a thin read-only snapshot/action bridge from existing app.js; all selection flows use the same state. Preserve map viewport on selection; invalidate after resizing.
- [x] Render measured comparison with explicit units/raw field names; site groups expose their recorded field/facility/unknown rows. No generic imagery paired to a selected site.
- [x] Progressive evidence uses the existing Analog Test Card render, with readable sections and first-class limitations.
- [x] Load Leaflet locally at its existing version; cache no fabricated data; keep GIBS attribution and a tile-failure notice.
- [x] Implement real empty/loading/error states; query/hash navigation, reversible selection, focus return and reduced motion.
- [x] Capture before/after at 1440/768/390; exercise every lens, selection, history, raw comparison, missing/zero results, errors and reduced motion.

## Deliberate deferrals and exceptions

No GSAP, WebGL, synthetic globe, fake Earth scan, forced pinned scenes, new framework or scoring changes. No reveal slider for unregistered images. Keep existing campaign exports via their preserved route. App-screen Taste --app is unavailable in installed 2.5.1 scripts (verified in script usage); use its real headless screenshot runner and purpose-built interaction checks instead. Storyboard/accessibility override marketing-only full-screen section, decorative-effect and no-caption rules. Do not claim an old marketing gate as a pass for this app.

## Sources

NASA image pages: https://science.nasa.gov/resource/image-earthrise/ and https://science.nasa.gov/photojournal/global-color-views-of-mars/. Usage: https://www.nasa.gov/nasa-brand-center/images-and-media/. Exact files and credits recorded in web/media/expedition/credits.json after asset verification.

## Component tokens

Shared typography: Chivo body/display, Chivo Mono identifiers; 12/14/16 px text tokens, component headings 20/25/32 px, fluid intro 44–80 px. Spacing tokens 8/12/16/24/32/48 px, with 48/32/24/20 px responsive outer gutters. One line token, 3 px control radius, 180 ms interaction duration. Semantic sigma colors are independent of the amber action color. Native result rows, lens buttons, table, disclosure and modal all reuse this system.

## Similarities follow-up — paired terrain and engineering criteria

User requests both supplied act-04 references: two real terrains side by side, plus detailed visual comparison of slope, moisture and other important criteria. Preserve engine rankings and source measurements. Reuse verified target hillshade and exact Earth review footprints; do not infer a site's photograph from its name or reuse an unrelated footprint. Site groups can disclose a specific published member/target comparison, with unavailable member records labelled explicitly. Add shared-scale bars to each numeric row, raw values and exact Earth-minus-target differences. Include visible missing humidity, soil-moisture, local-temperature and bearing-strength rows; distinguish X1 aridity from humidity. Show published planetary ledger values separately from site measurements. Verify source/target binding, no false missing-zero conversions, responsive image frames and real browser interactions.
