# Compliance — NASA Space Apps 2026 (DRAFT)

Owner: Linh (B). Status: **draft prepared by an AI agent for the team to verify**. Item 0.1 in PLAN
is done only when both members have read the official texts, made the G0 decision and signed below.

## 1. Official texts to read (not yet verified against the originals)
- [ ] Project Submission Guide (released 13/11/2026) — demo format, required fields
- [ ] Judging & Awards Guide — five criteria, equal weight
- [ ] FAQ 2026, section on Super Intelligence (SI) tools
- [ ] Challenge page: Resources tab, the 12 "Potential Considerations"
- [ ] Participant Terms & Conditions 2026 (licence, minors, commercial content)

Facts below come from `ABOUT.md` (secondary summaries), **not** from the originals:

| Rule | Value per ABOUT.md | Verified? |
| :--- | :--- | :--- |
| Deadline | 23:59 15/11/2026, Team Owner's local event time | [ ] |
| Portal | Project tab on spaceappschallenge.org only | [ ] |
| Demo | ONE public link: ≤ 7 slides incl. cover, OR video ≤ 30 s; English | [ ] |
| Data | Must use and explain NASA / partner-agency data; cite all sources | [ ] |
| SI (AI) | Must disclose how SI was used; local summary: SI must not generate the core idea | [ ] |
| Licence | OSI licence (default Apache-2.0) | [ ] |
| Minors | No photos / video / voice of under-18s in demo or team page | [ ] |

## 2. G0 decision — SI and originality (R0 in DESIGN)
Risk: `DESIGN.md` (solution architecture) was drafted with an AI model, from `ABOUT.md` and the
team's prompt. If the official guide forbids SI-generated core ideas, the team must decide which
ideas are its own, change or drop the rest, and disclose truthfully.

- [ ] Official wording read (quote it here): …
- [ ] Decision: continue / adjust ideas (describe): …
- [ ] Ideas the team claims as its own: …

## 3. SI use so far (factual log, to adapt for the Project page)
- Research and planning documents (`ABOUT.md`, `DESIGN.md`, `PLAN.md`) drafted with Claude models
  (Anthropic) under team direction; reviewed and edited by the team.
- Code: written with AI coding agents (Claude Code; Antigravity / Gemini) under team supervision;
  every module has unit tests; scientific choices and thresholds recorded in `progress.md` /
  `PLAN.md` with the reason and whether they were decided before or after seeing results.
- Literature / number checks: AI agents searched and quoted sources; every number in
  `ledger/*.yaml` carries a URL or DOI that was opened.
- No SI-generated images, voices or videos in the demo (to keep true).

Draft disclosure text for the Project page (edit before use):
> We used AI assistants (Anthropic Claude, Google Gemini) to help draft planning documents, write
> and test code, and search the literature. All data processing runs on NASA and partner data with
> open code in this repository; every scientific threshold, control site and expectation was
> fixed by the team and is recorded with its rationale. Results were checked by the team.

## 4. Data used (for the "NASA data" field)
- NASA EMIT L2A surface reflectance (via Google Earth Engine `NASA/EMIT/L2A/RFL`)
- MRO CRISM MICA type spectra (PDS Geosciences, MROCR_8001)
- NASA PGDA Product 78 (LOLA south-pole DEM), LRO data via Moon Trek
- MRO CTX mosaic via NASA Mars Trek; MODIS (MOD11A1, MOD11A2, MOD13A2); ASTER GED AG100
- SWIM (Mars subsurface water ice), NASA planetary fact sheets, Chang'e-4 LND / MSL RAD papers
- Partner / other open data: Copernicus GLO-30 DEM, ESA WorldCover, ERA5-Land (Copernicus),
  TerraClimate, OpenAlex (attention index), OpenStreetMap Nominatim (place names)

## 5. Pre-submission checklist (5.2)
- [ ] Every link (slides, repo, web) opens in a private window, no login
- [ ] Slides ≤ 7 incl. cover (or video ≤ 30 s), English
- [ ] No under-18 photos / voices anywhere
- [ ] Members tab: everyone verified, same local event
- [ ] Project page fields complete in English (summary, challenge, NASA data, SI disclosure,
      originality, T&C)
- [ ] Licence file present (Apache-2.0), README cites all data
- [ ] Submitted before 21:00 15/11, screenshot saved

## Signatures
- Bảo (A): ______  date ______
- Linh (B): ______  date ______
