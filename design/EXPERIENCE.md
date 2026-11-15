# Experience storyboard — Five acts, one expedition

## Journey map

| Act | User's question | Action | Outcome |
|---|---|---|---|
| I. The Mission | Why look on Earth to prepare for space? | Begin / Open Explorer | Purpose and a clear next step |
| II. Choose Your Mission | What are we trying to rehearse? | Select target + lens | Real task context |
| III. Search Across Earth | Where are the candidates? | Explore the map/list | A selected real site or an honest empty state |
| IV. Discover the Similarities | Why might this site be useful? | Inspect matched features | Comparable evidence and mismatches |
| V. Scientific Evidence | How much can we trust and transfer? | Open dossier / sources | Method, provenance and limitations |

Acts I and II are a short optional layer; Acts III–V share the existing persistent map-based application. The direct path goes straight to Explorer with current/default lens from the code. Never require scrolling through five giant panels to reach data. All sample copy below is editable; no scientific claim is authorized solely by this brief.

## Act I — The Mission (wonder and context)

**Reference:** `reference-images/act-01-mission.png` if present. Learn the scale, atmosphere and typography hierarchy from it.

- Composition: wide real Moon or Mars horizon image, subject biased to one side to leave room for a readable headline. Compact brand/navigation, not a marketing navbar. On desktop one near-viewport scene; on phone allow natural flow and use an appropriate crop.
- Opening heading: “To explore beyond Earth, we begin here.” Subcopy: “Find Earth analogs for specific Moon and Mars mission tasks. Compare the evidence. Understand what cannot transfer.”
- Primary CTA: “Begin the expedition”. Secondary: “Open Explorer”. A compact “Data & limits” link should remain easy to find throughout the journey.
- Narrative device: introduce the core difference between an image that looks similar and a place that supports a particular mission test. Proposed short copy: “A familiar landscape is not enough. The right analog depends on what you need to test.”
- Interaction: CTA leads into Act II; direct access bypasses onboarding. Optional subtle image movement on entry, never a blocking autoplay film. Reduced-motion and no-image fallback must retain copy and actions.
- Exit: planetary scene becomes a focused mission choice. If browser history is used, Back should return to the prior view without wiping selection.

## Act II — Choose Your Mission (intent)

**Reference:** `reference-images/act-02-choose-mission.png` if present. Learn planet-scale visual composition, not a decorative feature-card grid.

- Heading: “What are we preparing for?” Supporting copy: “Choose a mission task to see how terrestrial sites compare.”
- Composition: two distinct planetary visuals or a split editorial selector (Moon | Mars), followed by task-specific choices. Keep task descriptions visible and legible, not hover-only. Use real mission lenses from data; do not add fictional ones.
- Existing screenshot labels to verify in repo:
  - L1 — Touchdown & Traverse (Moon). User-facing question: “Where can we rehearse landing and surface traversal?” Confirm which measurable criteria are actually available.
  - L2 — Low-Sun Navigation (Moon). Question: “Where can we test navigation under challenging low-angle illumination?” Do not claim a specific solar geometry metric without code support.
  - M1 — Aqueous Minerals & Biosignature (Mars). Question: “Where on Earth are relevant water-altered mineral assemblages exposed?” The screenshot mentions carbonate, Fe/Mg-smectite, olivine and jarosite; use canonical backend wording. Mineral analogs alone are not evidence of life.
  - X1 — Ice under Dry Overburden (Mars, as shown). Question: “Where can we test conditions relevant to ice beneath dry surface material?” Confirm any modeled/observed quantities and limits.
  - Sites — preserve the separate showcase/overview; do not misrepresent it as a mission lens or a ranked result.
- Interaction: select a target, then one lens. A lens drives the existing engine/map request or data lookup. Display actual lens criteria if available, not an invented checklist. Primary action “Find Earth analogs” opens the Explorer with the selected lens. Power users may switch lenses directly in Explorer.
- Micro-feedback: selected mission gets a readable active state; no color-only selection. Reversible, keyboard-operable. Changing lens clears an incompatible selection; if site is still supported, retain it only as existing semantics permit.
- Exit: signature target-to-Earth transition. Do not imply a scan of the entire Earth if the dataset only evaluates a bounded coverage. Do not manufacture a progress bar or delay.

## Act III — Search Across Earth (discovery)

**Reference:** `reference-images/act-03-search-earth.png` if present. Study map centrality and spatial hierarchy. The operational starting point is `reference-images/current-ui.png`.

