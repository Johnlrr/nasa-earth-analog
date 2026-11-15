# Art direction — A field instrument for worlds beyond Earth

## Concept

**To explore beyond Earth, we begin here.**

SIMILITUDE is a scientific expedition into terrestrial proving grounds. The story moves from wonder (a planetary horizon), to intent (mission task), to discovery (Earth), to scrutiny (comparison), to accountability (evidence and limits). It should feel like a curated planetary atlas crossed with a precise field instrument — neither a space-themed game nor a generic analytics product.

Supporting line, proposed copy: “Find terrestrial proving grounds for Moon and Mars mission tasks — and understand where the analogy ends.” This is descriptive, not an official NASA tagline.

## Visual system (proposed starting direction)

- Cinematic entry: real, full-bleed planetary imagery; restrained dark surface, ample negative space and clear typography. One focal image per scene. Make content readable without relying on the image loading.
- Working Explorer: a quiet, high-contrast scientific instrument. Prefer deep graphite or mineral-paper surfaces, based on actual map readability. Keep the same type and palette across views. The map is central, with evidence and controls precisely aligned; avoid a collage of cards.
- Example dark tokens (adjust after testing): ink/background `#101719`, raised surface `#192225`, text `#F1EEE6`, muted `#AAB6B6`, separators `#344144`, single action accent `#E8BB82` (muted mineral amber). Use existing score/status colors as separate semantic tokens, not decorative brand colors. Verify normal-text contrast at least 4.5:1 and relevant UI/large-text contrast at least 3:1; adjust tokens rather than assume compliance.
- Typography: one characterful editorial display face and one highly legible UI sans, or a single strong type family; use at most two families and system fallbacks. A serif display face is optional, not mandatory. Map labels, values and controls should be legible and practical, with tabular numerals for measured values. Aim for 14–16 px normal UI text; avoid tiny muted all-caps blocks. Display headings can use fluid sizes (e.g. 44–76 px desktop / 32–44 px phone) and sensible line lengths.
- Composition: deliberate asymmetry, wide imagery, baseline alignment, purposeful whitespace, consistent spacing scale. Explorer should be denser than intro; do not apply landing-page spacing to scientific data. Prefer flat sections, clear dividers and restrained borders over deep shadows and nested cards.
- Iconography: familiar line icons / simple SVG with text labels on critical actions. Preserve scientific marker shapes and color categories; add labels/patterns for non-color recognition. Do not use emoji as navigation or icons.
- Assets: real planetary/terrestrial imagery with contextual labels and credits; no generated landscapes presented as observations. No NASA logos implying endorsement. Reference screenshots are mood boards, never automatically production media.
- Copy: short, matter-of-fact, precise. Strong narrative headings followed by specific scientific context. Avoid “unlock”, “revolutionary”, “AI-powered next-gen”, fake live dashboards, fabricated counts or ornamental status labels.

## Layout language

Intro and mission choice can be expansive, immersive and editorial. The Explorer should have one dominant map, a ranked result surface and a persistent or adjacent evidence area, with a compact active-mission header. Desktop uses an intentional split or layered drawer without covering essential map controls. On mobile: map, results and evidence can stack or open as accessible panels; preserve clear return navigation. Do not permanently waste half the screen on a blank detail placeholder.

## Anti-slop guardrails

No ubiquitous purple gradients, neon cyberpunk grids, decorative starfield particles, dashboard KPI filler, repeating identical cards, fake terminal text, glass over everything, oversized rounded pills, unexplained animations, generic icon tiles, fake loading/progress sequences, dashboard labels without real data, or giant empty areas. Space imagery must communicate scale or mission context rather than merely decorate. Use numbering for narrative progress only if it has a navigational purpose; do not label every component with arbitrary chapter numbers.

## Definition of wow

One coherent signature moment: the user's chosen planetary task transitions into an Earth search, and a clicked terrestrial site exposes the evidence that makes it comparable or not. The reveal must depend on a real interaction and real data. A static fallback must communicate the same meaning. The interface is successful when a judge remembers the scientific proposition, not simply the animation.
