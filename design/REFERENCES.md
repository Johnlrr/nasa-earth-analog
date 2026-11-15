# References — learn the principles, not the pixels

Prioritize the four core references and local storyboard captures. This is a curated reference brief, not permission to copy designs/assets. Public pages were identified from their documentation/project descriptions; the coding agent should inspect actual examples where browser access permits and record which examples it could open. If offline, use the local captures and written direction. Do not invent details from inaccessible pages.

## Core references

| Reference | What to study | Apply to | Do not copy |
|---|---|---|---|
| [NASA Eyes](https://science.nasa.gov/eyes/) | Free exploration of real scientific data/imagery; spatial context and meaningful controls | Acts II–IV: mission selector, map and science-first exploration | NASA branding, exact 3D interface, or a new 3D engine requirement |
| [Outreach — Rocani Studio](https://rocani.studio/work/outreach), [Studio Gruhl case study](https://www.studiogruhl.com/projects/outreach) | Chapter-based cosmic narrative, atmosphere, curiosity-led interactions | Acts I–II: scale, visual mood, transitions | Its fictional storyline, specific visuals, WebGL complexity, or speculative science |
| [The Pudding](https://pudding.cool/), [methods and resources](https://pudding.cool/resources/) | Question-driven visual essays; progressive evidence; visuals that answer specific questions | Acts III–V: question → candidate → comparison → limitation | Arbitrary charts, editorial templates or unrelated datasets |
| [Apple iPhone](https://www.apple.com/iphone/) | Product hierarchy and deliberate visual sequencing; inspect an individual current product page if accessible | Acts I–II: typography, restraint, single visual focal point | Product branding, exact layouts, expensive videos, or converting Explorer into a sales page |

## Functional and technical references

- [Mapbox Storytelling](https://github.com/mapbox/storytelling) and [scroll-to-map example](https://docs.mapbox.com/mapbox-gl-js/example/scroll-fly-to/): chapters connected to map views, camera continuity and information reveal. Borrow the *pattern*, keep existing Leaflet (if confirmed); do not introduce a Mapbox token or migration.
- [Taste Skill prompt guide](https://www.tasteskill.dev/guide#redesign) and [documentation](https://www.tasteskill.dev/docs): inventory the real UI, preserve stack and behavior, capture before/after. Use page flow for optional narrative and the app-screen flow for interactive Explorer.
- [GSAP ScrollTrigger](https://gsap.com/docs/v3/Plugins/ScrollTrigger/): optional scroll choreography. Refer to current installed version docs; native CSS/JS is the default for simple effects.
- [NASA Images and Media Guidelines](https://www.nasa.gov/nasa-brand-center/images-and-media/): authoritative asset usage guidance and media resources. Verify each asset's exact credit, third-party rights and permitted usage. No implied NASA endorsement or unauthorized NASA branding.

## Local moodboard mapping

| File in `reference-images/` | Intended lesson |
|---|---|
| `current-ui.png` | Earlier operational prototype; functional requirements and pain points, not final art direction |
| `act-01-mission.png` | Planetary imagery, dramatic negative space, opening hierarchy |
| `act-02-choose-mission.png` | Mission and planet choice, visual affordances |
| `act-03-search-earth.png` | Map-first discovery, spatial context |
| `act-04-similarities.png` | Earth/planet comparison, meaningful data explanation |
| `act-05-evidence.png` | Scientific dossier and evidence hierarchy |

These captured storyboard screenshots were mentioned by the user but not delivered with this kit. The coding agent must read the actual files if supplied; common image extensions and multiple numbered variants are fine. They are inspiration only, not evidence, source imagery, or literal layout specifications. Never embed screenshots of third-party websites as production assets without rights.

## Asset acquisition brief

- Act I: one high-quality, credited real planetary horizon or terrain image; choose based on composition and readability. Moon/Mars context must be labeled accurately.
- Act II: real labeled planet imagery with consistent crops, sufficient contrast and meaningful alt text.
- Act III: reuse existing map basemap imagery and attribution, avoid extra heavyweight media.
- Act IV: use only genuine, correctly labeled candidate/target imagery when available. Generic context may be used only if clearly labeled and not presented as measured comparison. If missing, prioritize feature evidence.
- Act V: real evidence fields and sources; no decorative fake documents.
- Store permitted local assets and their provenance in the appropriate existing assets directory (or `assets/credits.json`), including local path, original URL, creator/agency, license/usage terms and caption. Do not hotlink unverified media, embed unknown images as data, use generated imagery as observation, or add NASA marks implying affiliation. If asset sourcing fails, use a clean text/data-first fallback.

## Reference extraction deliverable

Before coding, write a brief mapping in `design/IMPLEMENTATION_PLAN.md`: for each core reference actually inspected, note one compositional rule, one interaction principle and where it applies. List which local images were present. Select a single visual direction consistent with `ART_DIRECTION.md`; do not merge several website layouts into a collage. References can guide aesthetics; existing scientific code is the authority for facts.
