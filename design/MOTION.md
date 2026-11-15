# Motion direction — purposeful cinematic transitions

Motion is an explanatory layer, not the product. Target smooth, responsive interaction. The intervals below are design suggestions, not hard timing or performance guarantees. No user should have to wait for a sequence to finish to access the tool.

| Moment | Proposed motion | Suggested timing | Fallback |
|---|---|---|---|
| Act I entry | Image + text reveal, subtle depth | 500–800 ms, one pass | Static composition |
| I → II | Leave headline, reveal task area | 250–450 ms | Immediate navigation |
| Planet/lens selection | Active border, image or text crossfade | 150–300 ms | Immediate selection |
| II → III signature | Target fades into Earth imagery/map frame; then fit map to actual coverage/results if useful | 650–1000 ms max for visual sequence | Direct map + active lens |
| Marker/list selection | Linked highlight, optional map pan/zoom, panel enters | 180–350 ms UI; map native timing | Immediate update / setView |
| III → IV | Evidence panel expands or opens adjacent to map | 220–350 ms | Instant disclosure |
| IV → V | Dossier expands, preserve selection | 180–300 ms | Native disclosure |
| UI hover/focus | Clear outline/color feedback | 100–180 ms | Immediate style |

## Signature choreography (P0 lightweight)

1. User presses Find Earth analogs; real lens selection is applied immediately.
2. Mission visual crossfades to real Earth imagery or directly into map container. Preserve a stable mission label as a visual anchor. Use existing map tile imagery or properly credited media; a static Earth asset is sufficient. Never suggest a real-time processing operation that does not exist.
3. Explorer is interactive as soon as available. If data is still loading, show an honest status rather than holding the scene. Move camera only after actual coordinates/coverage are known, if suitable; no artificial global scan. Reveal real results from current request.
4. Clicking a site highlights it in both representations and opens explanation; don't animate the numerical score from zero, which may momentarily communicate false values.

## Vanilla implementation

- Prefer CSS transitions, Web Animations API and IntersectionObserver for simple reveal; keep content visible by default before JS attaches. Use the current Leaflet map's own pan/zoom methods where supported; call `invalidateSize()` after a map container resize if applicable.
- Optional GSAP: use a scoped timeline for the signature moment, ScrollTrigger only for the optional guided intro, not the live map. See `REFERENCES.md` for official documentation. Avoid adding both CSS and GSAP animation on the same property. Register plugins only when used; dispose of old timelines/listeners and cancel animation on view/lens change. Respect `gsap.matchMedia()` / `prefers-reduced-motion` where relevant.
- Keep interactions interruptible. Users can navigate, change lens, skip, and return while an effect is running. Never override map-driven zoom or scroll. No scroll hijacking, required pinned scenes on phone, forced camera flights after every click, infinite particles, sound autoplay, or full-screen fake loading screens.
- Animate opacity and transform where possible; avoid animating large blur, layout-heavy properties or many map markers. Load a small first image/poster early, lazy-load later media. Use CSS-only no-motion fallback and persistent focus-visible state. Do not hide data behind an animation completion callback.

## Validation

Inspect mid-transition, final state, rapid repeated clicks, resizing, slow data, failed image/network and reduced-motion. Under reduced-motion disable cinematic moves, parallax and animated map flights while preserving every action and field. Keyboard focus must land on the new view or evidence heading when appropriate and return to the trigger on close. Never add motion just to pass an inspector's decorative animation count.
