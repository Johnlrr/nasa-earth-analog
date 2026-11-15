# Compliance — NASA Space Apps 2026

Owner: Linh (B). Status: **official texts read and quoted (15/11/2026, 16:30); decision and
signatures still open — only the two team members can make them.** An SI agent fetched and quoted
the pages below; it did not decide or sign anything. Item 0.1 in PLAN is done only when both
members have read these quotes (or the pages), made the G0 decision and signed.

## 1. Official texts (read on 15/11/2026; verbatim quotes)
- [x] Project Submission Guide — https://www.spaceappschallenge.org/resources/project-submission-guide/ (dated November 13, 2026)
- [x] Judging & Awards Guide — https://www.spaceappschallenge.org/resources/judging-awards-guide/
- [x] Participant FAQs (SI section) — https://www.spaceappschallenge.org/resources/participant-faqs/
- [x] Participant Terms & Conditions 2026 — https://www.spaceappschallenge.org/legal/
- [ ] Challenge page: Resources tab, the 12 "Potential Considerations" (not re-read today)

| Rule | Official wording (quote) | Our status |
| :--- | :--- | :--- |
| Deadline | "Project submission closes on Sunday, November 15 at 11:59 p.m. in accordance with the time zone of your team's Local Event." | Team target 21:00 (earlier, by choice) |
| Demo | "either in the form of a 7-slide presentation (including title and introductory slides) or a 30-second or less video presentation" · "Projects that exceed these limits will not be eligible for Global Judging." | 7 slides incl. cover, PDF: `slides/SIMILITUDE-slides.pdf` |
| Public links | "share a publicly accessible link with no logins, permissions, or registrations required. If judges can't access your project, it can't be evaluated" | Pages + GitHub, public; check in a private window before submitting |
| Language | "You must use English language on the project submission page and in any linked materials." · "Slide decks must be in English." | Slides, web, project text in English |
| NASA data | "To be eligible for a Global Award, you must use at least one NASA data or resource." | Many (LOLA/PGDA 78, EMIT, CRISM, SWIM, MODIS, NASADEM…) |
| References | "List all of the data, resources, and tools used in your project. Resources should include any code, text, and images (even if they are open source or freely available)" | `docs/project_page.md` + README + `ledger/*.yaml` |
| Originality checkbox | "I confirm that the submitted project represents my team's original work and that all external resources including code, text and images … used in the project are listed in the References field of the project submission form. In creating our solution, my team has not used any copyrighted materials … that we don't have permission to use." | ⟨TEAM⟩ ticks it only if true |
| SI use (permitted) | "The use of SI tools, such as machine learning, chatbots, image generation, and large language models, is permitted … SI should not be used to (come up with your idea of how to solve the challenge)." | **See §2 — team decision** |
| SI marking | "Generated content may not use, contain, or modify any NASA branding or design elements (such as the NASA logos, flags, or mission identifiers). We require that you clearly indicate where and how SI tools were utilized in your project, including: … Images and videos: Must include a visible watermark to indicate SI generation. … Code and data: Must acknowledge SI generation in descriptive text and metadata." | No NASA logo on slides/web; SI use stated on web footer, slide 7, project text and README ("Use of AI (Super Intelligence) tools") |
| SI form answer | "This SI question is for data-collection purposes only, and your response will not be seen by the judges. However, judges will be able to see any SI-generated indicators within your project" | Draft answer in `docs/project_page.md` |
| Licence | "any original content … is freely available without restriction or is licensed as open source as defined by the Open Source Initiative (OSI). If you do not specify a specific OSI compliant license, NASA will distribute your original content under an Apache 2.0 license." | `LICENSE` Apache-2.0 |
| Minors | "Recognizable names, voices, and likenesses of persons under the age of 18 should not be included in any submission." | No people in slides or web |
| Judging | "five criteria: Impact, Creativity, Validity, Relevance, and Presentation" | — |

## 2. G0 decision — SI and originality (R0 in DESIGN) — ⟨TEAM⟩
The official guide says SI "should not be used to (come up with your idea of how to solve the
challenge)". Facts recorded in this repository that bear on it:
- `DESIGN.md` (solution architecture) was drafted with an SI model (Fable) from `ABOUT.md` and the
  team's prompt (`AGENTS.md` roles; header of `DESIGN.md`).
- `docs/handoff_2e.md` and `docs/submission_kit.md` record that SI assistants proposed analysis
  directions that were adopted (results by field site, reading beside NASA requirements, second
  DEM, larger null sample).
- Thresholds, controls and rule changes are logged with dates in `PLAN.md`, `progress.md` and the
  Deviations table.

What the team has to decide and write here (an SI agent must not fill this in):
- [ ] Who originated the core idea (judging analog sites by which test results transfer, per
      mission test), and what SI contributed: …
- [ ] Decision: submit as is with a truthful statement / adjust the claim / other: …
- [ ] The SI answer in `docs/submission_kit.md` ("Core idea" line) filled with the same facts.

## 3. SI use (factual log, for the Project page)
- Planning documents (`ABOUT.md`, `DESIGN.md`, `PLAN.md`) drafted with Claude models (Anthropic)
  under team direction; reviewed and edited by the team.
- Code written with SI coding agents (Claude Code; Antigravity / Gemini) under team supervision;
  unit tests for every module; scientific choices and thresholds recorded in `progress.md` /
  `PLAN.md` with reason and whether decided before or after seeing results.
- Literature and number checks: SI agents searched and quoted sources; every number in
  `ledger/*.yaml` carries a URL or DOI.
- Web page, slide layout and slide text drafted by an SI agent from the pipeline tables; every
  number is filled by script from `docs/slide_numbers.json`.
- No SI-generated images, voices or videos (figures are Matplotlib plots of our data).

## 4. Data used (for the "NASA Data" and "Partner Data and Other References" fields)
See `docs/project_page.md` (generated from `docs/submission_kit.md`).

## 5. Pre-submission checklist (5.2)
- [x] Slides ≤ 7 incl. cover, English (`slides/SIMILITUDE-slides.pdf`, 7 pages, checked 15/11)
- [x] Web app and Evidence page load on the public URL (desktop and phone width; `progress.md`)
- [ ] Every link (slides, repo, web) opens in a private window, no login — ⟨TEAM, last check⟩
- [x] No under-18 photos / voices anywhere (no people in slides or web)
- [ ] Members tab: everyone verified, same local event — ⟨TEAM⟩
- [ ] Project page fields complete in English (text ready in `docs/project_page.md`) — ⟨TEAM⟩
- [x] Licence file present (Apache-2.0)
- [x] README states where SI was used ("Use of AI (Super Intelligence) tools" section)
- [ ] Submitted before 21:00 15/11, screenshot saved — ⟨TEAM⟩

## Signatures (only the members themselves)
- Bảo (A): ______  date ______
- Linh (B): ______  date ______
