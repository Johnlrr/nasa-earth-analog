/* Source-bound terrain comparison. Presentation only: no scoring, classification or imputation. */
(function(root){
  'use strict';
  const esc=v=>String(v??'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
  const finite=v=>typeof v==='number'&&Number.isFinite(v);
  const fmt=v=>!finite(v)?'Not available':v!==0&&Math.abs(v)<.001?v.toExponential(2):String(parseFloat(v.toFixed(Math.abs(v)>=100?1:3)));
  const pct=v=>finite(v)?Math.round(v*100)+' %':'—';
  const names={connecting_ridge:'Connecting Ridge (Site01)',shackleton_rim:'Shackleton inner wall (Site04 centre)',jezero_margin:'Jezero margin',arcadia_planitia:'Arcadia Planitia'};
  const earthImages={
    E10K_453_921:{src:'media/qaidam-4km.png',name:'Da Qaidam',credit:'Copernicus Sentinel-2 / project B17 review',note:'Nominal 4 km study window; original review thumbnail. Acquisition date not recorded.'},
    'E10K_729_-319':{src:'media/peary-4km.png',name:'Peary Land',credit:'Copernicus Sentinel-2 / project B17 review',note:'Nominal 4 km study window; partial image coverage retained. Acquisition date not recorded.'},
    'E10K_244_-1498':{src:'media/hawaii-4km.png',name:'Mauna Loa–Mauna Kea',credit:'Copernicus Sentinel-2 / project B17 review',note:'Nominal 4 km study window; original review thumbnail. Acquisition date not recorded.'}
  };
  const targetImages={
    connecting_ridge:{src:'media/connecting-ridge-4km.png',name:names.connecting_ridge,credit:'NASA / GSFC / LRO / LOLA / PGDA 78',note:'4 km hillshade from the 5 m DEM (not a photograph).'},
    shackleton_rim:{src:'media/expedition/shackleton-wall-4km.png',name:names.shackleton_rim,credit:'NASA / GSFC / LRO / LOLA / PGDA 78',note:'4 km hillshade from the 5 m DEM, Site04 centre (not a photograph).'},
    arcadia_planitia:{src:'media/expedition/arcadia-planitia-ctx.png',name:names.arcadia_planitia,credit:'NASA MRO CTX / Caltech mosaic / Mars Trek–OnMars',note:'4 km CTX image at the target centre (44°N, 167°W). Ice depth is not visible in an image; SWIM maps it.'},
    jezero_margin:{src:'media/expedition/jezero-margin-ctx.png',name:names.jezero_margin,credit:'NASA MRO CTX / Caltech mosaic / Mars Trek–OnMars',note:'5 km CTX image chip, approximately 10.16 m/pixel. Black regions are missing mosaic coverage; imagery is not mineral evidence.'}
  };
  function contexts(feature,features,lens){
    if(!feature)return [];
    const p=feature.properties;
    if(p.feature_type!=='site')return [{key:p.id+':'+lens,lens,target:p.lens_scores?.[lens]?.target,cellId:p.id.replace(/^[^-]+-/,''),feature,name:p.name}];
    return (p.field||[]).filter(r=>r.target&&r.best_cell).map(r=>{
      const published=features.find(f=>f.properties.id===r.lens+'-'+r.best_cell&&f.properties.lens_scores?.[r.lens]?.target===r.target)||null;
      // member cells without a lens feature: Earth/target values exported from the pipeline tables (no z)
      const extra=root?.SimilitudeCellDescriptors?.[r.lens+':'+r.target+':'+r.best_cell];
      const cell=published||(extra?{properties:{id:r.lens+'-'+r.best_cell,name:p.name,role:'hidden',synthetic:true,evidence_note:extra.note,lens_scores:{[r.lens]:{target:r.target,descriptors:extra.descriptors}}}}:null);
      return {key:r.lens+':'+r.target+':'+r.best_cell,lens:r.lens,target:r.target,cellId:r.best_cell,feature:cell,name:p.name,row:r};
    });
  }
  function context(feature,features,lens,key){const list=contexts(feature,features,lens);return list.find(c=>c.key===key)||list.find(c=>c.feature)||list[0]||null;}
  function imagePair(c){return {earth:root?.SimilitudeFootprintImages?.[c?.cellId]||earthImages[c?.cellId]||root?.SimilitudeContextImages?.[c?.cellId]||null,target:targetImages[c?.target]||null};}
  function range(earth,target){const values=[earth,target].filter(finite),min=Math.min(0,...values),max=Math.max(0,...values);return {min,max,span:max-min||1};}
  function valueCell(v,other,side){
    if(!finite(v))return '<span class="not-recorded">Not available</span>';
    const r=range(v,other),zero=-r.min/r.span*100,pos=(v-r.min)/r.span*100;
    return '<span class="metric-value">'+fmt(v)+'</span><span class="metric-track '+side+'" aria-hidden="true" data-min="'+r.min+'" data-max="'+r.max+'"><i class="metric-zero" style="left:'+zero+'%"></i><i class="metric-bar" style="left:'+Math.min(zero,pos)+'%;width:'+Math.abs(pos-zero)+'%"></i></span>';
  }
  function difference(a,b){return finite(a)&&finite(b)?a-b:null;}
  function signature(rows){
    return rows.filter(r=>finite(r.z)&&finite(r.earth)&&finite(r.target)).slice().sort((a,b)=>Math.abs(a.z)-Math.abs(b.z));
  }
  function discovery(c,rows,labelFor,unitFor,feature){
    const ordered=signature(rows),measured=ordered.filter(r=>r.key!=='permafrost_flag'),near=measured[0]||ordered[0],far=ordered[ordered.length-1];
    const missing=gaps(feature,c.lens),limit=(c.feature?.properties.verdicts||[]).find(r=>r.lens===c.lens&&r.state==='NO-ANALOG');
    let h='<section class="discovery" aria-label="Scientific discovery"><p class="overline">'+esc(c.lens)+' / '+esc(c.name)+' → '+esc(names[c.target]||c.target)+'</p>';
    const g8=rows.find(r=>r.key==='frac_gt8'),g20=rows.find(r=>r.key==='frac_gt20');
    const slopeLine=g8&&finite(g8.earth)&&finite(g8.target)?pct(g8.earth)+' steeper than 8° here, '+pct(g8.target)+' at the target.':'';
    const slopeSub=g20&&finite(g20.earth)&&finite(g20.target)?'Steeper than 20°: '+pct(g20.earth)+' here, '+pct(g20.target)+' at the target.':'';
    h+='<h3>'+(slopeLine?esc(slopeLine):near?esc(labelFor(near.key))+' is the closest measured alignment.':'A recorded field relationship. Detailed measurements are not published.')+'</h3>';
    if(slopeLine&&slopeSub)h+='<p class="discovery-sub">'+esc(slopeSub)+'</p>';
    h+='<p class="discovery-boundary">'+(c.feature?.properties.role==='control'?'Validation control; this is not a qualified discovery.':c.feature?.properties.role==='decoy'?'Validation decoy; this is not a qualified discovery.':'A feature comparison supports a test question; it does not qualify hardware.')+'</p>';
    const v=(x,k)=>{if(!finite(x))return 'not available';const un=unitFor(k,c.lens)||'';if(un==='study flag')return x>=0.5?'yes':'no';if(/^fraction/.test(un))return Math.round(x*100)+' %';const t=Math.abs(x)>=10?x.toFixed(1):fmt(x);return un==='degrees'||un==='deg'||un==='°'?t+'°':un&&un!=='dimensionless'?t+' '+esc(un):t;};
    if(near)h+='<div class="interpretation"><section><h4>Closest match</h4><p>'+esc(labelFor(near.key))+': <strong>'+v(near.earth,near.key)+'</strong> here, <strong>'+v(near.target,near.key)+'</strong> at the target.</p></section><section><h4>Biggest difference</h4><p>'+esc(labelFor(far.key))+': <strong>'+v(far.earth,far.key)+'</strong> here, <strong>'+v(far.target,far.key)+'</strong> at the target.</p></section><section><h4>What remains unknown</h4><p>'+esc(missing.slice(0,3).map(r=>r.name).join(', '))+'. Measure on site.</p></section></div>';
    h+='</section><!--discovery-end-->';
    if(ordered.length){
      const extent=Math.max(1,...ordered.map(r=>Math.abs(r.z)));
      h+='<section class="similarity-signature" aria-label="Interactive similarity signature"><div class="criteria-heading"><h3>Every measure at a glance</h3></div><p class="measurement-note">A dot on the centre line means Earth equals the target on that measure. Tap a row for the values.</p>';
      h+=ordered.map(r=>'<details class="signature-feature"><summary><span>'+esc(labelFor(r.key))+'</span><span class="alignment-strip" aria-hidden="true"><i class="alignment-zero"></i><i class="alignment-dot" style="left:'+((r.z/extent+1)*50)+'%"></i></span><code>'+fmt(r.z)+'</code></summary><div class="feature-reading"><strong>'+esc(labelFor(r.key))+'</strong><p>Earth '+fmt(r.earth)+' / target '+fmt(r.target)+' '+esc(unitFor(r.key,c.lens))+' / recorded z '+fmt(r.z)+'.</p><p>Source field: <code>'+esc(r.key)+'</code>. '+(r.key.startsWith('rms_')?'RMS height difference at the recorded terrain lag.':r.key.startsWith('slope_')?'Slope-distribution statistic over the study footprint.':r.key.startsWith('frac_gt')?'Fraction of terrain above the named slope cutoff; not a vehicle safety limit.':'Task-specific descriptor; inspect the full method and source record before interpretation.')+'</p></div></details>').join('');
      h+='</section>';
    }
    const tests=(c.feature?.properties.test_here||[]).filter(t=>!t.lens||t.lens===c.lens);
    h+='<section class="mission-reading"><h3>What could be tested here?</h3><p>'+(tests.length?'Subject to field verification: '+esc(tests.map(t=>t.tech).join('; '))+'.':c.row?'Recorded field relationship: '+esc(c.row.variable)+'. Detailed test readiness has not been established.':'Consult the source test verdicts before planning a field trial.')+'</p>'+(limit?'<p><strong>Transfer boundary.</strong> '+esc(limit.reason)+(limit.facility?' Test context: '+esc(limit.facility)+'.':'')+'</p>':'')+'</section>';
    return h;
  }
  function photo(asset,side,label){
    if(!asset)return '';
    const info=asset?'<a class="terrain-image" href="'+esc(asset.src)+'" target="_blank" rel="noopener" aria-label="Open full image: '+esc(asset.name)+'"><img src="'+esc(asset.src)+'" alt="'+esc(asset.name+' — '+asset.credit)+'" decoding="async"><span class="image-unavailable" hidden>Image could not load. Source details remain below.</span><span class="image-open" aria-hidden="true">Open image ↗</span></a>':'<div class="terrain-image image-missing"><p>No verified image for this footprint</p><small>The comparison uses published measurements. No substitute landscape is shown.</small></div>';
    return '<figure class="terrain-half '+side+'"><div class="terrain-title"><span>'+esc(side==='earth'?(asset?.type?'EARTH / REGIONAL CONTEXT':'EARTH / TEST LOCATION'):'TARGET / '+label.body)+'</span><h3>'+esc(asset?.name||label.name)+'</h3></div>'+info+'<figcaption><strong>'+esc(asset?.credit||'Image not published in this catalog')+'</strong><p>'+esc(asset?.note||'A source-bound image is required before a visual terrain comparison can be made.')+'</p></figcaption></figure>';
  }
  function gaps(feature,lens){
    const common=[
      {name:'Relative humidity',unit:'% RH',reason:'Site-specific atmospheric humidity is not published. Measure weather during the proposed test.'},
      {name:'Soil moisture',unit:'volumetric water content',reason:'No matched soil-moisture measurements are published. Aridity P/PET is a climate index, not humidity or soil-water content.'},
      {name:'Local surface temperature',unit:'K',reason:'No contemporaneous site/target temperature pair is published. Planetary reference temperatures below are not local observations.'},
      {name:'Soil bearing strength / traction',unit:'kPa / test-specific',reason:'Not measured by the terrain comparison. Survey and instrument the soil before hardware testing.'}
    ];
    const p=feature?.properties;
    const rows=p?.feature_type==='site'?(p.unobserved||[]).filter(r=>r.lens===lens):(p?.verdicts||[]).filter(r=>r.lens===lens&&r.state==='UNOBSERVED');
    return common.concat(rows.map(r=>({name:r.variable,unit:'not measured',reason:r.reason})));
  }
  function render(input){
    const {feature,features,lens,key,ledger,lenses,rowsFor,labelFor,unitFor}=input,p=feature.properties;
    const all=contexts(feature,features,lens),c=context(feature,features,lens,key);
    if(!c)return '<p class="measurement-note">No target-specific footprint is published for this selection. Inspect its full study record.</p>';
    const body=lenses.find(l=>l.id===c.lens)?.body||'Target',assets=imagePair(c),rows=c.feature?rowsFor(c.feature,c.lens):[];
    let h='';
    if(p.feature_type==='site')h+='<div class="comparison-context"><label for="terrain-context">Compare a recorded footprint and target</label><select id="terrain-context">'+all.map(o=>'<option value="'+esc(o.key)+'"'+(o.key===c.key?' selected':'')+'>'+esc(o.lens+' · '+(names[o.target]||o.target))+'</option>').join('')+'</select></div>';
    const story=discovery(c,rows,labelFor,unitFor,feature),split=story.indexOf('<!--discovery-end-->')+20;
    h+=story.slice(0,split);
    const pics=photo(assets.earth,'earth',{body:'Earth',name:c.name||c.cellId})+photo(assets.target,'target',{body,name:names[c.target]||c.target});
    if(pics)h+='<div class="worlds-heading"><p class="overline">Earth / '+esc(body)+'</p><h3>Compare two worlds.</h3></div><div class="terrain-pair-view'+(assets.earth&&assets.target?'':' single')+'">'+pics+'</div><p class="terrain-provenance">Same 4 km window; different sensors and lighting. <a href="media/provenance.json">Image sources</a></p>';
    h+=root?.SimilitudeTerrain?.markup(c)||'';
    h+=story.slice(split);
    h+='<details class="technical-evidence"><summary>Full measurement table (Earth vs target)</summary><p class="measurement-note">One scale per row. z = standardized difference from the target, not a confidence.</p>';
    if(rows.length){
      h+='<div class="table-scroll" tabindex="0" role="region" aria-label="Scrollable detailed terrain criteria"><table class="comparison-table"><caption>Published '+esc(c.lens)+' descriptors / units retained</caption><thead><tr><th scope="col">Criterion / unit</th><th scope="col" class="earth-column">Earth</th><th scope="col" class="target-column">Target</th><th scope="col">z</th><th scope="col">Δ Earth − target</th></tr></thead><tbody>';
      h+=rows.map(r=>{const delta=difference(r.earth,r.target);return '<tr><th scope="row">'+esc(labelFor(r.key))+'<small><code>'+esc(r.key)+'</code> / '+esc(unitFor(r.key,c.lens))+'</small></th><td>'+valueCell(r.earth,r.target,'earth')+'</td><td>'+valueCell(r.target,r.earth,'target')+'</td><td>'+fmt(r.z)+'</td><td>'+(finite(delta)&&delta>0?'+':'')+fmt(delta)+'</td></tr>';}).join('')+'</tbody></table></div>';
      if(c.lens==='L1')h+='<p class="measurement-note criteria-footnote">30 m baseline. Slope cutoffs describe the terrain; they are not vehicle limits.</p>';
    }else h+='<p class="criteria-unavailable">The catalog records this field/target relationship, but does not publish its detailed cell descriptors. No slope, moisture or similarity values have been inferred.</p>';
    h+='</details>';
    if(c.row)h+='<p class="measurement-note">'+esc(String(c.row.reason||'').replace(/A12 robust set \(intersection \(i\)&\(ii\)&\(iii\)\);\s*/,'Passes all three terrain-test configurations; ').replace(/native rank i\/ii\/iii =/,'rank among lunar footprints'))+'</p>';
    if(c.feature?.properties.evidence_note)h+='<p class="measurement-note">Recorded observation: '+esc(c.feature.properties.evidence_note)+'</p>';
    if(c.lens==='L2')h+='<p class="measurement-note">Ranking uses terrain-shadow similarity. The Sun-geometry mismatch is separate; an Earth shadow match does not reproduce lunar illumination.</p>';
    const gl=gaps(feature,c.lens);
    h+='<section class="field-checklist"><h3>Measure on site before testing</h3><ul class="gap-chips">'+gl.map(r=>'<li>'+esc(r.name)+'</li>').join('')+'</ul><details><summary>Why these are not in the comparison</summary><ul class="gap-reasons">'+gl.map(r=>'<li><strong>'+esc(r.name)+'.</strong> '+esc(r.reason)+'</li>').join('')+'</ul></details></section>';
    const items=(ledger?.[body.toLowerCase()]?.items||[]).filter(i=>(i.applies_to||[]).includes(c.lens));
    if(items.length){
      const ref=x=>'<strong>'+ (finite(x?.value)?fmt(x.value)+' '+esc(x.unit||''):'Not available')+'</strong>'+(x?.note?'<small>'+esc(x.note)+'</small>':'');
      h+='<details class="env-details"><summary>What no Earth site reproduces: '+items.length+' conditions and the facility to use instead</summary><p class="measurement-note">Planetary references, not measurements at '+esc(c.name||c.cellId)+'.</p><div class="table-scroll" tabindex="0" role="region" aria-label="Planetary environmental differences"><table class="environment-table"><caption>Reference values, limitations and citations</caption><thead><tr><th scope="col">Condition</th><th scope="col">Earth reference</th><th scope="col">'+esc(body)+' reference</th><th scope="col">Engineering consequence</th></tr></thead><tbody>'+items.map(i=>'<tr><th scope="row">'+esc(i.quantity)+'</th><td>'+ref(i.earth)+'</td><td>'+ref(i.target)+'</td><td>'+esc(i.consequence)+(i.mitigation?'<small>Test setup: '+esc(i.mitigation)+'</small>':'')+(/^https?:\/\//i.test(i.source||'')?' <a href="'+esc(i.source)+'" target="_blank" rel="noopener">Source ↗</a>':'')+'</td></tr>').join('')+'</tbody></table></div></details>';
    }
    if(p.feature_type==='site'&&c.feature&&!c.feature.properties.synthetic)h+='<button type="button" class="button secondary open-footprint" data-comparison-cell="'+esc(c.feature.properties.id)+'" data-comparison-lens="'+esc(c.lens)+'">Open this footprint in Explorer ↗</button>';
    return h;
  }
  const api={contexts,context,imagePair,range,difference,fmt,gaps,signature,render};
  if(typeof module!=='undefined'&&module.exports)module.exports=api;
  if(root)root.SimilitudeSimilarities=api;
})(typeof window==='undefined'?null:window);
