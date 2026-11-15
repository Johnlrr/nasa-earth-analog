# Similarities — terrain pair and detailed criteria

Implemented the user's follow-up from both `act-04-similarities.png` and `act-04-similarities-2.png`. Their useful principle is a clearly labelled target/Earth landscape pair followed by measurable criteria; the reference screenshots themselves are not production imagery.

The Explorer now has **Compare Moon & Earth terrain**, opening the actual Da Qaidam site. Its Similarities view displays the verified Connecting Ridge LOLA hillshade and Da Qaidam Sentinel-2 review thumbnail side by side. Captions identify sensor, modality, nominal footprint, missing acquisition dates and source. Image pixels and original proportions are retained. No invented ground photography, registration claim, calibrated scale bar or image-derived similarity is introduced.

For site groups, a selector binds a published member cell to its exact recorded target and lens. Da Qaidam exposes all 11 L1 source descriptors. Switching to a target/member without a published detailed cell displays that absence instead of borrowing another footprint's numbers or photo. A button opens an available member directly in the canonical map/list lens. Direct candidate selection and full Test Card behavior remain connected to the same engine state.

Numeric columns now show source Earth/target values and aligned bars using the same domain within each row, the original z, and an exact Earth-minus-target difference. Negative values are supported. Missing values receive neither bars nor deltas. Tiny environmental values use scientific notation, so lunar pressure is not rounded into a fabricated zero. Slope cutoffs are explicitly not vehicle safety limits.

Two additional tables make engineering gaps visible:

- **Measurements still needed:** atmospheric relative humidity, volumetric soil moisture, local surface temperature, soil bearing strength/traction, and the source record's unobserved criteria. These are explicitly unavailable where the current catalog provides no paired measurement. X1 aridity P/PET is not relabelled as humidity or soil moisture.
- **Planetary environment:** exact values, units, consequences, mitigations and citations from `data/ledger.json`, filtered to the relevant body/lens. These are marked as planetary/literature references, not local footprint measurements or additions to the terrain score.

The existing Jezero CTX chip is also available when the selected M1 target is Jezero margin. Its 5 km extent, approximate 10.16 m/pixel resolution and black missing-coverage pixels are disclosed. No unrelated Earth image is substituted when the catalog lacks an image for that cell.

Files: `web/similarities.js`, `expedition.js`, `expedition.css`, `index.html`, `explorer.html`; read-only ledger exposure in `app.js`; `media/expedition/jezero-margin-ctx.png` and `similarities-sources.json`. No scientific dataset, score, threshold, ordering or classification changed.

Verification: **15/15 Node tests**, **57/57 existing Explorer browser checks**, **24/24 new Similarities browser checks**, JavaScript syntax, Ruff and static site assembly passed. New checks cover exact member/target binding, real image loading, all 11 descriptors, shared row scales, moisture gaps, tiny pressure, context changes, missing-source behavior, image failure, canonical footprint navigation, evidence/back, keyboard scroll regions and page overflow at 1440/768/390/320. Source images and the numeric tables were inspected in actual screenshots at desktop/tablet/mobile widths. One polish pass removed a repeated headline so the images appear earlier.

Screenshots: `web/.taste-skill/after/similarities-1440.png`, `similarities-768.png`, `similarities-390.png`; browser results in `similarities-checks.png` and `similarities-regression.png`. Asset/measurement provenance and display math: `web/media/expedition/similarities-sources.json`. The existing Taste marketing gate limitation and Python environment lacking numpy remain as reported in `IMPLEMENTATION_REPORT.md`; no new gate or pytest pass is claimed.

Preview with `python scripts/build_site.py --serve 8000`, open Explorer and press **Compare Moon & Earth terrain** or select Da Qaidam in Sites.
