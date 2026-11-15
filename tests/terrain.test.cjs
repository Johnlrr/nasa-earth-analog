const test=require('node:test'),assert=require('node:assert/strict'),t=require('../web/terrain.js');
test('profile keeps missing samples missing and uses each surface start as its own datum',()=>{const p=t.profile({grid:[[100,null,130,90]],step_m:50},0);assert.equal(p[0].relative,0);assert.equal(p[1].relative,null);assert.equal(p[2].relative,30);assert.equal(p[3].x,150)});
test('display slope is zero for a flat grid and 45 degrees for a unit plane',()=>{assert.equal(t.slope({grid:[[4,4,4],[4,4,4],[4,4,4]],step_m:1},1,1),0);assert.ok(Math.abs(t.slope({grid:[[0,1,2],[0,1,2],[0,1,2]],step_m:1},1,1)-45)<1e-9)});
test('missing neighbours never become artificial flat terrain',()=>{assert.equal(t.slope({grid:[[null,1,2],[null,1,2],[0,1,2]],step_m:1},1,1),null)});
