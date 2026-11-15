/* Five-act presentation layer. app.js remains the authority for lens, ordering and selection. */
(function () {
  'use strict';
  const e = value => String(value == null ? '' : value).replace(/[&<>"']/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
  const number = value => typeof value === 'number' && Number.isFinite(value) ? value.toFixed(3) : 'Not available';
  function descriptorUnit(key, lens) {
    if (/^slope_p/.test(key)) return 'degrees';
    if (/^rms_s/.test(key)) return 'metres';
    if (/^(frac_gt|shadow_e|lowsun_)/.test(key)) return 'fraction (0 to 1)';
    if (key === 'ft_cycles_yr') return 'annual count';
    if (key === 'permafrost_flag') return 'study flag';
    if (['hurst','ice_depth_ratio','aridity_p_pet'].includes(key)) return 'dimensionless';
    return lens === 'M1' ? 'spectral index (dimensionless)' : 'unit not published';
  }
  function comparisonRows(feature, lens) {
    const descriptors = feature?.properties?.lens_scores?.[lens]?.descriptors || {};
    return Object.entries(descriptors).map(([key, values]) => ({key, unit:descriptorUnit(key,lens),earth:values?.earth ?? null,target:values?.target ?? null,z:values?.z ?? null}));
  }
  function descriptorLabel(key) {
    const labels = {slope_p50:'Median slope',slope_p90:'90th percentile slope',hurst:'Hurst exponent',lowsun_frac_daylight:'Low Sun / daylight fraction',lowsun_az_coverage:'Low-Sun azimuth coverage',permafrost_flag:'Permafrost study flag',ice_depth_ratio:'Ice depth / drill reach',aridity_p_pet:'Aridity / precipitation to PET',ft_cycles_yr:'Freeze-thaw cycles per year'};
    if (labels[key]) return labels[key];
    if (/^frac_gt\d+$/.test(key)) return 'Fraction with slope above '+key.slice(7)+'°';
    if (/^shadow_e\d+$/.test(key)) return 'Terrain shadow at '+key.slice(8)+'° Sun elevation';
    if (/^rms_s\d+$/.test(key)) return 'RMS roughness / '+key.slice(4);
    return key;
  }
  function classification(feature) {
    const p = feature?.properties;
    if (!p) return 'No selection';
    if (p.feature_type === 'site') return 'Showcase site / regional group';
    if (p.role === 'control') return 'Validation control / not a qualified discovery';
    if (p.role === 'decoy') return 'Validation decoy / not a qualified discovery';
    return 'Engine-qualified cell / ' + (p.evidence_status || 'evidence status not published');
  }
  if (typeof module !== 'undefined' && module.exports) module.exports = {comparisonRows,descriptorUnit,classification,number};
  if (typeof document === 'undefined') return;
  const $ = id => document.getElementById(id);
  let current = null, pendingLens = 'L1', planet = 'moon', appliedInitial = false, comparisonOpen = false, lastTrigger = null, returnFocus = null, initialViewShown = false;
  const reduced = () => window.matchMedia('(prefers-reduced-motion: reduce)').matches;
  const api = () => window.SimilitudeExplorer;
  const validLens = id => ['SITES','L1','L2','M1','X1'].includes(id);
  let comparisonContextKey = null, comparisonOwner = null;
  function route() {
    const hash = location.hash.slice(1);
    if (['mission','choose','explorer','comparison','dossier'].includes(hash)) return hash;
    return document.documentElement.dataset.startView || 'mission';
  }
  function focus(id) { if (initialViewShown) requestAnimationFrame(() => $(id)?.focus({preventScroll:true})); }
  function go(hash) { if (location.hash === '#' + hash) showView(hash); else location.hash = hash; }
  function showView(view) {
    const focusTarget = returnFocus; returnFocus = null;
    const isExplorer = ['explorer','comparison','dossier'].includes(view);
    $('mission').hidden = view !== 'mission'; $('choose').hidden = view !== 'choose'; $('explorer').hidden = !isExplorer;
    if (isExplorer) {
      api()?.resize(); requestAnimationFrame(() => api()?.resize());
      if (view === 'comparison' || view === 'dossier') comparisonOpen = !!current?.selected;
      syncSelection(view === 'dossier');
      if (view === 'comparison' && current?.selected) { $('comparison').scrollIntoView({block:'start'}); focus(focusTarget === 'evidence-trigger' ? 'open-dossier' : 'comparison-heading'); }
      else if (view === 'dossier' && current?.selected) { $('dossier').scrollIntoView({block:'start'}); focus('dossier-heading'); }
      else { window.scrollTo({top:0,behavior:'instant'}); if (focusTarget === 'results') restoreListFocus(); else focus('explorer-heading'); }
    } else { document.documentElement.classList.remove('earth-arrival'); window.scrollTo({top:0,behavior:'instant'}); focus(view === 'choose' ? 'choose-heading' : 'mission-heading'); }
  }
  function renderChoices() {
    if (!current) return;
    document.querySelectorAll('[data-planet]').forEach(button => button.setAttribute('aria-pressed',String(button.dataset.planet === planet)));
    const lenses = current.lenses.filter(l => l.body.toLowerCase() === planet);
    if (!lenses.some(l => l.id === pendingLens)) pendingLens = lenses[0]?.id || 'L1';
    $('mission-options').innerHTML = lenses.map(l => '<button type="button" class="task-option" data-task="'+e(l.id)+'" aria-pressed="'+(pendingLens===l.id)+'"><small>'+e(l.id)+' / '+e(l.body)+'</small><strong>'+e(l.name)+'</strong><span>'+e(l.question || 'Inspect this mission task in the Explorer.')+'</span></button>').join('');
    const config = current.configs.find(l => l.id === pendingLens);
    const baselineUnit = {dem_m:'m terrain baseline',grid_km:'km grid',spectral_grid_nm:'nm spectral grid'};
    $('task-scope').textContent = config ? 'Study footprint: '+config.footprint_km+' km. '+(config.baseline ? config.baseline.value+' '+(baselineUnit[config.baseline.type] || config.baseline.type)+'.' : '') : '';
    $('find-analogs').disabled = current.status !== 'ready';
    $('task-status').hidden = current.status === 'ready';
    $('task-status').textContent = current.status === 'error' ? 'Study data could not load. Open Explorer for the error details, or read the evidence report below.' : 'Loading published study data…';
  }
  function renderComparison() {
    const f = current.selected; if (!f) return;
    const p = f.properties;
    $('selected-name').textContent = p.name || p.id;
    $('selected-class').textContent = classification(f);
    $('dossier-subtitle').textContent = (p.name || p.id)+' / '+current.lens+' / '+classification(f);
    const owner = p.id+':'+current.lens;
    if (owner !== comparisonOwner) { comparisonContextKey = null; comparisonOwner = owner; }
    $('comparison-content').innerHTML = window.SimilitudeSimilarities.render({feature:f,features:current.features,lens:current.lens,key:comparisonContextKey,ledger:current.ledger,lenses:current.lenses,rowsFor:comparisonRows,labelFor:descriptorLabel,unitFor:descriptorUnit});
    const insightHeading=$('comparison-content').querySelector('.discovery>h3');
    $('comparison-heading').textContent=insightHeading?.textContent||'Inspect the recorded evidence';
    insightHeading?.remove();
    $('comparison-content').querySelector('.similarities-intro')?.remove();
    $('comparison-content').querySelectorAll('.engineering-gaps,.environment-table').forEach(table=>{
      const scroll=table.closest('.table-scroll'), prior=scroll.previousElementSibling;
      const heading=prior.matches('.criteria-heading')?prior:prior.previousElementSibling;
      if(!heading?.matches('.criteria-heading'))return;
      const details=document.createElement('details');details.className='technical-evidence';
      const summary=document.createElement('summary');summary.textContent=table.classList.contains('engineering-gaps')?'Unmeasured conditions / field measurements needed':'Planetary transfer limits / values, implications & sources';
      heading.before(details);details.append(summary);
      let node=heading;while(node){const next=node.nextSibling;details.append(node);if(node===scroll)break;node=next;}
    });
    const missionReading=$('comparison-content').querySelector('.mission-reading');
    if(missionReading)$('comparison-content').append(missionReading);
    const facility = p.feature_type === 'site' ? (p.facility || []) : (p.verdicts || []).filter(r => r.state !== 'TRANSFERS' && (!r.lens || r.lens === current.lens));
    const unknown = p.unobserved || [];
    const texts = [...facility.map(r => ({name:r.variable,reason:r.reason,facility:r.facility})),...unknown.map(r => ({name:r.variable,reason:r.reason}))];
    let limits = '<h3>What cannot transfer / what remains unknown</h3>';
    if (texts.length) limits += '<ul>'+texts.map(r => '<li>'+e(r.name)+(r.reason ? '<small>'+e(r.reason)+'</small>' : '')+(r.facility ? '<small>Test context: '+e(r.facility)+'</small>' : '')+'</li>').join('')+'</ul>';
    else if (p.cannot_test?.length) limits += '<ul>'+p.cannot_test.map(t => '<li>'+e(t)+'</li>').join('')+'</ul>';
    else limits += '<p class="note">No item-specific transfer limits are published in this record. This absence does not establish operational readiness. Consult the full study record and Data &amp; limits.</p>';
    $('transfer-limits').innerHTML = limits;
  }
  function syncSelection(openDossier) {
    const hasSelection = !!current?.selected;
    $('selection-guide').hidden = hasSelection && comparisonOpen;
    $('comparison').hidden = !hasSelection || !comparisonOpen;
    $('dossier').hidden = !hasSelection || !openDossier;
    if (hasSelection) renderComparison();
  }
  function update(reason) {
    current = api()?.getState(); if (!current) return;
    $('loading-banner').hidden = current.status !== 'loading';
    $('workspace').setAttribute('aria-busy',String(current.status==='loading'));
    const lens = current.lenses.find(l => l.id === current.lens);
    $('map-task-label').textContent = current.lens === 'SITES' ? 'Grouped site overview' : current.lens+' / '+(lens?.name || '');
    $('score-help').textContent = current.lens === 'SITES' ? 'Regional groups, not a single ranked score.' : current.lens === 'L2' ? 'Lower σ_shadow is a closer terrain-shadow match. Sun geometry is separate.' : 'Lower σ is a closer feature match. It is not confidence.';
    if (!appliedInitial && current.status === 'ready') {
      appliedInitial = true; const requested = new URLSearchParams(location.search).get('lens');
      if (validLens(requested) && requested !== current.lens) { api().setLens(requested); return; }
    }
    if (current.status === 'error') { $('list').innerHTML = '<li class="empty">Study data could not load. <a href="'+e(location.pathname+location.search+location.hash)+'">Reload this view</a> or <a href="evidence.html">read the evidence report</a>.</li>'; }
    renderChoices();
    const example = document.querySelector('[data-terrain-example]');
    if (example) example.disabled = current.status !== 'ready' || !current.features.some(f=>f.properties.id==='site:E10K_453_921');
    if (reason === 'selection') comparisonOpen = true;
    if (!current.selected) comparisonOpen = false;
    syncSelection(route() === 'dossier');
    if (reason === 'selection' && !$('explorer').hidden) { $('comparison').scrollIntoView({block:'start',behavior:reduced()?'instant':'smooth'}); focus('comparison-heading'); }
    if (reason === 'lens' && /^https?:$/.test(location.protocol)) {
      const url = new URL(location.href); url.searchParams.set('lens',current.lens); history.replaceState(null,'',url);
    }
    document.documentElement.dataset.ready = current.status;
    decorateMarkers();
  }
  function decorateMarkers() {
    api()?.markerElements().forEach(({id,element}) => {
      if (!element) return;
      const f = current.visible.find(f=>f.properties.id===id); if (!f) return;
      element.setAttribute('tabindex','0'); element.setAttribute('role','button');
      element.setAttribute('aria-label',(f.properties.name || id)+' / '+classification(f));
      element.setAttribute('aria-pressed',String(id===current.selectedId));
      element.onkeydown = event => { if (event.key==='Enter'||event.key===' ') {event.preventDefault();lastTrigger={id};api().select(id,false);} };
      element.onmouseenter = () => highlight(id);
      element.onmouseleave = () => highlight(null);
      element.onfocus = () => highlight(id);
      element.onblur = () => highlight(null);
    });
  }
  function highlight(id) {
    api()?.markerElements().forEach(m=>m.element?.classList.toggle('linked-focus',m.id===id));
    document.querySelectorAll('#list [data-id]').forEach(b=>b.classList.toggle('linked-focus',b.dataset.id===id));
  }
  function restoreListFocus() {
    requestAnimationFrame(() => {
      const button = [...document.querySelectorAll('#list [data-id]')].find(b=>b.dataset.id===(current?.selectedId || lastTrigger?.id));
      if (button) button.focus({preventScroll:true}); else focus('explorer-heading');
    });
  }
  document.addEventListener('similitude:change',event=>update(event.detail.reason));
  window.addEventListener('hashchange',()=>showView(route()));
  document.querySelectorAll('[data-planet]').forEach(button=>button.addEventListener('click',()=>{planet=button.dataset.planet;renderChoices();}));
  $('mission-options').addEventListener('click',event=>{const button=event.target.closest('[data-task]');if(!button)return;pendingLens=button.dataset.task;renderChoices();document.querySelector('[data-task="'+pendingLens+'"]').focus({preventScroll:true});});
  $('find-analogs').addEventListener('click',()=>{
    if(!current || current.status!=='ready')return;
    api().setLens(pendingLens); go('explorer');
    if(!reduced()) {document.documentElement.classList.add('earth-arrival');setTimeout(()=>document.documentElement.classList.remove('earth-arrival'),750);}
  });
  $('list').addEventListener('click',event=>{const b=event.target.closest('[data-id]');if(b)lastTrigger={id:b.dataset.id};},true);
  $('list').addEventListener('focusin',event=>highlight(event.target.closest('[data-id]')?.dataset.id));
  $('list').addEventListener('focusout',()=>highlight(null));
  $('list').addEventListener('pointerover',event=>highlight(event.target.closest('[data-id]')?.dataset.id));
  $('list').addEventListener('pointerleave',()=>highlight(null));
  $('open-dossier').addEventListener('click',()=>go('dossier'));
  $('close-dossier').addEventListener('click',()=>{returnFocus='evidence-trigger';go('comparison');});
  $('back-results').addEventListener('click',()=>{comparisonOpen=false;returnFocus='results';go('explorer');syncSelection(false);});
  $('comparison-content').addEventListener('change',event=>{
    if(event.target.id!=='terrain-context')return;
    comparisonContextKey=event.target.value; renderComparison(); $('terrain-context').focus({preventScroll:true});
  });
  $('comparison-content').addEventListener('click',event=>{
    const button=event.target.closest('[data-comparison-cell]');if(!button)return;
    api().setLens(button.dataset.comparisonLens);api().select(button.dataset.comparisonCell,true);
  });
  $('comparison-content').addEventListener('error',event=>{
    if(event.target.tagName!=='IMG')return;
    const frame=event.target.closest('.terrain-image');if(!frame)return;
    event.target.hidden=true;frame.querySelector('.image-unavailable').hidden=false;
  },true);
  document.querySelector('[data-terrain-example]')?.addEventListener('click',()=>{
    const site=current?.features.find(f=>f.properties.id==='site:E10K_453_921');if(!site)return;
    api().setLens('SITES');api().select(site.properties.id,false);
  });
  const dialog = $('limits-dialog');
  document.querySelectorAll('[data-limits]').forEach(b=>b.addEventListener('click',()=>dialog.showModal()));
  $('close-limits').addEventListener('click',()=>dialog.close());
  dialog.addEventListener('click',event=>{if(event.target===dialog){const r=dialog.getBoundingClientRect();if(event.clientX<r.left||event.clientX>r.right||event.clientY<r.top||event.clientY>r.bottom)dialog.close();}});
  document.querySelectorAll('.mission-photo,.planet-choice img').forEach(img=>img.addEventListener('error',()=>{img.hidden=true;}));
  window.addEventListener('resize',()=>api()?.resize());
  window.addEventListener('popstate',()=>{
    const lens=new URLSearchParams(location.search).get('lens');if(current?.status==='ready'&&validLens(lens)&&lens!==current.lens)api().setLens(lens);
  });
  showView(route());
  initialViewShown = true;
  if(api())update('initial');
})();
