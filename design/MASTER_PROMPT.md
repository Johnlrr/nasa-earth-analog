# Master prompt — SIMILITUDE immersive scientific experience

Use the `design-taste-frontend` skill. If GSAP skills are installed, use the relevant timeline and ScrollTrigger guidance only when motion complexity warrants it. Do not invoke several competing art-direction skills at once.

Act as a creative director, interaction designer, scientific visualization designer and senior frontend engineer. Redesign the existing SIMILITUDE web application into a memorable, interactive scientific expedition, not a decorative SaaS dashboard.

## Read first

Read `design/ART_DIRECTION.md`, `design/EXPERIENCE.md`, `design/MOTION.md`, and `design/REFERENCES.md` in full. Inspect every available screenshot in `design/reference-images/`. The five-act storyboard is the required narrative architecture; screenshots are inspiration, not pixel-perfect specs. Resolve any conflicts in favor of scientific correctness, existing functionality, accessibility and this brief. If a referenced screenshot is missing, use the written storyboard; do not claim to have seen it.

## Product and scope

- Product: SIMILITUDE — the proving-ground finder. Core proposition: find and evaluate terrestrial analogs for Moon/Mars mission tasks, using a consistent task-specific comparison framework and explicitly reporting what cannot transfer.
- Audience: NASA Space Apps judges, researchers, engineers, and curious non-specialists. English UI. Make the scientific value understandable quickly, and deeper evidence accessible on demand.
- Existing app: `http://localhost:8000`. The earlier screenshot shows Leaflet with NASA GIBS / Blue Marble attribution, a Sites showcase, lens tabs, ranked results, validation controls/decoys, score bands and an Analog Test Card. Verify all names, units, logic and states from the actual repo; the screenshot may be outdated.
- Scope: redesign the presentation and information architecture; build a short optional guided introduction and improve the existing scientific Explorer. Keep all current routes/APIs and interactions working; add a route or hash only if compatible. Do not migrate the framework.
- Stack: preserve HTML, CSS, Vanilla JavaScript and the existing map library. No React, Vue, Svelte, Next.js, Tailwind, new build system, or paid API requirements. Prefer CSS and native browser APIs. GSAP is optional if already available or added as one justified, pinned, lightweight dependency; retain a working non-GSAP fallback. Do not add WebGL/3D just for spectacle.
- Do not alter scientific calculations, thresholds, data processing, scores, ranking, classifications, API contracts, or evidence provenance. Do not infer confidence from a score unless the model actually defines confidence. Do not fabricate data/imagery, matches or NASA affiliation.

## Required experience

Use the following five acts as a single connected narrative, not five generic landing-page sections. `EXPERIENCE.md` is the implementation specification.

1. **The Mission:** cinematic opening with a real planetary image and the question: where on Earth can we rehearse a mission beyond it? Primary action: Begin the expedition. Persistent direct-access option: Open Explorer.
2. **Choose Your Mission:** Moon/Mars choice and task-specific lens selection. Describe what each lens evaluates, not merely what planet it belongs to. Selected task drives the real existing Explorer state.
3. **Search Across Earth:** signature transition from mission target to real Earth map; expose actual result categories and map/list selection. Keep map interactive. Show zero qualified cells honestly, if so.
4. **Discover the Similarities:** selecting a candidate opens comparative evidence — target vs Earth where real comparable data exists, feature values/differences, limitations. Never substitute visual resemblance for scientific qualification.
5. **Scientific Evidence:** progressive disclosure into the existing Analog Test Card: provenance, method, validation, unknowns, and what cannot transfer. A clearly labeled route back to candidates gives the user control.

Acts I–II are narrative/onboarding, optional and short. Acts III–V are working views or states of the same persistent Explorer, not full-screen forced scrolling. A judge should be able to reach real data immediately via Open Explorer. A single selection must drive the map, list, comparison and evidence; do not build a disconnected animated mockup.

## Execution sequence

### A — Inspect and plan

- Read existing repo instructions, inspect routes, data schemas, map code, CSS and state handling. Inspect actual desktop UI before changes. Inventory lens IDs, endpoints, units, legend, missing-data and selection states, links, attribution and scientific guardrails.
- Record before screenshots in `.taste-skill/before` at 1440, 768 and 390 where practical. Use Taste app-screen checks for the Explorer, page checks for guided story. Lint according to installed skill documentation. If tooling is unavailable, use the available browser/screenshot runner and report the gap.
- Create a concise implementation plan and a token/component specification in `design/IMPLEMENTATION_PLAN.md`. Identify relevant reference files, and choose one coherent direction. List which optional features are unsafe, unsupported or too expensive. Then implement without waiting for approval for normal UI changes; do not change backend or migrate framework.

### B — Deliver in priority order

**P0 (must ship, demo-critical):**
- Real, refined Explorer (Act III–V): mission selector, clear active lens, linked map/list, honest score legend, evidence panel, and useful empty/no-selection/zero-qualified/error/loading states.
- Static or lightweight cinematic intro (Act I), mission selection (Act II), direct Explorer shortcut and a coherent theme across all acts.
- One signature transition from chosen lens to Earth search; implement a simple CSS/map-camera fallback first. Comparison and evidence must work on real data.
- Responsive desktop/tablet/mobile, keyboard support, reduced motion, attribution and preserved behavior.

**P1 (only after P0 works):** richer pinned storytelling, restrained parallax, optional comparison image reveal for actual paired imagery, improved map camera choreography, refined dossier transitions. Optional 3D only if existing infrastructure/assets support it and it adds information; otherwise use a strong 2D composition. Do not add a new feature at the cost of P0 reliability.

### C — Verify and polish

- Test the full live journey, plus direct Explorer access, every lens, map and list selection, navigation back, validation-only results, no results, missing values, slow/failing data, mobile interactions, keyboard-only and reduced motion.
- Screenshot both views at 1440, 768 and 390 widths into `.taste-skill/after`. For pinned/animated scenes inspect intermediate frames and reduced motion, not only final stills. Check loading, layout shift, text clipping, map resizing, performance and browser errors. Use installed Taste scripts where available (including `--app` for Explorer).
- Critique screenshots against `ART_DIRECTION.md` and references; remove generic patterns. Iterate up to two focused polish passes after implementation, without breaking the scientific workflow. Do not add meaningless effects just to satisfy a design lint rule. Report justified exceptions.
- Produce a final concise report: files changed, before/after evidence, design decisions, what data is actually rendered, tests performed and outcomes, known failures/limitations, asset sources, and what was deferred. Never claim a check was run if it was not.

## Acceptance criteria

A first-time visitor understands the mission and can enter the real Explorer within two deliberate actions. All four existing mission lenses and Sites remain accessible if confirmed in the current repo. The selected site and lens remain consistent across map, list, comparison and dossier; no misleading or invented science. The interface has a distinctive planetary editorial identity without gradients/glow/card overload; the cinematic treatment does not slow or obscure the actual tool. The existing working app remains demonstrable even when motion or external media fails.
