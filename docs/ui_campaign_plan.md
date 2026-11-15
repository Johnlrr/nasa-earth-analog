software — planetary test planning for rover test engineers.
Deal: split hero; blue-black-cornflower with Chivo / Chivo Mono. Dark neutral terrain workspace; blue denotes modelled evidence, amber denotes unresolved work. Liquid-type on the export heading only. The user's scientific workflow overrides marketing-specific section recipes, caption prohibitions and fake-address guidance.

Voice: technical-dry; plain task language; explicit distinction between a modelled match and field readiness. Existing SIMILITUDE name retained. No customer claims, impact measurements or NASA endorsement invented.

Scope authorized directly on 2026-11-15: UI only. Existing pipeline, thresholds, scientific verdicts and concurrent access/slide work stay unchanged.

- Mission: split hero and real Moon/Earth study visuals, one desktop screen. Earth thumbnail scale is nominal; original georeferencing is not embedded. This limitation is retained in image provenance.
- Objectives: editable task checklist and review question, one desktop screen.
- Compare: three existing Connecting Ridge study candidates, one desktop screen; mobile content grows to retain readable evidence and controls.
- Campaign: per-variable evidence matrix and user notes; planned survey checklist. No coverage optimizer, calculated route or predicted lighting window.
- Evidence: live brief preview and HTML/JSON downloads. Original source records and SHA-256 accompany the draft. Export heading has the skill's low-strength pointer moment; no effect on scientific images.

Implemented as `web/index.html`, `web/campaign.css`, `web/campaign.js`. Previous homepage retained as `web/explorer.html`, using existing `app.js` / `style.css`. Existing `evidence.html` retained. Static hosting; no new service or framework. Draft persists only in browser localStorage.

Validation: `node --test tests/campaign.test.cjs`; JavaScript syntax check; skill browser checks and screenshots; Python lint/test attempted per repository instructions. Results recorded at completion.

The copy-lint numbered-step warning is intentional: these are the user's ordered workflow and exported brief contents. Scientific image labels, scale bars, provenance and nearby evidence limitations take precedence over the skill's generic no-caption rule. The compact resource footer intentionally avoids adding a sixth marketing screen to the five-stage workflow.

## UI implementation — 2026-11-15

Authorized scope: the five-stage interface requested by the user. The original explorer remains available at `web/explorer.html`. No scientific pipeline, model thresholds or underlying result tables were modified by this UI work.

Implemented: selectable mission task and objectives; three existing study candidates; live per-variable evidence matrix; local draft persistence; route/setup notes; planned survey checklist; HTML and JSON review exports with complete available source records and dataset SHA-256. Candidate regions and exact cell records are distinguished; missing cell coordinates remain missing. No route optimizer, predicted lighting window or hardware validation is implied.

Visual system: dealt split hero, blue-black-cornflower tokens, local Chivo/Chivo Mono fonts with OFL licenses; one low-strength liquid-type moment on the export heading; kit entrance/hover and reduced-motion support. NASA LOLA central 4 km hillshade and the project's Sentinel-2 review thumbnails are local assets. Original Earth georeferencing is unavailable in those thumbnails, so the comparison scale is explicitly nominal; Peary's narrow source image is retained without enlarging its height to fill the card. No stock or generated site photographs, invented performance figures, testimonials or customer endorsements.

Verification:

- `node --test tests/campaign.test.cjs`: 5/5 pass, including target isolation, unknown preservation, escaped exported notes and rejecting mock/provisional records.
- Headless browser interaction page: 15/15 pass. Checks include the worked example, add/remove evidence, local notes, HTML/JSON blobs, source hash, retained gaps, menu and images. Evidence: `web/.taste-skill/shots/browser-qa.png`.
- Desktop and mobile screenshots inspected. Final desktop: `web/.taste-skill/shots/finished1440.png`. Mobile: `web/.taste-skill/shots/final390.png`; later adjustments preserve native candidate-image ratios and shared grid edges.
- `node --check web/campaign.js`, `ruff check . --no-cache`, `git diff --check`: pass.
- Python pytest could not collect: current Python lacks numpy. No Python dependencies were installed for this UI-only change.
- Static build via `python scripts/build_site.py .taste-skill/ui-preview-final`: pass.
- Copy lint: 0 FAIL, 1 numbered-step warning. Numbered labels intentionally follow the requested ordered workflow and report contents.
- Design skill gate: `GATE: FAIL 17 (round 1 of 3)`. This is not represented as a pass. Its open findings were nav brand span wrapping, two text-only form/matrix sections, heading vocabulary, geographic coordinate/map links, hero app frame interpreted as a docked strip, compact footer section height/structure, hero wrapper structure, two inner-image edge rules, and mobile section-height/neighbour rules. The five-stage tool retains its forms, scientific map links, paired images and content-driven mobile lengths as requested; no checker files were edited or findings hidden. Zero waivers applied. The visual and functional results are recorded separately from this marketing-template gate.

No deployment was requested. Run `python scripts/build_site.py --serve 8000` from the repository for a complete local preview including existing figures and slides.

Final layout/performance checks: layout checker ran at 1440, 1024, 820, 768 and 390. Remaining strict findings concern scientific subframes/grid edges and content-driven mobile section lengths; tablet paired images were subsequently expanded to full frame width. Performance check: 0 FAIL, 6 WARN across desktop/mobile (font weight, full-resolution hillshade size). Both measured layout shift 0.000 and zero broken requests. Total compressed transfer approximately 1.25 MiB. The full-resolution hillshade is intentionally retained for source inspection. No waivers or checker modifications.
