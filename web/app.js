(function () {
  'use strict';

  var FALLBACK_LENSES = [
    { id: 'L1', name: 'Touchdown & Traverse', body: 'Moon', question: '' },
    { id: 'L2', name: 'Low-Sun Navigation', body: 'Moon', question: '' },
    { id: 'M1', name: 'Aqueous Minerals', body: 'Mars', question: '' },
    { id: 'X1', name: 'Ice under Dry Overburden', body: 'Mars', question: '' }
  ];
  var LENSES = FALLBACK_LENSES.slice();
  var BAND_COLORS = { good: '#2b9348', ok: '#9ac93a', warn: '#f08c00', bad: '#d62828' };

  var state = { features: [], lens: 'L1', selectedId: null, meta: {}, ledger: null };
  var map, markerLayer, markers = {};

  function esc(v) {
    return String(v === null || v === undefined ? '' : v).replace(/[&<>"']/g, function (c) {
      return { '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c];
    });
  }
  function $(id) { return document.getElementById(id); }
  function num(v, digits) {
    return (typeof v === 'number' && isFinite(v)) ? v.toFixed(digits === undefined ? 2 : digits) : '—';
  }
  function cap(s) { s = String(s || ''); return s.charAt(0).toUpperCase() + s.slice(1); }
  function lensInfo(id) { if (id === 'SITES') return SITES_TAB; return LENSES.filter(function (l) { return l.id === id; })[0] || { id: id, name: id, body: '', question: '' }; }
  function roleOf(p) { return p.role === 'control' || p.role === 'decoy' ? p.role : 'hidden'; }
  // B17: the word "hidden" is not shown until site-level attention exists (A17 after 07:00)
  var ROLE_LABEL = { hidden: 'engine-qualified cell', control: 'control', decoy: 'decoy' };
  function roleLabel(r) { return ROLE_LABEL[r] || r; }
  var SITES_TAB = { id: 'SITES', name: 'Showcase sites', body: 'Earth',
    question: 'Engine-qualified 4 km cells grouped into field sites (150 km): which rows of your test matrix come home valid, which need a facility, which are not certified.' };
  function isSite(f) { return !!(f && f.properties && f.properties.feature_type === 'site'); }
  function safeUrl(u) { return /^https?:\/\//i.test(String(u || '')) ? String(u) : ''; }

  function sigmaColor(s) {
    if (typeof s !== 'number') return '#868e96';
    if (s <= 1) return BAND_COLORS.good;
    if (s <= 2) return BAND_COLORS.ok;
    if (s <= 3) return BAND_COLORS.warn;
    return BAND_COLORS.bad;
  }
  function sigmaText(ls) {
    if (!ls || typeof ls.sigma !== 'number') return '—';
    return (ls.sigma_capped ? '> ' : '') + ls.sigma.toFixed(2) + ' σ';
  }
  // Sigma used for ranking / colour: L2 is a candidate for its terrain-shadow part only; its
  // sun-geometry part is a pre-registered no-analog shown separately in the card.
  function hasShadow(ls) { return !!ls && typeof ls.sigma_shadow === 'number'; }
  function rankSigma(ls) { return hasShadow(ls) ? ls.sigma_shadow : (ls ? ls.sigma : null); }
  function rankSigmaText(ls) {
    if (!ls) return '—';
    return hasShadow(ls) ? 'σ_shadow ' + ls.sigma_shadow.toFixed(2) : sigmaText(ls);
  }
  function outline(status) {
    if (status === 'engine-confirmed') return { dashArray: null, color: '#111', weight: 3 };
    if (status === 'engine-semiquant') return { dashArray: '4 3', color: '#111', weight: 3 };
    return { dashArray: null, color: '#868e96', weight: 2 };
  }

  // ---------- radar (pure) ----------
  function similarity(z) {
    return (typeof z === 'number' && isFinite(z)) ? Math.exp(-Math.abs(z) / 2) : null;
  }
  function shortName(k) { k = String(k); return k.length > 11 ? k.slice(0, 10) + '…' : k; }
  function radarSvg(descs) {
    var axes = Object.keys(descs || {}).map(function (k) {
      return { name: k, z: descs[k] ? descs[k].z : null };
    }).filter(function (a) { return similarity(a.z) !== null; });
    if (axes.length < 3) return '<p class="note">Not enough descriptors with z-values for a radar chart.</p>';
    var W = 360, H = 340, cx = 180, cy = 170, R = 100, n = axes.length;
    function pt(i, r) {
      var a = -Math.PI / 2 + 2 * Math.PI * i / n;
      return [cx + r * Math.cos(a), cy + r * Math.sin(a)];
    }
    function poly(fn) {
      return axes.map(function (a, i) { var q = pt(i, R * fn(a)); return q[0].toFixed(1) + ',' + q[1].toFixed(1); }).join(' ');
    }
    var s = '<svg viewBox="0 0 ' + W + ' ' + H + '" width="100%" role="img" aria-label="Radar chart of per-descriptor match to the target" class="radar-svg">';
    [0.25, 0.5, 0.75, 1].forEach(function (g) {
      s += '<polygon points="' + poly(function () { return g; }) + '" class="r-grid"/>';
    });
    var worst = axes[0];
    axes.forEach(function (a, i) {
      if (Math.abs(a.z) > Math.abs(worst.z)) worst = a;
      var e = pt(i, R), l = pt(i, R + 10), ca = Math.cos(-Math.PI / 2 + 2 * Math.PI * i / n);
      var anchor = ca > 0.3 ? 'start' : (ca < -0.3 ? 'end' : 'middle');
      s += '<line x1="' + cx + '" y1="' + cy + '" x2="' + e[0].toFixed(1) + '" y2="' + e[1].toFixed(1) + '" class="r-axis"/>';
      s += '<text x="' + l[0].toFixed(1) + '" y="' + (l[1] + 3).toFixed(1) + '" text-anchor="' + anchor + '" class="r-label"><title>' +
        esc(a.name) + ' (z = ' + esc(num(a.z)) + ')</title>' + esc(shortName(a.name)) + '</text>';
    });
    s += '<polygon points="' + poly(function () { return 1; }) + '" class="r-ref"/>';
    s += '<polygon points="' + poly(function (a) { return similarity(a.z); }) + '" class="r-cand"/>';
    axes.forEach(function (a, i) {
      var q = pt(i, R * similarity(a.z));
      s += '<circle cx="' + q[0].toFixed(1) + '" cy="' + q[1].toFixed(1) + '" r="2.5" class="r-dot"/>';
    });
    s += '</svg>';
    s += '<p class="radar-key"><span class="k-ref"></span>target (1.0) <span class="k-cand"></span>this site</p>';
    s += '<p class="limiting">Limiting factor: <strong>' + esc(worst.name) + '</strong> (z = ' + esc(num(worst.z)) + ')</p>';
    return s;
  }

  // ---------- data ----------
  function fetchJson(url) {
    return fetch(url).then(function (r) {
      if (!r.ok) { var e = new Error('HTTP ' + r.status + ' for ' + url); e.status = r.status; throw e; }
      return r.json();
    });
  }
  function loadData() {
    var override = new URLSearchParams(location.search).get('data');
    if (override) {
      return fetchJson(override).then(function (d) { return { data: d, mock: !!(d.metadata && d.metadata.mock) }; });
    }
    return fetchJson('data/candidates.geojson').then(function (d) {
      return { data: d, mock: !!(d.metadata && d.metadata.mock) };
    }, function () {
      return fetchJson('data/candidates.mock.geojson').then(function (d) { return { data: d, mock: true }; });
    });
  }
  function loadLenses() {
    return fetchJson('data/lenses.json').then(function (arr) {
      if (Array.isArray(arr) && arr.length) {
        LENSES = arr.map(function (l) {
          return { id: String(l.id), name: l.name || l.id, body: cap(l.body), question: l.question || '' };
        });
      }
    }).catch(function () { /* keep fallback */ });
  }
  function loadLedger() {
    return fetchJson('data/ledger.json').then(function (d) { state.ledger = d; }).catch(function () { state.ledger = null; });
  }

  // ---------- UI ----------
  function buildLensTabs() {
    var host = $('lens-tabs');
    var siteBtn = '<button type="button" class="lens-btn" data-lens="SITES" aria-pressed="false" aria-label="Showcase sites">Sites<small>showcase</small></button>';
    host.innerHTML = siteBtn + LENSES.map(function (l) {
      return '<button type="button" class="lens-btn" data-lens="' + esc(l.id) + '" aria-pressed="false" aria-label="Lens ' +
        esc(l.id) + ': ' + esc(l.name) + ', ' + esc(l.body) + '">' + esc(l.id) + ' ' + esc(l.name) +
        '<small>' + esc(l.body) + '</small></button>';
    }).join('');
  }
  function buildLegend() {
    var items = [
      ['≤ 1 σ', BAND_COLORS.good], ['≤ 2 σ', BAND_COLORS.ok],
      ['≤ 3 σ', BAND_COLORS.warn], ['> 3 σ', BAND_COLORS.bad]
    ].map(function (i) {
      return '<span class="item"><span class="swatch" style="background:' + i[1] + '"></span>' + esc(i[0]) + '</span>';
    }).join('');
    var roles = '<span class="item"><span class="swatch" style="background:#ccc"></span><b>engine-qualified cell</b> (filled)</span>' +
      '<span class="item"><span class="swatch ring"></span><b>control</b> (ring: known good site)</span>' +
      '<span class="item"><span class="swatch diamond"></span><b>decoy</b> (diamond: looks similar, should fail)</span>';
    var ev = '<span class="item"><span class="swatch" style="background:#ccc;border-style:solid"></span>engine-confirmed (solid)</span>' +
      '<span class="item"><span class="swatch" style="background:#ccc;border-style:dashed"></span>engine-semiquant (dashed)</span>' +
      '<span class="item"><span class="swatch" style="background:#ccc;border-color:#868e96"></span>literature-only / hypothesis (grey)</span>';
    $('legend').innerHTML = '<div class="lg-row">' + items + '<span class="item">σ small = good analog; "> X σ" = capped</span></div>' +
      '<div class="lg-row">' + roles + '<span class="item"><span class="swatch sq"></span><b>site</b> (square, Sites tab)</span></div><div class="lg-row">' + ev + '</div>';
  }

  function siteFeatures() {
    return state.features.filter(isSite).sort(function (a, b) {
      return String(a.properties.showcase).localeCompare(String(b.properties.showcase)) ||
        String(a.properties.name).localeCompare(String(b.properties.name));
    });
  }
  function lensFeatures() {
    if (state.lens === 'SITES') return siteFeatures();
    return state.features.filter(function (f) {
      return f.properties && f.properties.lens_scores && f.properties.lens_scores[state.lens];
    }).sort(function (a, b) {
      var x = rankSigma(a.properties.lens_scores[state.lens]), y = rankSigma(b.properties.lens_scores[state.lens]);
      return (typeof x === 'number' ? x : 1e9) - (typeof y === 'number' ? y : 1e9);
    });
  }
  function lensMeta(id) { return (state.meta.lenses && state.meta.lenses[id]) || null; }

  function setLens(id) {
    state.lens = id;
    Array.prototype.forEach.call(document.querySelectorAll('.lens-btn'), function (b) {
      b.setAttribute('aria-pressed', b.getAttribute('data-lens') === id ? 'true' : 'false');
    });
    $('lens-question').textContent = lensInfo(id).question || '';
    var sel = state.features.filter(function (f) { return f.properties.id === state.selectedId; })[0];
    if (sel && (id === 'SITES' ? !isSite(sel) : (isSite(sel) || !sel.properties.lens_scores[id]))) state.selectedId = null;
    renderMap(); renderList(); renderCard();
  }

  function decoyIcon(color, big) {
    var sz = big ? 22 : 18;
    return L.divIcon({
      className: 'decoy-icon', iconSize: [sz, sz], iconAnchor: [sz / 2, sz / 2],
      html: '<span style="background:' + color + '"></span>'
    });
  }
  function makeMarker(p, ls, lat, lon, big) {
    var role = roleOf(p), r = big ? 13 : 9, col = sigmaColor(rankSigma(ls));
    if (role === 'decoy') return L.marker([lat, lon], { icon: decoyIcon(col, big), keyboard: false });
    if (role === 'control') {
      return L.circleMarker([lat, lon], { radius: r, fillColor: col, fillOpacity: 0.12, color: '#111', weight: 3 });
    }
    var o = outline(p.evidence_status);
    return L.circleMarker([lat, lon], { radius: r, fillColor: col, fillOpacity: 0.9, color: o.color, weight: o.weight, dashArray: o.dashArray });
  }

  function renderMap() {
    markerLayer.clearLayers(); markers = {};
    var feats = lensFeatures();
    feats.forEach(function (f) {
      if (isSite(f)) {
        var sp = f.properties, big = sp.id === state.selectedId, sz = big ? 22 : 16;
        var col = sp.lenses_engine_confirmed.length ? BAND_COLORS.good : (sp.lenses_engine_semiquant.length ? BAND_COLORS.ok : '#868e96');
        var sm = L.marker([f.geometry.coordinates[1], f.geometry.coordinates[0]], { icon: L.divIcon({
          className: 'site-icon', iconSize: [sz, sz], iconAnchor: [sz / 2, sz / 2],
          html: '<span style="background:' + col + '"></span>' }), keyboard: false });
        sm.bindTooltip(esc(sp.name) + ' — site, ' + esc(sp.n_cells) + ' cell(s)');
        sm.on('click', function () { select(sp.id, false); });
        sm.addTo(markerLayer); markers[sp.id] = sm;
        return;
      }
      var p = f.properties, ls = p.lens_scores[state.lens];
      var lat = f.geometry.coordinates[1], lon = f.geometry.coordinates[0];
      var m = makeMarker(p, ls, lat, lon, p.id === state.selectedId);
      m.bindTooltip(esc(p.name) + ' (' + esc(roleLabel(roleOf(p))) + ') — ' + esc(rankSigmaText(ls)));
      m.on('click', function () { select(p.id, false); });
      m.addTo(markerLayer);
      markers[p.id] = m;
    });
    if (feats.length) {
      var b = L.latLngBounds(feats.map(function (f) { return [f.geometry.coordinates[1], f.geometry.coordinates[0]]; }));
      map.fitBounds(b, { padding: [40, 40], maxZoom: 5 });
    }
  }

  function siteRowHtml(f) {
    var p = f.properties;
    var chips = p.lenses_engine_confirmed.concat(p.lenses_engine_semiquant.map(function (x) { return x + '~'; }));
    return '<li><button type="button" data-id="' + esc(p.id) + '"' + (p.id === state.selectedId ? ' aria-current="true"' : '') + '>' +
      '<span class="dot sq"></span><span>' + esc(p.name) + '<br><span class="note">' + esc(p.n_cells) + ' cell(s) · showcase ' + esc(p.showcase) + '</span></span>' +
      '<span class="sig">' + esc(chips.join(' ')) + '</span></button></li>';
  }
  function rowHtml(f) {
    if (isSite(f)) return siteRowHtml(f);
    var p = f.properties, ls = p.lens_scores[state.lens], role = roleOf(p);
    var dot = role === 'decoy' ? 'dot diamond' : (role === 'control' ? 'dot ring' : 'dot');
    var tag = role === 'hidden' ? '' : ' <span class="tag ' + role + '">' + esc(roleLabel(role)) + '</span>';
    return '<li><button type="button" data-id="' + esc(p.id) + '"' + (p.id === state.selectedId ? ' aria-current="true"' : '') + '>' +
      '<span class="' + dot + '" style="background:' + sigmaColor(rankSigma(ls)) + '"></span>' +
      '<span>' + esc(p.name) + tag + '<br><span class="note">' + esc(p.country || '') + '</span></span>' +
      '<span class="sig">' + esc(rankSigmaText(ls)) + '</span></button></li>';
  }

  function renderList() {
    var li = lensInfo(state.lens), feats = lensFeatures(), lm = lensMeta(state.lens);
    var host = $('list');
    if (state.lens === 'SITES') {
      $('list-title').textContent = 'Showcase sites (selection rule in config/sites.yaml, not hand-picked)';
      host.innerHTML = feats.length ? feats.map(siteRowHtml).join('') : '<li class="empty">No site table published yet.</li>';
      return;
    }
    $('list-title').textContent = 'Cells for ' + li.id + ' ' + li.name + ' (' + li.body + '), best first';
    if (!feats.length) {
      var msg = (lm && lm.status) ? 'No engine results for this lens yet' + (lm.status !== 'no fidelity data yet' ? ' (' + lm.status + ')' : '') :
        'No candidates scored for this lens.';
      host.innerHTML = '<li class="empty">' + esc(msg) + '</li>';
      return;
    }
    var hidden = feats.filter(function (f) { return roleOf(f.properties) === 'hidden'; });
    var valid = feats.filter(function (f) { return roleOf(f.properties) !== 'hidden'; });
    var h = '<li class="group-h">Engine-qualified cells</li>';
    if (hidden.length) h += hidden.map(rowHtml).join('');
    else h += '<li class="empty">' + (lm && lm.no_hidden_found ? 'No engine-qualified cell for this lens' : 'No engine-qualified cells in the current data') + '</li>';
    if (lm && lm.n_attention_unknown) {
      h += '<li class="empty">' + esc(lm.n_attention_unknown) + ' more candidate(s) pass the fidelity test but their literature attention is not yet known — an unknown count is never treated as "little studied".</li>';
    }
    if (valid.length) h += '<li class="group-h">Validation: controls &amp; decoys</li>' + valid.map(rowHtml).join('');
    host.innerHTML = h;
  }

  function select(id, pan) {
    state.selectedId = id;
    renderMap(); // refresh marker emphasis
    var m = markers[id];
    if (m) {
      if (m.bringToFront) m.bringToFront();
      if (pan) map.panTo(m.getLatLng());
    }
    renderList(); renderCard();
    var c = $('card');
    if (window.matchMedia('(max-width: 899px)').matches && c.scrollIntoView) c.scrollIntoView({ behavior: 'smooth', block: 'start' });
  }

  function listHtml(items) {
    return items.length ? '<ul>' + items.map(function (i) { return '<li>' + i + '</li>'; }).join('') + '</ul>' : '<p class="muted">—</p>';
  }

  function ledgerHtml(lensId) {
    var body = lensInfo(lensId).body.toLowerCase();
    var L_ = state.ledger && state.ledger[body];
    if (!L_) return '';
    var items = (L_.items || []).filter(function (i) { return (i.applies_to || []).indexOf(lensId) >= 0; });
    var gaps = L_.nasa_gaps || [];
    var h = '<details class="fold"><summary>Transfer Ledger (' + esc(cap(body)) + ', ' + esc(lensId) + ')</summary>';
    if (!items.length) h += '<p class="muted">No ledger items for this lens.</p>';
    h += items.map(function (i) {
      var e = i.earth || {}, t = i.target || {}, u = safeUrl(i.source);
      return '<div class="led"><strong>' + esc(i.quantity) + '</strong><br>' +
        'Earth ' + esc(e.value) + ' ' + esc(e.unit) + ' vs target ' + esc(t.value) + ' ' + esc(t.unit) +
        (typeof i.ratio_target_over_earth === 'number' ? ' <span class="note">(ratio ' + esc(i.ratio_target_over_earth) + ')</span>' : '') +
        '<br><span class="lbl">Consequence:</span> ' + esc(i.consequence) +
        '<br><span class="lbl">Mitigation:</span> ' + esc(i.mitigation) +
        (u ? '<br><a href="' + esc(u) + '" target="_blank" rel="noopener noreferrer">Source</a>' : '') + '</div>';
    }).join('');
    if (gaps.length) {
      h += '<h4>NASA gaps</h4><ul>' + gaps.map(function (g) {
        return '<li><span class="note">' + esc(g.id) + '</span> ' + esc(g.name) + '</li>';
      }).join('') + '</ul>';
    }
    return h + '</details>';
  }

  // B16: three-state verdicts, read from verdicts.parquet (A15) by discovery; never computed here.
  var VERDICT_LABEL = { 'TRANSFERS': 'Qualified for', 'NO-ANALOG': 'Not qualified for', 'UNOBSERVED': 'Not certified' };
  function verdictHtml(p) {
    var v = (p.verdicts || []);
    if (!v.length) {
      return '<p class="note">Verdicts (TRANSFERS / NO-ANALOG / UNOBSERVED) appear here once the verdict table is published.</p>';
    }
    var h = '<div class="verdicts"><h3>Test verdicts</h3><ul>';
    v.forEach(function (r) {
      var cls = r.state === 'TRANSFERS' ? 'v-ok' : (r.state === 'NO-ANALOG' ? 'v-no' : 'v-unk');
      h += '<li class="' + cls + '"><span class="v-state">' + esc(VERDICT_LABEL[r.state] || r.state) + '</span> ' +
        '<strong>' + esc(r.test) + '</strong> — ' + esc(r.variable) + ' <span class="tag">' + esc(r.state) + '</span>' +
        (r.value !== null && r.value !== undefined ? ' <span class="note">(' + esc(r.value) + ')</span>' : '') +
        (r.reason ? '<br><span class="note">' + esc(r.reason) + '</span>' : '') +
        (r.facility ? '<br><span class="note">→ ' + esc(r.facility) + '</span>' : '') +
        (r.scope === 'lens' ? ' <span class="note">[applies to the whole lens]</span>' : '') + '</li>';
    });
    return h + '</ul></div>';
  }
  function evidenceScaleHtml(s) {
    if (!s) return '';
    var parts = [];
    if (typeof s.native_rank === 'number' && typeof s.n_native === 'number') {
      parts.push('Native rank <strong>' + esc(s.native_rank) + '/' + esc(s.n_native) + '</strong>' +
        ' <span class="note">(target-body footprints farther from the target than this site' +
        (s.native_rank_basis ? ', by ' + esc(s.native_rank_basis) : '') + ')</span>');
    }
    if (typeof s.largest_patch_km2 === 'number') {
      parts.push('Matched area <strong>' + esc(num(s.matched_area_km2, 3)) + ' km²</strong>, largest patch ' +
        esc(num(s.largest_patch_km2, 3)) + ' km² <span class="note">(per-pixel match; pass ≥ 0.1 km²' +
        (s.pixel_footprint === 'relocated' ? '; footprint relocated by rule A14, original: ' +
          esc(num(s.largest_patch_km2_original, 3)) + ' km²' : '') + ')</span>');
    }
    return parts.length ? '<p class="scale">' + parts.join('<br>') + '</p>' : '';
  }

  // ---------- B17 site card (2c contract; rows copied from field_facility.json) ----------
  function rowsHtml(rows, kind) {
    if (!rows || !rows.length) return '<p class="note">None.</p>';
    return '<ul class="rows ' + kind + '">' + rows.map(function (r) {
      var src = safeUrl(r.source);
      return '<li><strong>' + esc(r.lens) + '</strong> ' + (r.target_label ? esc(r.target_label) + ' — ' : '') +
        esc(r.variable) + (r.value !== null && r.value !== undefined ? ' <span class="note">(' + esc(r.value) + ')</span>' : '') +
        (r.reason ? '<br><span class="note">' + esc(r.reason) + '</span>' : '') +
        (r.facility ? '<br>→ ' + esc(r.facility) : '') +
        (src ? ' <a href="' + esc(src) + '" target="_blank" rel="noopener">source</a>' : '') + '</li>';
    }).join('') + '</ul>';
  }
  function chip(list, cls, label) {
    return (list || []).map(function (l) { return '<span class="chip ' + cls + '" title="' + esc(label) + '">' + esc(l) + ' · ' + esc(label) + '</span>'; }).join(' ');
  }
  function siteCardHtml(p) {
    var h = '<h2>' + esc(p.name) + '</h2>';
    h += '<p class="meta">Site · ' + num(p.lat, 3) + ', ' + num(p.lon, 3) + ' · ' + esc(p.n_cells) + ' cell(s) · span ' +
      esc(num(p.max_span_km, 0)) + ' km' + (p.max_span_km > 300 ? ' <span class="flag">a region, not one camp</span>' : '') +
      ' · <span class="note">' + esc(p.id) + '</span></p>';
    h += '<p class="chips">' + chip(p.lenses_engine_confirmed, 'c-ok', 'engine-confirmed') + ' ' +
      chip(p.lenses_engine_semiquant, 'c-semi', 'engine-semiquant') + ' ' + chip(p.lenses_hypothesis, 'c-hyp', 'hypothesis (B10 downgraded)') + ' ' +
      chip(p.lenses_literature_only, 'c-lit', 'literature-only context') + '</p>';
    h += '<p><strong>Literature attention:</strong> ' + esc(p.hidden_status) +
      (typeof p.attention_n === 'number' ? ' (' + esc(p.attention_n) + ' papers)' : '') + '</p>';
    if (p.note) h += '<p class="note">' + esc(p.note) + '</p>';
    h += '<h3>Comes home valid (Field)</h3>' + rowsHtml(p.field, 'r-field');
    h += '<h3>Needs a facility</h3>' + rowsHtml(p.facility, 'r-fac');
    h += '<h3>Not certified (unobserved)</h3>' + rowsHtml(p.unobserved, 'r-unobs');
    var snow = p.l2_snow_free_frac || {};
    var sk = Object.keys(snow);
    if (sk.length) h += '<p class="note">L2 cells snow-free fraction (MODIS 2023): ' + sk.map(function (k) { return esc(k) + ' ' + esc(num(snow[k], 2)); }).join(', ') + '</p>';
    if (p.multilens && p.multilens.length) {
      h += '<h3>Other lenses nearby (≤ 150 km)</h3><ul class="rows">' + p.multilens.map(function (m) {
        return '<li>' + esc(m.partner_lens) + ' ' + esc(m.partner_label) + ' · ' + esc(num(m.distance_km, 0)) + ' km · ' + esc(m.partner_state) +
          (m.edge_of_radius ? ' <span class="note">(edge of radius)</span>' : '') + '</li>';
      }).join('') + '</ul>';
    }
    if (p.b10_unreviewed_cells && p.b10_unreviewed_cells.length) {
      h += '<p class="note">Cells not yet visually reviewed (B10): ' + esc(p.b10_unreviewed_cells.join(', ')) + '</p>';
    }
    h += '<p class="note">Member cells: ' + esc(p.member_cells.join(', ')) + '</p>';
    return h;
  }

  function renderCard() {
    var host = $('card');
    var f = state.features.filter(function (x) { return x.properties.id === state.selectedId; })[0];
    if (!f) { host.innerHTML = '<p class="muted">Select a site on the map or in the list to open its Analog Test Card.</p>'; return; }
    if (isSite(f)) { host.innerHTML = siteCardHtml(f.properties); return; }
    var p = f.properties, h = '', role = roleOf(p);
    h += '<h2>' + esc(p.process_title) + '</h2>';
    h += '<p class="meta"><strong>' + esc(p.name) + '</strong>' + (p.country ? ' · ' + esc(p.country) : '') +
      ' · ' + num(p.lat, 3) + ', ' + num(p.lon, 3) + ' · footprint ' + esc(p.footprint_km) + ' km · ' +
      '<span class="tag ' + role + '">' + esc(roleLabel(role)) + '</span> <span class="note">' + esc(p.id) + '</span></p>';
    if (role !== 'hidden') h += '<p class="note">' + (role === 'control' ?
      'Control: a site that should match; it validates the method.' : 'Decoy: a site that looks similar but should fail; it validates the method.') + '</p>';
    if (p.process_summary) h += '<p>' + esc(p.process_summary) + '</p>';
    if (p.mock) h += '<p class="flag">MOCK feature - fake numbers.</p>';
    var l2 = p.lens_scores.L2;
    if (hasShadow(l2)) {
      h += '<div class="split-box"><p><strong>Terrain shadows: ' + esc(rankSigmaText(l2)) + '</strong>' +
        ' — this is what the site is a candidate for (long shadows over matching relief).</p>' +
        '<p class="note"><strong>Sun geometry: no Earth analog</strong> (σ ' + esc(num(l2.sigma, 1)) +
        '). The Sun circling the horizon at 0–7° all day needs latitude ≳ 83–86°; this was expected before scoring' +
        ' and is reported as a number.</p></div>';
    }
    h += verdictHtml(p);
    h += evidenceScaleHtml(p.lens_scores[state.lens]);

    h += '<h3>Fidelity per lens</h3><div class="tbl-wrap"><table><thead><tr><th>Lens</th><th>Target</th><th>σ</th><th>Percentile</th><th>d</th><th>Mode</th><th>Limiting factor</th><th>No analog</th></tr></thead><tbody>';
    var nullNote = false;
    Object.keys(p.lens_scores).forEach(function (lid) {
      var s = p.lens_scores[lid];
      var pct = (s.percentile === null || s.percentile === undefined) ? '—' : esc(num(s.percentile, 1));
      if (pct === '—') nullNote = true;
      var nn = (typeof s.n_null === 'number') ? ' <span class="note">(n=' + esc(s.n_null) + ')</span>' : '';
      h += '<tr><td>' + esc(lid) + '</td><td>' + esc(s.target) + '</td><td>' + esc(sigmaText(s)) + '</td><td>' + pct + nn +
        '</td><td>' + esc(num(s.d)) + '</td><td>' + esc(s.metric_mode || '—') + '</td><td>' + esc(s.limiting_factor) +
        '</td><td>' + (s.no_analog ? '<span class="flag">NO ANALOG</span>' : 'no') + '</td></tr>';
      if (lid === 'L2' || s.d_shadow !== undefined || s.sigma_shadow !== undefined) {
        h += '<tr><td></td><td colspan="7" class="note">' + esc(lid) + ' shadow part: d_shadow ' + esc(num(s.d_shadow)) +
          ', sigma_shadow ' + esc(num(s.sigma_shadow)) + '</td></tr>';
      }
    });
    h += '</tbody></table></div>';
    if (nullNote) h += '<p class="note">Percentile — : null sample &lt; 30</p>';

    var sel = p.lens_scores[state.lens];
    if (sel) {
      h += '<h3>Descriptors (' + esc(state.lens) + ' vs ' + esc(sel.target) + ')</h3>';
      var d = sel.descriptors || {}, keys = Object.keys(d);
      h += '<div id="radar" class="radar"><h4>Match per descriptor (1 = same as ' + esc(lensInfo(state.lens).body || 'target') + ' target)</h4>' + radarSvg(d) + '</div>';
      if (keys.length) {
        h += '<details class="fold"><summary>Descriptor table (' + keys.length + ')</summary><div class="tbl-wrap"><table><thead><tr><th>Descriptor</th><th>Earth</th><th>Target</th><th>z</th></tr></thead><tbody>';
        keys.forEach(function (k) {
          h += '<tr><td>' + esc(k) + '</td><td>' + esc(num(d[k].earth, 3)) + '</td><td>' + esc(num(d[k].target, 3)) +
            '</td><td>' + esc(num(d[k].z, 2)) + '</td></tr>';
        });
        h += '</tbody></table></div></details>';
      }
    } else h += '<div id="radar"></div>';

    h += '<h3>Test here</h3>' + listHtml((p.test_here || []).map(function (t) {
      return esc(t.tech) + (t.lens ? ' <span class="note">[' + esc(t.lens) + ']</span>' : '') +
        '<br><span class="note">NASA gap: ' + (t.nasa_gap ? esc(t.nasa_gap) : '—') + '</span>';
    }));
    h += '<h3>Cannot test here</h3>' + listHtml((p.cannot_test || []).map(esc));
    h += ledgerHtml(state.lens);

    var a = p.attention || {};
    h += '<h3>Attention</h3><p>' + (a.n_pubs === null || a.n_pubs === undefined ? '—' : esc(a.n_pubs)) + ' publications<br>' +
      '<span class="note">Query: <code>' + esc(a.query) + '</code><br>Source: ' + esc(a.source) + ' · ' + esc(a.date) + '</span></p>';

    var ac = p.access || {};
    h += '<h3>Access</h3><p>Travel time: ' + (ac.travel_time_h === null || ac.travel_time_h === undefined ? '—' : esc(ac.travel_time_h) + ' h') +
      ' · Protected area: ' + (ac.protected_area === null || ac.protected_area === undefined ? '—' : (ac.protected_area ? 'yes' : 'no')) +
      (ac.note ? '<br><span class="note">' + esc(ac.note) + '</span>' : '') + '</p>';

    h += '<h3>Evidence</h3><p><span class="badge ' + esc(p.evidence_status) + '">' + esc(p.evidence_status) + '</span> ' + esc(p.evidence_note || '') + '</p>';
    if (p.in_exclusion_buffer) h += '<p class="flag">In exclusion buffer.</p>';
    else h += '<p class="note">In exclusion buffer: no</p>';
    h += '<h3>Data sources</h3>' + listHtml((p.data_sources || []).map(esc));
    host.innerHTML = h;
  }

  // ---------- init ----------
  function init() {
    map = L.map('map', { worldCopyJump: true, minZoom: 1 }).setView([20, 30], 2);
    L.tileLayer('https://gibs.earthdata.nasa.gov/wmts/epsg3857/best/BlueMarble_ShadedRelief_Bathymetry/default/GoogleMapsCompatible_Level8/{z}/{y}/{x}.jpeg', {
      maxNativeZoom: 8, maxZoom: 10, attribution: 'NASA GIBS / Blue Marble'
    }).addTo(map);
    markerLayer = L.layerGroup().addTo(map);
    buildLegend();
    var hl = document.querySelector('.hdr-link');
    if (hl) hl.addEventListener('click', function () { $('limits').open = true; });
    $('lens-tabs').addEventListener('click', function (e) {
      var b = e.target.closest('button[data-lens]');
      if (b) setLens(b.getAttribute('data-lens'));
    });
    $('list').addEventListener('click', function (e) {
      var b = e.target.closest('button[data-id]');
      if (b) select(b.getAttribute('data-id'), true);
    });

    Promise.all([loadLenses(), loadLedger()]).then(function () {
      buildLensTabs();
      return loadData();
    }).then(function (res) {
      state.features = (res.data.features || []).filter(function (f) { return f && f.properties && f.geometry; });
      state.meta = res.data.metadata || {};
      if (res.mock) $('mock-banner').hidden = false;
      if (state.meta.provisional) $('prov-banner').hidden = false;
      var first = LENSES.filter(function (l) {
        return state.features.some(function (f) { return f.properties.lens_scores && f.properties.lens_scores[l.id]; });
      })[0];
      setLens(state.features.some(isSite) ? 'SITES' : (first ? first.id : LENSES[0].id));
    }).catch(function (err) {
      var b = $('error-banner'); b.textContent = 'Could not load data: ' + err.message; b.hidden = false;
      buildLensTabs();
      setLens(LENSES[0].id);
    });
  }
  init();
})();
