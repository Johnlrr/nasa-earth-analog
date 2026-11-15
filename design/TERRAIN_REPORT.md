# Compare two worlds → Explore beyond the surface

Implemented both user references as one connected sequence in the existing Similarities view. Earth is consistently left/amber, target right/blue. Larger verified imagery and source labels lead into an interactive 2D terrain laboratory, rather than a fabricated shared planetary horizon or ornamental 3D scene.

## Data acquired and preserved

Verified the user's existing Google Earth Engine connection without exposing credentials. Acquired Sentinel-2 SR Harmonized 2023 RGB median composites for the exact nominal 4 km Earth windows E10K_453_921 and E10K_691_-680. Cloud/shadow masking excludes SCL 3/8/9/10; snow is retained. An initially clipped white rendering was rejected during inspection and regenerated with a documented wider display range. Neither image supplies a new score. Collection, dates, scene counts, bounding geometry, band/render parameters and Copernicus attribution are recorded in `web/media/expedition/footprints/sources.json`. Public static image files are served; site visitors do not need an Earth Engine account.

Terrain: existing NASA PGDA 78 Connecting Ridge 5 m DEM, new public Copernicus GLO-30 COG covering Da Qaidam's exact coordinates, and one matching existing Earth cache. Source raster checksums, crop/sample indices or coordinates, source URLs and approximate horizontal sampling method appear in `web/media/terrain/sources.json`. The terrain window is nominally 4 km, displayed on 50 m samples for the main pair. New terrain samples and visuals do not replace any original scoring descriptors. No source scientific dataset, threshold, classification or calculation was modified.

## Interaction

The terrain inspector supports hillshade, a display-grid slope layer (degrees), 100 m contours, a movable A–A′ section, surface click selection, and a cursor linked between the elevation plot and both raster views. Range controls provide keyboard operation. The elevation chart is an accessible scroll region on small screens. Native/source resolution, footprint and provenance stay visible. Missing DEMs produce a compact unavailable state; they are never inferred from a photograph.

Profiles show **height relative to the first valid sample of each transect**, with raw source heights in the readout. Different planetary/Earth vertical datums are not conflated. Raster-column sections are independent, not identical geographic azimuths or surveyed traverses. Local Earth horizontal distances are approximate. Slopes and contour interpolation use the display grid and are not engineering-grade hazard or displacement measurements. No unsupported risk classes, vectors, cracks, stability assessment or vertical exaggeration were added.

## Verification and review

20/20 Node checks passed, including missing-value profiles and known flat/45° slope grids. Real browser checks: Explorer 57/57, Similarities 27/27, new terrain 16/16; reduced-motion terrain run also 16/16. Covers layers, contour toggle, transect changes, real distance readout, selection preservation, absent DEMs and 1440/768/390/320 page overflow. Ruff, JS syntax, whitespace checks and existing static assembly passed. Python scientific pytest remains subject to the previously reported environment limitation; no new pytest pass or marketing Taste gate pass is claimed.

Screenshots inspected at 1440, 768 and 390: `web/.taste-skill/after/terrain-1440.png`, `terrain-768.png`, `terrain-390.png`. A polish pass made DEM canvases occupy their columns, strengthened contour contrast and made the profile scrollable with legible axis labels on phones. Captured browser results: `terrain-regression.png`, `terrain-similarities.png`, `terrain-checks.png`, `terrain-reduced.png`.

Live preview was replaced on **http://localhost:8000**. Homepage, terrain controller, DEM grids and footprint-image manifest all verified HTTP 200. Open Explorer → Compare Moon & Earth terrain. The complete original technical tables, validation roles, comparison signature, campaign exports and Analog Test Card remain available.
