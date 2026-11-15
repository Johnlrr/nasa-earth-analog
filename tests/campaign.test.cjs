const test = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const ui = require('../web/campaign.js');
const data = JSON.parse(fs.readFileSync(path.join(__dirname, '../web/data/candidates.geojson'), 'utf8'));
const catalog = ui.catalogFrom(data);

test('published target-specific evidence drives the worked example', () => {
  assert.equal(catalog.length, 3);
  const state = ui.defaults();
  state.selected = ['site:E10K_453_921'];
  let rows = ui.matrix(state, catalog);
  assert.equal(rows.find(r => r.id === 'terrain').state, 'modelled');
  assert.equal(rows.find(r => r.id === 'shadow').state, 'unresolved');
  state.selected.push('site:E10K_244_-1498');
  rows = ui.matrix(state, catalog);
  assert.equal(rows.find(r => r.id === 'shadow').state, 'modelled');
  for (const id of ['lighting', 'obstacles']) assert.equal(rows.find(r => r.id === id).state, 'unresolved');
  state.selected = [];
  assert.ok(ui.matrix(state, catalog).every(r => r.state !== 'modelled'));
});

test('different planetary targets cannot supply evidence for Connecting Ridge', () => {
  const other = structuredClone(data);
  for (const f of other.features) for (const row of f.properties.field || []) row.target = 'shackleton_rim';
  assert.deepEqual(ui.catalogFrom(other), []);
});

test('export preserves uncertainty, exact records, provenance and unverified notes', () => {
  const state = ui.defaults();
  state.selected = ['site:E10K_729_-319'];
  state.route = '<script>alert("unsafe")</script>';
  state.objectives.push('gravity');
  const pack = ui.evidencePack(state, catalog, data, 'test-hash');
  assert.equal(pack.source.sha256, 'test-hash');
  assert.equal(pack.proposed_route_or_setup.geometry, null);
  assert.equal(pack.test_matrix.find(r => r.id === 'gravity').state, 'facility_needed');
  assert.ok(pack.selected_footprints[0].caution.includes('ArcticDEM'));
  assert.equal(pack.selected_footprints[0].matching_evidence[0].best_cell, 'E10K_729_-319');
  assert.equal(pack.selected_footprints[0].footprint_location_status, 'exact_cell_coordinates_not_in_web_catalog');
  assert.ok(pack.reconnaissance.every(r => r.verification_status === 'not_verified'));
  const html = ui.briefHTML(pack);
  assert.ok(!html.includes('<script>'));
  assert.ok(html.includes('&lt;script&gt;'));
  assert.ok(html.includes('Original site record'));
});

test('persisted state is bounded and never injects unknown selections', () => {
  const state = ui.cleanState({ selected: ['fake', 'site:E10K_453_921', 'site:E10K_453_921'], objectives: ['fake'], task: 'mars', name: 'x'.repeat(1000), route: 'x'.repeat(9000) });
  assert.equal(state.selected.length, 1);
  assert.equal(state.task, 'navigation');
  assert.deepEqual(state.objectives, []);
  assert.equal(state.name.length, 100);
  assert.equal(state.route.length, 2000);
});

test('provisional and mock scientific records cannot be exported as published evidence', () => {
  assert.throws(() => ui.catalogFrom({ features: [], metadata: { mock: true } }));
  assert.throws(() => ui.catalogFrom({ features: [], metadata: { provisional: true } }));
});