- Heading: “Search across Earth” / active mission title. One line of the actual scientific question, plus compact lens switching. Secondary return to mission selection and direct “Data & limits” access.
- Desktop shell: a compact top bar, map as dominant block, visible ranked results surface (side or below depending on density), and a contextual detail drawer/panel. At 1440, prefer enough vertical map height for interaction while making real results visible. Avoid a half-empty side column; before selection show a meaningful guide with how to interpret the current lens and counts derived from actual data, or collapse the drawer.
- Keep Leaflet/NASA GIBS / Blue Marble as seen in the screenshot if confirmed; preserve attribution, zoom, pan and existing interactions. Do not migrate to Mapbox just because a reference uses it.
- Render actual candidate cells and categories. Map/list selection must stay synchronized. Retain current ordering, map marker semantics, score thresholds, capped values, controls, decoys, site showcase, and confirmed/semiquantitative/literature-only distinctions. Screenshot shows sigma bands (≤1, ≤2, ≤3, >3) and a “smaller is better” convention; verify exact definitions and display from code. Do not convert sigma into a percent or confidence gauge.
- Legend should be scannable, grouped by what the score means vs validation/evidence type. Use symbols and labels in addition to color. Hover/focus highlights a real corresponding map/list item; click activates its evidence.
- Real empty state: if qualified candidate count is zero, explicitly say “No engine-qualified cells for this lens” (or use existing canonical text). If validation controls/decoys exist, label and show them separately. Do not rank them as qualified discoveries or imply no Earth analog can exist outside the evaluated dataset. Offer another lens / show validation / clear filter only where implemented. Distinguish loading, network failure, no data, zero qualified and no selected site.
- Interaction: switch lens, inspect candidates, zoom or select from list/map. On selection animate map camera only as helpful; preserve user-controlled navigation. Open comparison preview and allow deeper evidence; no separate artificial dataset for the story.

## Act IV — Discover the Similarities (understanding)

**Reference:** `reference-images/act-04-similarities.png` if present. Study side-by-side comparison and visual explanation; do not treat illustrative terrain as a measured match.

- Heading: “What makes this place an analog?” Site name, location and active task; clear status and score only if present. If a control, decoy or hypothesis is selected, show its exact class prominently and explain its existing role from the data/method.
- Composition: evidence panel or expanded comparison beside/past the map. If actual, attributed site/target imagery exists, use a side-by-side scientific composition with captions, date/resolution if available and labels Earth vs Moon/Mars. If images are generic context, explicitly label them “Illustrative context — not this site”. If no legitimate comparable imagery exists, use real feature data without images. Do not invent a target region or image pairing.
- Primary visual: aligned feature rows or paired dot/bullet plots for real comparable measurements with units, reference values and differences. Show contribution/residual only if backend provides it or the documented formula supports an exact UI derivation; otherwise use current feature fields. Missing values get “Not available”; never render missing as zero. Do not use decorative radar charts, fake similarity percentages or a misleading distance scale.
- Narrative beat: a concise explanation of what matches and what differs using recorded observations (e.g. strongest agreement and mismatch only if computed and verified); clearly label qualitative/literature statements. Do not generate scientific facts on the fly. If no comparison fields exist, present existing Analog Test Card evidence directly rather than invent new metrics.
- Interaction: choosing another site updates the same panel and selected marker. If suitable same-type registered imagery exists, optional reveal slider may be added; otherwise keep fixed comparison. A clear “View evidence & limits” action goes to Act V. Back to all results restores the active lens and map/list context.

## Act V — Scientific Evidence (trust)

**Reference:** `reference-images/act-05-evidence.png` if present. Aim for a precise research dossier, not a long generic card wall.

- Heading: “Analog Test Card” (preserve product terminology). Subtitle: site + task context and actual qualification/validation state.
- Group available fields into: (1) site and mission task; (2) comparison method and feature evidence; (3) validation role, controls/decoys and score interpretation; (4) data provenance and citations; (5) what cannot transfer / uncertainty / missing measurements. Preserve the original data and distinctions. Do not invent confidence values, methodology, source links, validation or claims of operational readiness.
- “What cannot transfer” is a first-class panel, not hidden footer text. Use the repo's known limitations for the selected lens/site. General differences between worlds may be introduced as context only when supported and clearly separate from the measured score. Do not treat an Earth analog as qualification for lunar/Martian operations.
- Interaction: evidence disclosure can expand source details, methods and limitations using actual URLs/fields. Include existing Data & limits route. Optional print/export only if already supported or trivial, and never P0. Return to results without losing the selection. Native disclosure controls should be keyboard accessible.
- Closing idea (optional): “An analog is a place to test a question, not a second planet.” End by returning the user to exploration, not a sales CTA.

## Interaction / state contract

Inspect existing state rather than replacing it. Conceptual state elements: current narrative view, selected planet, canonical lens ID, selected site/cell ID, data request status, map view and optional evidence expansion. Reuse existing identifiers and rendering paths; adapt only where necessary. One source of truth should drive active lens, results, marker highlight, comparison and dossier, with stale responses ignored on quick lens switching if asynchronous. Do not let intro animation create an alternative data pipeline.

| Event | Expected behavior |
|---|---|
| Begin expedition | Show Act II; no data fabricated |
| Open Explorer | Open functional Act III immediately, from any intro state |
| Choose lens | Apply real lens, reset invalid selection, show accurate status |
| Click marker or result | Synchronize map/list and open real comparison/evidence |
| Open evidence | Show selected item's existing Test Card, preserve context |
| Back / close | Keep current lens and valid selection, restore focus |
| Zero qualified | Show honest empty state + separate controls/decoys if present |
| Missing imagery/metric | Use labeled context or omit; never fake comparison |
| Reduced motion or script failure | Same usable flows without cinematic animation |

## Judge demo path (rehearsal, not an auto-playing UI)

0–10s: mission question → 10–25s: choose real lens → 25–45s: map and real candidates/validation → 45–70s: comparison and evidence → 70–90s: limits and method. Choose a lens/site based on verified real data. If no lens has qualified candidates, present the honest validation story and limitations. Never preselect a fabricated successful result to make the demo look better.
