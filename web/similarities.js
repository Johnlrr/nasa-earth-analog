/* Source-bound terrain comparison. Presentation only: no scoring, classification or imputation. */
(function(root){
  'use strict';
  const esc=v=>String(v??'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
  const finite=v=>typeof v==='number'&&Number.isFinite(v);
  const fmt=v=>!finite(v)?'Not available':v!==0&&Math.abs(v)<.001?v.toExponential(2):v.toFixed(3);
  const names={connecting_ridge:'Connecting Ridge (Site01)',shackleton_rim:'Shackleton inner wall (Site04 centre)',jezero_margin:'Jezero margin',arcadia_planitia:'Arcadia Planitia'};
  const earthImages={
    E10K_453_921:{src:'media/qaidam-4km.png',name:'Da Qaidam',credit:'Copernicus Sentinel-2 / project B17 review',note:'Nominal 4 km study window; original review thumbnail. Acquisition date not recorded.'},
    'E10K_729_-319':{src:'media/peary-4km.png',name:'Peary Land',credit:'Copernicus Sentinel-2 / project B17 review',note:'Nominal 4 km study window; partial image coverage retained. Acquisition date not recorded.'},
    'E10K_244_-1498':{src:'media/hawaii-4km.png',name:'Mauna Loa–Mauna Kea',credit:'Copernicus Sentinel-2 / project B17 review',note:'Nominal 4 km study window; original review thumbnail. Acquisition date not recorded.'}
  };
  const targetImages={
    connecting_ridge:{src:'media/connecting-ridge-4km.png',name:names.connecting_ridge,credit:'NASA / GSFC / LRO / LOLA / PGDA 78',note:'4 km DEM-derived hillshade, not a photograph. Native DEM 5 m; terrain comparison uses a 30 m baseline. Illustrative lighting.'},
    jezero_margin:{src:'media/expedition/jezero-margin-ctx.png',name:names.jezero_margin,credit:'NASA MRO CTX / Caltech mosaic / Mars Trek–OnMars',note:'5 km CTX image chip, approximately 10.16 m/pixel. Black regions are missing mosaic coverage; imagery is not mineral evidence.'}
  };
  function contexts(feature,features,lens){
    if(!feature)return [];
    const p=feature.properties;
    if(p.feature_type!=='site')return [{key:p.id+':'+lens,lens,target:p.lens_scores?.[lens]?.target,cellId:p.id.replace(/^[^-]+-/,''),feature,name:p.name}];
    return (p.field||[]).filter(r=>r.target&&r.best_cell).map(r=>{
      const cell=features.find(f=>f.properties.id===r.lens+'-'+r.best_cell&&f.properties.lens_scores?.[r.lens]?.target===r.target)||null;
      return {key:r.lens+':'+r.target+':'+r.best_cell,lens:r.lens,target:r.target,cellId:r.best_cell,feature:cell,name:p.name,row:r};
    });
  }
  function context(feature,features,lens,key){const list=contexts(feature,features,lens);return list.find(c=>c.key===key)||list.find(c=>c.feature)||list[0]||null;}
  function imagePair(c){return {earth:earthImages[c?.cellId]||null,target:targetImages[c?.target]||null};}
  function range(earth,target){const values=[earth,target].filter(finite),min=Math.min(0,...values),max=Math.max(0,...values);return {min,max,span:max-min||1};}
  function valueCell(v,other,side){
    if(!finite(v))return '<span class="not-recorded">Not available</span>';
    const r=range(v,other),zero=-r.min/r.span*100,pos=(v-r.min)/r.span*100;
    return '<span class="metric-value">'+fmt(v)+'</span><span class="metric-track '+side+'" aria-hidden="true" data-min="'+r.min+'" data-max="'+r.max+'"><i class="metric-zero" style="left:'+zero+'%"></i><i class="metric-bar" style="left:'+Math.min(zero,pos)+'%;width:'+Math.abs(pos-zero)+'%"></i></span>';
  }
  function difference(a,b){return finite(a)&&finite(b)?a-b:null;}
  function photo(asset,side,label){
    const info=asset?'<a class="terrain-image" href="'+esc(asset.src)+'" target="_blank" rel="noopener" aria-label="Open full image: '+esc(asset.name)+'"><img src="'+esc(asset.src)+'" alt="'+esc(asset.name+' — '+asset.credit)+'" decoding="async"><span class="image-unavailable" hidden>Image could not load. Source details remain below.</span><span class="image-open" aria-hidden="true">Open image ↗</span></a>':'<div class="terrain-image image-missing"><p>No verified image for this footprint</p><small>The comparison uses published measurements. No substitute landscape is shown.</small></div>';
    return '<figure class="terrain-half '+side+'"><div class="terrain-title"><span>'+esc(side==='earth'?'EARTH / TEST LOCATION':'TARGET / '+label.body)+'</span><h3>'+esc(asset?.name||label.name)+'</h3></div>'+info+'<figcaption><strong>'+esc(asset?.credit||'Image not published in this catalog')+'</strong><p>'+esc(asset?.note||'A source-bound image is required before a visual terrain comparison can be made.')+'</p></figcaption></figure>';
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
    let h='<p class="similarities-intro">Compare the terrain, then inspect the measurements. Visual resemblance alone does not establish an analog.</p>';
    if(p.feature_type==='site')h+='<div class="comparison-context"><label for="terrain-context">Compare a recorded footprint and target</label><select id="terrain-context">'+all.map(o=>'<option value="'+esc(o.key)+'"'+(o.key===c.key?' selected':'')+'>'+esc(o.lens+' / '+(names[o.target]||o.target)+' / '+o.cellId+(o.feature?'':' / detailed values unavailable'))+'</option>').join('')+'</select><p><code>'+esc(c.cellId)+'</code> / This footprint only. Values are not averaged across the regional group.</p></div>';
    h+='<div class="terrain-pair-view">'+photo(assets.target,'target',{body,name:names[c.target]||c.target})+photo(assets.earth,'earth',{body:'Earth',name:c.name||c.cellId})+'</div>';
    h+='<p class="terrain-provenance">Images retain their original proportions. Different sensors and lighting; not co-registered. The nominal window labels are not a calibrated image scale. <a href="media/provenance.json">Image provenance</a> · <a href="media/expedition/similarities-sources.json">Comparison sources</a></p>';
    h+='<div class="criteria-heading"><h3>Measured terrain &amp; mission criteria</h3><span class="comparison-key"><i class="key-earth"></i>Earth <i class="key-target"></i>Target</span></div><p class="measurement-note">'+esc(c.cellId)+' → '+esc(names[c.target]||c.target)+'. Each row shares one linear scale between Earth and target; scales differ between criteria. Δ = Earth − target. z is the recorded standardized difference, not confidence.</p>';
    if(rows.length){
      h+='<p class="table-hint">Scroll the table horizontally on small screens to inspect every column.</p><div class="table-scroll" tabindex="0" role="region" aria-label="Scrollable detailed terrain criteria"><table class="comparison-table"><caption>Published '+esc(c.lens)+' descriptors / units retained</caption><thead><tr><th scope="col">Criterion / unit</th><th scope="col" class="earth-column">Earth</th><th scope="col" class="target-column">Target</th><th scope="col">z</th><th scope="col">Δ Earth − target</th></tr></thead><tbody>';
      h+=rows.map(r=>{const delta=difference(r.earth,r.target);return '<tr><th scope="row">'+esc(labelFor(r.key))+'<small><code>'+esc(r.key)+'</code> / '+esc(unitFor(r.key,c.lens))+'</small></th><td>'+valueCell(r.earth,r.target,'earth')+'</td><td>'+valueCell(r.target,r.earth,'target')+'</td><td>'+fmt(r.z)+'</td><td>'+(finite(delta)&&delta>0?'+':'')+fmt(delta)+'</td></tr>';}).join('')+'</tbody></table></div>';
      if(c.lens==='L1')h+='<p class="measurement-note criteria-footnote">Terrain comparison uses a 30 m baseline. The 8°, 15° and 20° slope cutoffs describe the terrain distribution; they are not vehicle safety limits. Metre-scale obstacles and soil response still require field measurements.</p>';
    }else h+='<p class="criteria-unavailable">The catalog records this field/target relationship, but does not publish its detailed cell descriptors. No slope, moisture or similarity values have been inferred.</p>';
    if(c.row)h+='<p class="measurement-note">Recorded field evidence: '+esc(c.row.variable)+' — '+esc(c.row.reason||'No additional note published.')+'</p>';
    if(c.feature?.properties.evidence_note)h+='<p class="measurement-note">Recorded observation: '+esc(c.feature.properties.evidence_note)+'</p>';
    if(c.lens==='L2')h+='<p class="measurement-note">Ranking uses terrain-shadow similarity. The Sun-geometry mismatch is separate; an Earth shadow match does not reproduce lunar illumination.</p>';
    h+='<div class="criteria-heading"><h3>Measurements still needed</h3><span class="note">Not included in the similarity score</span></div><div class="table-scroll" tabindex="0" role="region" aria-label="Missing engineering measurements"><table class="engineering-gaps"><caption>Unmeasured site conditions / no values imputed</caption><thead><tr><th scope="col">Criterion</th><th scope="col">Earth</th><th scope="col">Target</th><th scope="col">What the test plan needs</th></tr></thead><tbody>'+gaps(feature,c.lens).map(r=>'<tr><th scope="row">'+esc(r.name)+'<small>'+esc(r.unit)+'</small></th><td>Not available</td><td>Not available</td><td>'+esc(r.reason)+'</td></tr>').join('')+'</tbody></table></div>';
    const items=(ledger?.[body.toLowerCase()]?.items||[]).filter(i=>(i.applies_to||[]).includes(c.lens));
    if(items.length){
      const ref=x=>'<strong>'+ (finite(x?.value)?fmt(x.value)+' '+esc(x.unit||''):'Not available')+'</strong>'+(x?.note?'<small>'+esc(x.note)+'</small>':'');
      h+='<div class="criteria-heading"><h3>Planetary environment / reference conditions</h3></div><p class="measurement-note">Published transfer-ledger values for Earth and '+esc(body)+'. These are planetary or literature references, not measurements at '+esc(c.name||c.cellId)+'. They do not enter the terrain score.</p><div class="table-scroll" tabindex="0" role="region" aria-label="Planetary environmental differences"><table class="environment-table"><caption>Reference values, limitations and citations</caption><thead><tr><th scope="col">Condition</th><th scope="col">Earth reference</th><th scope="col">'+esc(body)+' reference</th><th scope="col">Engineering consequence</th></tr></thead><tbody>'+items.map(i=>'<tr><th scope="row">'+esc(i.quantity)+'</th><td>'+ref(i.earth)+'</td><td>'+ref(i.target)+'</td><td>'+esc(i.consequence)+(i.mitigation?'<small>Test setup: '+esc(i.mitigation)+'</small>':'')+(/^https?:\/\//i.test(i.source||'')?' <a href="'+esc(i.source)+'" target="_blank" rel="noopener">Source ↗</a>':'')+'</td></tr>').join('')+'</tbody></table></div>';
    }
    if(p.feature_type==='site'&&c.feature)h+='<button type="button" class="button secondary open-footprint" data-comparison-cell="'+esc(c.feature.properties.id)+'" data-comparison-lens="'+esc(c.lens)+'">Open this footprint in Explorer ↗</button>';
    return h;
  }
  const api={contexts,context,imagePair,range,difference,fmt,gaps,render};
  if(typeof module!=='undefined'&&module.exports)module.exports=api;
  if(root)root.SimilitudeSimilarities=api;
})(typeof window==='undefined'?null:window);
