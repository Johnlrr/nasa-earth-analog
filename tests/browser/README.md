# Browser verification

These fixtures load the actual application in a same-origin iframe. They are test code, not deployment assets or a second implementation of the UI. Run from the repository root using the installed design-taste-frontend skill's own runner, one browser at a time:

```powershell
node <skill>/scripts/shoot.mjs --url tests/browser/expedition.html --root . --w 1440 --wait 6000 --out web/.taste-skill/after/browser-checks.png --profile web/.taste-skill/chrome-qa --no-tiles
node <skill>/scripts/shoot.mjs --url tests/browser/expedition.html --root . --w 1440 --reduced --wait 6000 --out web/.taste-skill/after/browser-reduced.png --profile web/.taste-skill/chrome-qa --no-tiles
node <skill>/scripts/shoot.mjs --url tests/browser/campaign.html --root . --w 1440 --out web/.taste-skill/after/campaign-checks.png --profile web/.taste-skill/chrome-qa --no-tiles
```

Inspect the rendered PASS/FAIL list. Expedition reports its total and exposes `window.qaResults` plus `html[data-ready=passed|failed]`. It includes controlled failure, empty, delayed and missing-value responses in isolated test frames; the production data files remain untouched. Campaign exercises local drafts and intercepts download blobs to inspect their contents without opening files. Local screenshots are excluded by the production build.

For manual inspection, serve the repository root with a local HTTP server and open `/tests/browser/expedition.html` or `/tests/browser/campaign.html`. Serve the shipped application through `python scripts/build_site.py --serve 8000` so document and figure links are assembled too.
