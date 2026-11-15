# SIMILITUDE interface review — field dossier revision

Scope: apply the user's explicit anti-slop brief to the existing five-stage campaign interface. Vanilla HTML/CSS/JS, original datasets, calculations, explorer and export formats retained.

## Visual direction fixed before implementation

An engineering field dossier: warm paper (#f5f4ee), dark blue-green ink (#1c3239), restrained green selection (#244f48), ochre for unresolved evidence (#805215). Chivo for reading; Chivo Mono for identifiers and provenance. Square study windows, ruled comparison rows and a printable evidence record connect the interface to field planning. Colour always accompanies a text state. Reusable type, spacing, colour, border/radius and 120 ms motion tokens live at the top of campaign.css.

The user's latest instructions supersede the previous skill's mandatory marketing effects, screen-height sections and repeated visual panels. The old marketing-template gate is not used as evidence for this revision; no gate pass is claimed.

## Critique and fixes

Reviewed from the perspective of a designer assessing another author's interface; this is an internal critique, not an independent external designer's endorsement.

1. Before: five large dark marketing bands forced routine input into long screens. After: content determines section height; rules and numbered steps carry the workflow.
2. Before: three equal cards implied equivalent evidence and repeated thumbnail/status/button scaffolding. After: study records form rows with distinct footprint, evidence/limitations and selection columns. Thin polar imagery retains its native aspect ratio.
3. Before: liquid-type, entrance animation, hover lifts and dark framed preview were decorative. After: no motion library loads, no gradients/glass/glows, no emoji icons, no card shadows. Hover changes only control colour; focus is a visible ochre outline.
4. Before: repeated outlined badges competed with the data. After: plain evidence labels with a small square signal; meaning stays in text.
5. First revision on mobile exposed incorrect matrix reading order caused by grid auto-placement. Fixed with explicit row/column placement: criterion first, status beside it, explanation below.
6. First review found ambiguous arrow-only source links and generic disabled downloads. Fixed with Map/Source text and a specific explanation identifying the missing footprint or objective.
7. Selection keeps row geometry stable; a left rule and background accompany aria-pressed and the remove action.
8. Loading exposes aria-busy; a failed request ends loading, raises an alert and leaves export disabled. Empty objectives name the next step. Notes are escaped in exported HTML.

## Validation

- Actual headless Chrome captures inspected: desktop 1440, tablet 768 and mobile 390.
- 23 browser interaction checks pass: existing example, add/remove, per-variable evidence, persistence, two export blobs, dataset hash, escaped user notes, no invented route, task change, menu/Escape, loaded images, no horizontal overflow at the checked width, empty/restored objectives, long names, visible keyboard focus, no decorative runtime and controlled data-load error.
- Browser report: web/.taste-skill/shots/dossier-interactions.png.
- Node regression tests: 5/5 pass. JS syntax, ruff, git diff --check and static site build pass.
- Text contrast on paper: body 12.18:1, secondary 5.68:1, modelled 6.98:1, unresolved 6.08:1. Primary button 9.18:1. All exceed 4.5:1.
- Existing Python scientific suite remains unavailable in this Python environment because numpy is missing; no scientific code changed.
- No performance, scientific-validity or user-impact metric was invented. Existing imagery still has the nominal-scale/georeferencing limitation stated in provenance.

Screenshots: web/.taste-skill/shots/dossier-final-1440.png, dossier-768.png, dossier-final-390.png. These are ignored local review files, not production dependencies.
