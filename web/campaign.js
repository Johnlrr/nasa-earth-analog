/* Presentation-only campaign builder. Reads the existing study; never writes scientific verdicts. */
(function () {
  'use strict';
  const TARGET = 'connecting_ridge';
  const STORAGE = 'similitude.review-draft.v1';
  const REPORT = 'https://github.com/Johnlrr/nasa-earth-analog/blob/main/docs/validation_report.md';
  const CATALOG = [
    { id: 'site:E10K_453_921', title: 'Da Qaidam', location: 'Qinghai, China', image: 'media/qaidam-4km.png', label: 'Terrain study', limit: 'A terrain reference. Access and collaboration require review; no field permission is established.' },
    { id: 'site:E10K_729_-319', title: 'Peary Land', location: 'North Greenland', image: 'media/peary-4km.png', label: 'DEM-sensitive', limit: 'This footprint leaves the robust set with ArcticDEM. Treat the terrain result as sensitive.' },
    { id: 'site:E10K_244_-1498', title: 'Mauna Loa–Mauna Kea', location: 'Hawaiʻi, United States', image: 'media/hawaii-4km.png', label: 'Shadow study', limit: 'Terrain-shadow evidence only. Sun geometry, camera response and site access remain unresolved.' }
  ];
  const OBJECTIVES = [
    { id: 'terrain', title: 'Slope & roughness', variable: 'slope_roughness', lens: 'L1', missing: 'No selected footprint has this modelled match.' },
    { id: 'shadow', title: 'Terrain shadows', variable: 'shadow_casting', lens: 'L2', missing: 'Add a shadow-study footprint or record a separate test setup.' },
    { id: 'lighting', title: 'Lighting & camera response', missing: 'Measure contrast and exposure; specify a time window or calibrated lighting setup.' },
    { id: 'obstacles', title: 'Small obstacles & soil', missing: 'Survey small hazards and soil properties before selecting a route.' },
    { id: 'gravity', title: 'Reduced-gravity traction', missing: 'Define a separate controlled test. Field terrain does not validate reduced-gravity traction.' }
  ];
  const SURVEYS = [
    { id: 'access', label: 'Confirm site permission and access' },
    { id: 'route', label: 'Survey a proposed traverse corridor' },
    { id: 'soil', label: 'Measure small obstacles and soil' },
    { id: 'light', label: 'Measure lighting and camera response' }
  ];
  const LIMITS = [
    'Draft for review only; no field qualification, flight readiness or TRL is assigned.',
    'Evidence is per variable and footprint. Combining sites does not establish joint terrain–lighting coverage.',
    'The 30 m terrain baseline does not resolve metre-scale obstacles or establish soil strength.',
    'No access permission, safe route, weather forecast, lighting window or hardware performance has been verified.',
    'Peary Land is sensitive to the elevation model; see validation report section 7c.',
    'Checklist entries are planned survey work, not completed verification.'
  ];
  const escape = value => String(value ?? '').replace(/[&<>"']/g, c => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' })[c]);
  const defaults = () => ({ task: 'navigation', selected: [], objectives: ['terrain', 'shadow', 'lighting', 'obstacles'], name: 'Connecting Ridge · navigation review', route: '', assumptions: '', surveys: SURVEYS.map(x => x.id) });
  function cleanState(value) {
    const s = defaults();
    if (!value || typeof value !== 'object') return s;
    s.task = value.task === 'terrain' ? 'terrain' : 'navigation';
    for (const [key, valid] of [['selected', CATALOG.map(x => x.id)], ['objectives', OBJECTIVES.map(x => x.id)], ['surveys', SURVEYS.map(x => x.id)]]) {
      if (Array.isArray(value[key])) s[key] = [...new Set(value[key].filter(x => valid.includes(x)))];
    }
    for (const key of ['name', 'route', 'assumptions']) if (typeof value[key] === 'string') s[key] = value[key].slice(0, key === 'name' ? 100 : 2000);
    return s;
  }
  function catalogFrom(data) {
    if (!Array.isArray(data?.features) || data.metadata?.mock || data.metadata?.provisional) throw new Error('Published, non-provisional study records are required.');
    return CATALOG.map(display => {
      const feature = data.features.find(f => f.properties?.id === display.id && f.properties?.feature_type === 'site');
      if (!feature) return null;
      const fields = (feature.properties.field || []).filter(r => r.target === TARGET && ['L1', 'L2'].includes(r.lens));
      if (!fields.length) return null;
      const cells = fields.map(r => data.features.find(f => f.properties?.id === r.lens + '-' + r.best_cell)).filter(Boolean);
      return { ...display, feature, fields, cells };
    }).filter(Boolean);
  }
  function matrix(state, catalog) {
    return OBJECTIVES.filter(o => state.objectives.includes(o.id)).map(o => {
      const matching = catalog.filter(c => state.selected.includes(c.id) && c.fields.some(f => f.variable === o.variable && f.lens === o.lens));
      return { id: o.id, title: o.title, state: matching.length ? 'modelled' : o.id === 'gravity' ? 'facility_needed' : 'unresolved',
        label: matching.length ? 'Modelled evidence' : o.id === 'gravity' ? 'Facility needed' : 'Evidence gap',
        sites: matching.map(c => ({ id: c.id, title: c.title, caution: c.limit })),
        note: matching.length ? matching.map(c => c.title + (c.id === 'site:E10K_729_-319' ? ' (DEM-sensitive)' : '')).join(' · ') : o.missing };
    });
  }
  function evidencePack(state, catalog, data, hash) {
    return {
      schema_version: 'similitude.review-draft/1', created_utc: new Date().toISOString(), status: 'review_draft',
      campaign_name: state.name.trim() || 'Untitled campaign', task: state.task, target: TARGET,
      source: { file: 'web/data/candidates.geojson', generated: data.metadata.generated, sha256: hash, validation_report: REPORT, metadata: data.metadata },
      test_matrix: matrix(state, catalog),
      selected_footprints: catalog.filter(c => state.selected.includes(c.id)).map(c => ({
        id: c.id, name: c.feature.properties.name, caution: c.limit,
        matching_evidence: c.fields, footprint_records: c.cells,
        footprint_location_status: c.cells.length ? 'cell_records_available' : 'exact_cell_coordinates_not_in_web_catalog',
        region_record: c.feature, geometry_note: 'Use footprint_records for cell locations. The region record is a group representative, not a traverse route.'
      })),
      proposed_route_or_setup: { status: 'user_notes_unverified', notes: state.route.trim() || 'Not specified. Site survey required.', geometry: null },
      assumptions: state.assumptions.trim() || 'No additional assumptions recorded.',
      reconnaissance: SURVEYS.map(x => ({ ...x, included_in_plan: state.surveys.includes(x.id), verification_status: 'not_verified' })),
      limitations: LIMITS,
      source_links: [REPORT, 'https://pgda.gsfc.nasa.gov/products/78', 'https://doi.org/10.5270/ESA-c5d3d65', 'https://github.com/Johnlrr/nasa-earth-analog/blob/main/docs/test_protocols.md']
    };
  }
  function briefHTML(pack) {
    const e = escape;
    const table = pack.test_matrix.map(r => '<tr><th>' + e(r.title) + '</th><td>' + e(r.label) + '</td><td>' + e(r.note) + '</td></tr>').join('');
    const sites = pack.selected_footprints.map(s => '<article><h3>' + e(s.name) + '</h3><p>' + e(s.caution) + '</p>' + s.footprint_records.map(f => '<p>Study cell ' + e(f.properties.id) + ' · ' + e(f.properties.footprint_km) + ' km footprint · ' + e(f.geometry.coordinates.join(', ')) + ' (longitude, latitude).<br>' + e(f.properties.evidence_note) + '</p>').join('') + '<ul>' + s.matching_evidence.map(r => '<li>' + e(r.variable) + ' · ' + e(r.target_label) + ': ' + e(r.reason) + '</li>').join('') + '</ul><details><summary>Original site record and source citations</summary><pre>' + e(JSON.stringify(s.region_record.properties, null, 2)) + '</pre></details></article>').join('');
    return '<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>' + e(pack.campaign_name) + '</title><style>body{font:16px/1.6 system-ui,sans-serif;max-width:960px;margin:48px auto;padding:0 24px;color:#172234}h1{line-height:1.2}h2{margin-top:40px}table{border-collapse:collapse;width:100%}th,td{border-bottom:1px solid #ccd3dd;text-align:left;padding:12px;vertical-align:top}th{width:25%}pre{white-space:pre-wrap;overflow-wrap:anywhere;font-size:12px}.note{background:#f2f4f7;padding:20px}article{border-bottom:1px solid #ccd3dd;padding:12px 0}a{color:#174e75}.notes{white-space:pre-wrap}@media print{body{margin:0;max-width:none}details{display:block}pre{font-size:9px}h2,h3{break-after:avoid}tr{break-inside:avoid}}</style></head><body><p>SIMILITUDE / Review draft</p><h1>' + e(pack.campaign_name) + '</h1><p>Target: Connecting Ridge · Task: ' + e(pack.task) + '<br>Exported UTC: ' + e(pack.created_utc) + '</p><p class="note">' + e(pack.limitations[0]) + '</p><h2>Test matrix</h2><table><thead><tr><th>Objective</th><th>Evidence status</th><th>Supporting footprint / remaining work</th></tr></thead><tbody>' + table + '</tbody></table><h2>Selected study footprints</h2>' + sites + '<h2>Proposed route / setup</h2><p class="notes">' + e(pack.proposed_route_or_setup.notes) + '</p><p>User notes, unverified. Route geometry has not been calculated.</p><h2>Assumptions</h2><p class="notes">' + e(pack.assumptions) + '</p><h2>Reconnaissance checklist</h2><ul>' + pack.reconnaissance.map(x => '<li>' + e(x.label) + ' — ' + (x.included_in_plan ? 'included in plan' : 'not included in plan') + '; not verified.</li>').join('') + '</ul><h2>Evidence limits</h2><ul>' + pack.limitations.map(x => '<li>' + e(x) + '</li>').join('') + '</ul><h2>Sources and reproducibility</h2><p>Dataset: ' + e(pack.source.file) + '<br>Generated: ' + e(pack.source.generated) + '<br>SHA-256: ' + e(pack.source.sha256 || 'Unavailable in this browser') + '</p><ul>' + pack.source_links.map(u => '<li><a href="' + e(u) + '">' + e(u) + '</a></li>').join('') + '</ul><p>Download the companion evidence JSON to retain the complete cell records.</p></body></html>';
  }
  // Export pure presentation functions for meaningful checks without browser dependencies.
  if (typeof module !== 'undefined' && module.exports) module.exports = { cleanState, defaults, catalogFrom, matrix, evidencePack, briefHTML };
  if (typeof document === 'undefined') return;

  const $ = id => document.getElementById(id);
  let state = defaults(), catalog = [], source = null, sourceHash = null, persistence = true;
  try { state = cleanState(JSON.parse(localStorage.getItem(STORAGE))); } catch (_) { persistence = false; }
  function save() {
    try { localStorage.setItem(STORAGE, JSON.stringify(state)); persistence = true; } catch (_) { persistence = false; }
    $('draft-state').textContent = persistence ? 'Draft saved in this browser' : 'Browser storage unavailable — export to keep your draft';
  }
  const pct = n => Number.isFinite(n) ? (n * 100).toFixed(1) + '%' : 'Not available';
  function bindInputs() {
    $('mission-task').value = state.task;
    $('campaign-name').value = state.name; $('route-notes').value = state.route; $('assumptions').value = state.assumptions;
    document.querySelectorAll('.objective-list input').forEach(el => { el.checked = state.objectives.includes(el.value); });
  }
  function renderCandidates() {
    $('candidate-grid').innerHTML = catalog.map(c => {
      const selected = state.selected.includes(c.id);
      const cell = c.cells[0];
      const coordinates = cell?.geometry?.coordinates;
      const tags = c.fields.map(f => '<span class="state-label observed">' + escape(f.variable === 'slope_roughness' ? 'Terrain match' : 'Shadow geometry') + '</span>').join('');
      const metric = cell?.properties?.lens_scores?.L1?.descriptors?.frac_gt8?.earth;
      const metricLine = Number.isFinite(metric) ? '<div class="candidate-metric"><span>Terrain above 8°</span><b>' + pct(metric) + '</b></div>' : '<div class="candidate-metric"><span>Lighting response</span><b>Unmeasured</b></div>';
      const mapLink = coordinates ? 'https://www.openstreetmap.org/?mlat=' + coordinates[1] + '&mlon=' + coordinates[0] + '#map=12/' + coordinates[1] + '/' + coordinates[0] : 'explorer.html';
      return '<article class="candidate-card card' + (selected ? ' selected' : '') + '"><div class="candidate-image"><img src="' + c.image + '" alt="Sentinel-2 study image of ' + escape(c.title) + '" width="400" height="300" loading="lazy" data-source="client" data-subject="' + escape(c.title) + '"><span class="state-label">' + escape(c.label) + '</span></div><div class="candidate-content"><h3>' + escape(c.title) + '</h3><p class="candidate-location">' + escape(c.location) + ' · 4 km footprint</p><div class="candidate-evidence">' + tags + '</div>' + metricLine + '<p class="candidate-limit">' + escape(c.limit) + '</p><div class="candidate-action"><button type="button" class="btn ' + (selected ? 'btn--primary' : 'btn--secondary') + '" data-select="' + c.id + '" aria-pressed="' + selected + '">' + (selected ? 'Remove from brief −' : 'Add to brief +') + '</button><a href="' + mapLink + '" target="_blank" rel="noopener" aria-label="' + (coordinates ? 'Open footprint map for ' : 'Open source explorer for ') + escape(c.title) + '">' + (coordinates ? 'Map ↗' : 'Source ↗') + '</a></div></div></article>';
    }).join('');
  }
  function render() {
    const rows = matrix(state, catalog), selected = catalog.filter(c => state.selected.includes(c.id));
    const modelled = rows.filter(r => r.state === 'modelled').length;
    $('objective-count').textContent = state.objectives.length;
    $('selection-count').textContent = selected.length;
    $('task-question').textContent = state.task === 'navigation' ? 'Where can we rehearse navigation, and what remains untested?' : 'Which terrain variables can we compare before a field survey?';
    $('campaign-sites-label').textContent = selected.length + ' footprint' + (selected.length === 1 ? '' : 's') + ' selected';
    $('test-matrix').innerHTML = rows.length ? rows.map(r => '<div class="matrix-row"><strong>' + escape(r.title) + '</strong><span class="state-label ' + (r.state === 'modelled' ? 'observed' : r.state === 'facility_needed' ? 'facility' : 'pending') + '">' + escape(r.label) + '</span><small>' + escape(r.note) + '</small></div>').join('') : '<p class="inline-limit">Choose at least one test objective above.</p>';
    $('survey-checklist').innerHTML = SURVEYS.map(x => '<label><input type="checkbox" data-survey="' + x.id + '" ' + (state.surveys.includes(x.id) ? 'checked' : '') + '><span>' + escape(x.label) + '</span></label>').join('') + '<p class="field-note">Checked tasks are included in the plan; completion is unverified.</p>';
    const title = state.name.trim() || 'Untitled campaign';
    $('export-title').textContent = title; $('paper-title').textContent = title;
    $('export-summary').textContent = selected.length ? selected.map(c => c.title).join(' + ') + '. ' + (rows.length - modelled) + ' objective(s) still need evidence or a controlled test.' : 'Choose a study footprint to prepare your brief.';
    $('paper-summary').innerHTML = [['Study footprints', selected.length], ['Test objectives', rows.length], ['With modelled evidence', modelled], ['Unresolved / facility', rows.length - modelled]].map(([k, v]) => '<div class="paper-summary-row"><span>' + k + '</span><b>' + v + '</b></div>').join('');
    $('paper-date').textContent = source?.metadata?.generated?.slice(0, 10) || '';
    const exportBlocked = !source || !selected.length || !rows.length;
    $('download-brief').disabled = $('download-data').disabled = exportBlocked;
    $('export-hint').hidden = !exportBlocked;
    if (exportBlocked) $('export-hint').textContent = !source ? 'Downloads become available after published study records load.' : !selected.length ? 'Select a study footprint in step 03 to enable downloads.' : 'Select at least one test objective in step 02 to enable downloads.';
    save();
  }
  function download(content, type, extension) {
    const blob = new Blob([content], { type }); const url = URL.createObjectURL(blob);
    const a = document.createElement('a'); a.href = url; a.download = 'similitude-review.' + extension; document.body.appendChild(a); a.click(); a.remove(); setTimeout(() => URL.revokeObjectURL(url), 30000);
    $('export-status').textContent = 'Download prepared. Review the unresolved items before sharing.';
  }
  const menu = document.querySelector('.menu-toggle');
  function closeMenu() { menu.setAttribute('aria-expanded', 'false'); $('mobile-nav').hidden = true; }
  menu.addEventListener('click', () => { const open = menu.getAttribute('aria-expanded') !== 'true'; menu.setAttribute('aria-expanded', String(open)); $('mobile-nav').hidden = !open; });
  $('mobile-nav').addEventListener('click', e => { if (e.target.closest('a')) closeMenu(); });
  document.addEventListener('keydown', e => { if (e.key === 'Escape' && !$('mobile-nav').hidden) { closeMenu(); menu.focus(); } });
  document.querySelector('.objective-list').addEventListener('change', () => { state.objectives = [...document.querySelectorAll('.objective-list input:checked')].map(x => x.value); render(); });
  $('mission-task').addEventListener('change', e => { state.task = e.target.value; state.objectives = state.task === 'terrain' ? ['terrain', 'obstacles', 'gravity'] : ['terrain', 'shadow', 'lighting', 'obstacles']; bindInputs(); render(); });
  $('candidate-grid').addEventListener('click', e => {
    const button = e.target.closest('[data-select]'); if (!button) return;
    const id = button.dataset.select; state.selected = state.selected.includes(id) ? state.selected.filter(x => x !== id) : [...state.selected, id];
    renderCandidates(); render(); document.querySelector('[data-select="' + id + '"]')?.focus({ preventScroll: true });
  });
  $('survey-checklist').addEventListener('change', e => { const id = e.target.dataset.survey; if (!id) return; state.surveys = e.target.checked ? [...new Set([...state.surveys, id])] : state.surveys.filter(x => x !== id); save(); });
  for (const [id, key] of [['campaign-name', 'name'], ['route-notes', 'route'], ['assumptions', 'assumptions']]) $(id).addEventListener('input', e => { state[key] = e.target.value; render(); });
  $('guided-demo').addEventListener('click', () => {
    if (!catalog.length) { $('load-status').textContent = 'Study records are still loading. Please retry when candidates appear.'; location.hash = 'compare'; return; }
    state.task = 'navigation'; state.objectives = ['terrain', 'shadow', 'lighting', 'obstacles']; state.selected = ['site:E10K_453_921'];
    bindInputs(); renderCandidates(); render();
    $('load-status').textContent = 'Worked example: Da Qaidam adds terrain evidence. Add Hawaiʻi to compare shadow evidence; camera response and soil remain unmeasured.';
    location.hash = 'compare';
  });
  for (const [id, extension] of [['download-brief', 'html'], ['download-data', 'json']]) $(id).addEventListener('click', () => {
    if (!source || !state.selected.length || !state.objectives.length) return;
    const pack = evidencePack(state, catalog, source, sourceHash);
    download(extension === 'html' ? briefHTML(pack) : JSON.stringify(pack, null, 2), extension === 'html' ? 'text/html;charset=utf-8' : 'application/json', extension);
  });
  bindInputs(); render();
  fetch('data/candidates.geojson').then(r => { if (!r.ok) throw new Error('HTTP ' + r.status); return r.text(); }).then(async text => {
    const data = JSON.parse(text); const entries = catalogFrom(data); if (!entries.length) throw new Error('No supported study footprints found.');
    if (globalThis.crypto?.subtle) { try { sourceHash = [...new Uint8Array(await crypto.subtle.digest('SHA-256', new TextEncoder().encode(text)))].map(b => b.toString(16).padStart(2, '0')).join(''); } catch (_) { /* explicitly null in export */ } }
    $('candidate-grid').setAttribute('aria-busy', 'false');
    source = data; catalog = entries; state.selected = state.selected.filter(id => catalog.some(c => c.id === id));
    $('load-status').textContent = '';
    const descriptor = catalog.find(c => c.id === 'site:E10K_453_921')?.cells[0]?.properties?.lens_scores?.L1?.descriptors?.frac_gt8;
    if (descriptor) { $('hero-moon').textContent = pct(descriptor.target); $('hero-earth').textContent = pct(descriptor.earth); $('hero-moon-bar').style.width = (descriptor.target * 100) + '%'; $('hero-earth-bar').style.width = (descriptor.earth * 100) + '%'; }
    renderCandidates(); render();
  }).catch(error => { $('candidate-grid').setAttribute('aria-busy', 'false'); $('load-status').classList.add('error'); $('load-status').setAttribute('role', 'alert'); $('load-status').textContent = 'Study records could not be loaded (' + error.message + '). Reload this page or use the scientific evidence link. Export is unavailable.'; });
})();
