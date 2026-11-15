const test = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const ui = require('../web/expedition.js');
const data = JSON.parse(fs.readFileSync(require('node:path').join(__dirname,'../web/data/candidates.geojson'),'utf8'));

test('missing measurements remain missing; real zero remains zero',()=>{
  const f={properties:{lens_scores:{L1:{descriptors:{slope_p50:{earth:0,target:12,z:null},rms_s1:{earth:null,target:0.1}}}}}};
  const rows=ui.comparisonRows(f,'L1');
  assert.equal(rows[0].earth,0);assert.equal(ui.number(rows[0].earth),'0.000');
  assert.equal(ui.number(rows[1].earth),'Not available');assert.equal(rows[1].z,null);
  assert.equal(ui.number(NaN),'Not available');
});
test('raw comparison retains published values without converting scores into confidence',()=>{
  let count=0;
  for(const f of data.features)for(const [lens,s] of Object.entries(f.properties.lens_scores||{})){
    const rows=ui.comparisonRows(f,lens);
    for(const r of rows){count++;assert.equal(r.earth,s.descriptors[r.key].earth??null);assert.equal(r.target,s.descriptors[r.key].target??null);assert.equal(r.z,s.descriptors[r.key].z??null);}
  }
  assert.ok(count>100);
});
test('controls and decoys cannot be described as qualified discoveries',()=>{
  for(const role of ['control','decoy'])assert.match(ui.classification({properties:{role}}),/not a discovery/);
  assert.match(ui.classification({properties:{feature_type:'site'}}),/regional group/);
  assert.match(ui.classification(null),/No selection/);
});
test('known terrain, illumination, spectral and ice units are explicit',()=>{
  assert.equal(ui.descriptorUnit('slope_p90','L1'),'degrees');
  assert.equal(ui.descriptorUnit('rms_s8','L1'),'metres');
  assert.equal(ui.descriptorUnit('shadow_e5','L2'),'fraction (0 to 1)');
  assert.equal(ui.descriptorUnit('BD2290','M1'),'spectral index (dimensionless)');
  assert.equal(ui.descriptorUnit('ft_cycles_yr','X1'),'annual count');
  assert.equal(ui.descriptorUnit('unknown_future_field','L1'),'unit not published');
});
