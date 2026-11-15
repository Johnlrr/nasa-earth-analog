const test=require('node:test');
const assert=require('node:assert/strict');
const fs=require('node:fs');
const path=require('node:path');
const s=require('../web/similarities.js');
const e=require('../web/expedition.js');
const data=JSON.parse(fs.readFileSync(path.join(__dirname,'../web/data/candidates.geojson'),'utf8'));
const ledger=JSON.parse(fs.readFileSync(path.join(__dirname,'../web/data/ledger.json'),'utf8'));
const lenses=JSON.parse(fs.readFileSync(path.join(__dirname,'../web/data/lenses.json'),'utf8'));
const site=data.features.find(f=>f.properties.id==='site:E10K_453_921');
function render(feature,lens,key){return s.render({feature,features:data.features,lens,key,ledger,lenses,rowsFor:e.comparisonRows,labelFor:k=>k,unitFor:e.descriptorUnit});}
test('regional comparison binds both the exact member cell AND its recorded target',()=>{
  const options=s.contexts(site,data.features,'SITES');
  assert.equal(options.length,2);assert.equal(options[0].feature.properties.id,'L1-E10K_453_921');
  assert.equal(options[0].target,'connecting_ridge');assert.equal(options[1].feature,null);
  const wrong=structuredClone(site);wrong.properties.field[0].target='shackleton_rim';
  assert.equal(s.contexts(wrong,data.features,'SITES')[0].feature,null);
});
test('images never substitute an unrelated footprint or target',()=>{
  const c=s.context(site,data.features,'SITES');const pair=s.imagePair(c);
  assert.match(pair.earth.src,/qaidam/);assert.match(pair.target.src,/connecting-ridge/);
  assert.equal(s.imagePair({cellId:'E10K_691_-680',target:'shackleton_rim'}).earth,null);
  assert.match(s.imagePair({cellId:'E10K_691_-680',target:'shackleton_rim'}).target.src,/shackleton-wall-4km/);
});
test('row scales share one domain, including signed spectral values, with no missing-zero imputation',()=>{
  assert.deepEqual(s.range(-.2,.3),{min:-.2,max:.3,span:.5});
  assert.deepEqual(s.range(12,15),{min:0,max:15,span:15});
  assert.equal(s.difference(null,5),null);assert.equal(s.difference(0,5),-5);
  assert.equal(s.fmt(3e-10),'3.00e-10');assert.equal(s.fmt(null),'Not available');
});
test('the rendered pair includes measured values and clearly separate moisture gaps and planetary references',()=>{
  const html=render(site,'SITES');
  assert.match(html,/terrain-pair-view/);assert.match(html,/qaidam-4km.png/);assert.match(html,/connecting-ridge-4km.png/);
  const d=s.context(site,data.features,'SITES').feature.properties.lens_scores.L1.descriptors.slope_p50;
  assert.ok(html.includes(s.fmt(d.earth)));assert.ok(html.includes(s.fmt(d.target)));
  assert.match(html,/Relative humidity/);assert.match(html,/Soil moisture/);assert.match(html,/not humidity/);
  assert.match(html,/not measurements at/);assert.match(html,/3.00e-10 Pa/);assert.match(html,/Source ↗/);
});
test('unpublished member measurements do not inherit another target table',()=>{
  const option=s.contexts(site,data.features,'SITES')[1];const html=render(site,'SITES',option.key);
  assert.match(html,/does not publish its detailed cell descriptors/);
  assert.doesNotMatch(html,/<table class="comparison-table">/);
  assert.doesNotMatch(html,/No verified image/);assert.match(html,/shackleton-wall-4km/);
});
test('copied CTX image pixels remain identical to the original project observation',()=>{
  const a=fs.readFileSync(path.join(__dirname,'../web/media/expedition/jezero-margin-ctx.png'));
  const b=fs.readFileSync(path.join(__dirname,'../data/raw/mars/ctx_chips/jezero_margin.png'));
  assert.ok(a.equals(b));
});

test('signature orders only observed standardized differences without changing source data',()=>{
 const rows=[{key:'far',earth:1,target:3,z:-2},{key:'missing',earth:null,target:3,z:0},{key:'near',earth:1,target:1,z:.1}];
 const before=JSON.stringify(rows);assert.deepEqual(s.signature(rows).map(r=>r.key),['near','far']);assert.equal(JSON.stringify(rows),before);
});
test('the discovery interpretation preserves evidence role and exposes feature-level inspection',()=>{
 const f=data.features.find(f=>f.properties.id==='M1-ctl_lake_salda');const html=render(f,'M1');
 assert.match(html,/Validation control; this is not a qualified discovery/);assert.match(html,/What aligns/);assert.match(html,/What differs/);assert.match(html,/What remains unknown/);assert.match(html,/signature-feature/);assert.match(html,/not a new pass\/fail threshold/);
});
