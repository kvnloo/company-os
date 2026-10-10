import {buildInspectionModel} from './inspection-model.mjs';
// Presentation only. The integrated production consumer is the only data authority.
const API = '/api/plugins/company-os/snapshot';
const $ = (selector) => document.querySelector(selector);
const esc = (value) => String(value).replace(/[&<>"']/g, ch => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[ch]));
const shown = (value) => value === null || value === undefined ? 'unknown' : typeof value === 'object' ? JSON.stringify(value) : String(value);
const stamp = (value) => typeof value === 'number' && Number.isFinite(value) ? new Date(value * 1000).toISOString().replace('T', ' ').replace(/\.\d+Z$/, ' UTC') : 'unknown';
const human = (value) => shown(value).replaceAll('_', ' ');
const DESIGNS = {
  spatial: {title:'Spatial cockpit', description:'Orient around sources. Inspect without losing the map.', number:'01'},
  balanced: {title:'Operations split', description:'Compare services and workloads side by side. Evidence stays in reach.', number:'02'},
  dense: {title:'Instrument desk', description:'A source ledger and expandable instruments. More rows, the same boundaries.', number:'03'},
};
const STORE = {choice:'companyos.chooser.choice.v1',theme:'companyos.chooser.theme'};
function stored(key) { try { return localStorage.getItem(key); } catch (_) { return null; } }
function persist(key, value) { try { localStorage.setItem(key,value); return true; } catch (_) { return false; } }
function savedChoice() {
  try { const value = JSON.parse(stored(STORE.choice)); return value?.scope === 'local-design-preference' && Object.hasOwn(DESIGNS,value.design) && ['dark','light'].includes(value.theme) ? value : null; } catch (_) { return null; }
}
const query = new URLSearchParams(location.search), choice = savedChoice();
const state = {snapshot:null, model:null, selected:'network', retained:null, pages:{}, collapsed:{},
  layout:Object.hasOwn(DESIGNS,query.get('design')) ? query.get('design') : choice?.design || 'spatial',
  theme:['dark','light'].includes(query.get('theme')) ? query.get('theme') : stored(STORE.theme) === 'light' ? 'light' : 'dark',
  choice, choiceStored:!!choice, error:false, pending:false, paused:false};
function controls() {
  document.documentElement.dataset.hudTheme = state.theme;
  $('#theme-controls').innerHTML = `<div class="hud-theme-switch" role="group" aria-label="Color theme">${['dark','light'].map(theme => `<button data-theme="${theme}" aria-pressed="${theme === state.theme}">${theme[0].toUpperCase()+theme.slice(1)}</button>`).join('<span aria-hidden="true">/</span>')}</div>`;
  $('#design-tabs').innerHTML = `<div role="tablist" aria-label="Dashboard views">${Object.entries(DESIGNS).map(([key,d]) => `<button role="tab" id="tab-${key}" aria-label="${d.title}" aria-selected="${key === state.layout}" aria-controls="workspace" tabindex="${key === state.layout ? 0 : -1}" data-design="${key}"><span class="tab-number">${d.number}</span>${d.title}${state.choice?.design === key ? '<span class="choice-mark" aria-label="default view">◉</span>' : ''}</button>`).join('')}</div>`;
  $('#choice-controls').innerHTML = `<button class="primary-button" id="choose" aria-pressed="${state.choice?.design === state.layout}">Save as default view</button><button class="text-button" id="download" ${state.choice ? '' : 'disabled'}>Download preference</button>`;
  $('#choice-state').textContent = state.choice ? `${state.choiceStored ? 'Saved locally' : 'Session only (storage unavailable)'}: ${DESIGNS[state.choice.design].title} / ${state.choice.theme}. All three views remain available. Production unchanged.` : 'All three views available. No default saved; production unchanged.';
  $('#layout-title').textContent = DESIGNS[state.layout].title;
  $('#layout-description').textContent = DESIGNS[state.layout].description;
  $('#workspace').setAttribute('role','tabpanel');
  $('#workspace').setAttribute('aria-labelledby',`tab-${state.layout}`);
  $('#workspace').dataset.layout = state.layout;
}
function switchDesign(key) { state.layout=key; showGallery(false); controls(); render(); }
$('#design-tabs').addEventListener('click', e => { const b=e.target.closest('[data-design]'); if(b) switchDesign(b.dataset.design); });
$('#design-tabs').addEventListener('keydown', e => {
  const keys=Object.keys(DESIGNS), index=keys.indexOf(e.target.closest('[data-design]')?.dataset.design || state.layout);
  const target={ArrowRight:keys[(index+1)%keys.length],ArrowLeft:keys[(index+keys.length-1)%keys.length],Home:keys[0],End:keys.at(-1)}[e.key];
  if(target) {e.preventDefault();switchDesign(target);$(`#tab-${target}`).focus();}
});
$('#theme-controls').addEventListener('click', e => {
  const b=e.target.closest('[data-theme]'); if(!b) return;
  state.theme=b.dataset.theme;persist(STORE.theme,state.theme);controls();$(`[data-theme="${state.theme}"]`).focus();
});
$('#choice-controls').addEventListener('click', e => {
  if(e.target.id === 'choose') {
    state.choice={schema:'companyos.design-choice.v1',scope:'local-design-preference',design:state.layout,theme:state.theme,chosen_at:new Date().toISOString(),production_changed:false,style_base:'7da554116d096cdfc7a7fb77658da5eca80bd6e4',reference:'https://github.com/kvnloo/company-os/issues/5'};
    state.choiceStored=persist(STORE.choice,JSON.stringify(state.choice));controls();$('#choose').focus();
  } else if(e.target.id === 'download' && state.choice) {
    const url=URL.createObjectURL(new Blob([JSON.stringify(state.choice,null,2)+'\n'],{type:'application/json'}));
    const link=document.createElement('a');link.href=url;link.download='companyos-design-choice.json';link.click();setTimeout(()=>URL.revokeObjectURL(url),1000);
  }
});
controls();
function showGallery(open) {
  $('#gallery').hidden=!open;$('#workspace').hidden=open;$('.projection-heading').hidden=open;
  $('#compare').textContent=open ? 'Back to live view' : 'Compare images';
  $('#compare').setAttribute('aria-expanded',String(open));
}
$('#compare').addEventListener('click',async () => {
  const open=$('#gallery').hidden;showGallery(open);
  if(!open)return;
  if($('#gallery img'))return;
  $('#gallery').innerHTML='<p class="loading">Retrieving captured views.</p>';
  try {
    const response=await fetch('/design-chooser/gallery.json',{cache:'no-store',credentials:'omit'});
    if(!response.ok)throw new Error('gallery unavailable');
    const data=await response.json();
    const images=data.images.filter(image=>Object.hasOwn(DESIGNS,image.layout) && ['dark','light'].includes(image.theme) && image.file===`${image.layout}-${image.theme}.png`);
    $('#gallery').innerHTML=`<div class="gallery-heading"><p class="hud-label">Browser-rendered comparisons</p><h2>Same evidence. Different attention.</h2><p>Captured views, not current telemetry. Open an image to return to its live read-only view. Previewing does not change your default.</p></div><div class="gallery-grid">${images.map(image=>`<article class="gallery-image hud-brackets"><button data-gallery-design="${image.layout}" data-gallery-theme="${image.theme}" aria-label="Open ${DESIGNS[image.layout].title} / ${image.theme} live view"><img src="/design-chooser/gallery/${image.file}" alt="Actual browser capture of ${DESIGNS[image.layout].title} in ${image.theme} theme" width="1536" height="1800"><span class="gallery-caption"><strong>${DESIGNS[image.layout].title}</strong><span>${image.theme} / Open live ↗</span></span></button><p class="capture-time">Captured ${esc(stamp(image.captured_at))} <a href="/design-chooser/gallery/${image.file}" target="_blank" rel="noreferrer">Full PNG ↗</a></p></article>`).join('')}</div>${images.length ? '' : '<p class="empty">No captured images are available yet. The live views are still usable.</p>'}`;
  } catch (_) {$('#gallery').innerHTML='<p class="loading">Captured images could not be retrieved. Use the view tabs to compare live views.</p>';}
});
$('#gallery').addEventListener('click',e=>{
  const button=e.target.closest('[data-gallery-design]');if(!button)return;
  state.theme=button.dataset.galleryTheme;persist(STORE.theme,state.theme);switchDesign(button.dataset.galleryDesign);
  $('#workspace').focus({preventScroll:true});window.scrollTo(0,0);
});
const source = (key) => state.snapshot?.sources?.[key] || {};
const freshness = (s) => `${state.error || state.paused ? 'last known / ' : ''}${shown(s.freshness)}`;
const badge = (value) => `<span class="state-badge">${esc(shown(value))}</span>`;
const item = (kind, id, text, attrs='') => `<button type="button" class="inspect-row" data-kind="${kind}" data-id="${esc(id)}" ${attrs}>${text}<span class="row-arrow" aria-hidden="true">↗</span></button>`;
const fields = (values) => `<dl class="field-list">${Object.entries(values).map(([key,value]) => `<div><dt>${esc(human(key))}</dt><dd>${esc(shown(value))}</dd></div>`).join('')}</dl>`;
const PAGE_SIZE = 8;
function nodeKey(kind,id) {
  if(kind==='group') return ({providers:'capacity',k8s:'resources',nodes:'kube-nodes',processes:'agents',gaps:'sources'})[id] || id;
  if(kind==='metrics') return 'service:metrics';
  if(kind==='runtime') return 'resources';
  if(kind==='gap') return 'sources';
  if(kind==='pod') return 'pod:'+id;
  if(kind==='node') return 'kube-node:'+id;
  return kind+':'+id;
}
function groupStrip() {
  return `<nav class="group-strip" aria-label="Compressed network groups">${state.model.nodes.network.children.map(id=>{
    const n=state.model.nodes[id];
    return `<button data-kind="group" data-id="${id}" aria-label="Browse ${esc(n.label)} group"><span class="group-name"><i class="hud-orb" aria-hidden="true"></i>${esc(n.label)}<span aria-hidden="true">↗</span></span><small>${esc(n.summary)}</small></button>`;
  }).join('')}</nav>`;
}
function trailFor(id,model=state.model) {
  const trail=[],seen=new Set();
  while(id && model.nodes[id] && !seen.has(id)) {seen.add(id);const n=model.nodes[id];trail.unshift({id:n.id,label:n.label});id=n.parent;}
  return trail;
}
function selectedDetail() {
  const n=state.model.nodes[state.selected];
  const last=state.retained?.node.id===state.selected ? state.retained : null;
  const unavailable=n && !n.id.startsWith('source:') && n.sources.length && n.sources.every(key=>source(key).status==='unavailable');
  const retained=last && (!n || unavailable && last.observed);
  if(retained) return {...last,stale:true,reason:!n ? 'Selected row absent from the latest projection. Disappearance is not completion.' : 'Selected source unavailable. Latest successful detail and provenance retained.'};
  if(!n) return null;
  const value={node:n,trail:trailFor(n.id),sources:Object.fromEntries(n.sources.map(key=>[key,source(key)])),generated_at:state.snapshot.generated_at,observed:!unavailable};
  if(!state.error)state.retained=value;
  return {...value,stale:state.error || state.paused,reason:state.error ? 'Source retrieval failed. Latest successful detail retained.' : 'Updates paused; last-known detail.'};
}
function breadcrumbs(trail) {
  const parent=trail.at(-2);
  return `<nav class="breadcrumbs" aria-label="Inspection breadcrumb">${trail.map((n,i)=>i===trail.length-1 ? `<span aria-current="page">${esc(n.label)}</span>` : `<button data-child-id="${esc(n.id)}">${esc(n.label)}</button><span aria-hidden="true">/</span>`).join('')}</nav><button class="text-button" id="inspect-back" ${parent ? `data-child-id="${esc(parent.id)}"` : 'disabled'}>Back one level</button>`;
}
function childContent(n) {
  const children=n.children.filter(id=>state.model.nodes[id]);
  if(!children.length)return '<p class="empty">No projected child rows. Unobserved inventory remains unknown, not zero or idle; this is not a global count or proof of no work. Consult source coverage.</p>';
  const page=Math.min(state.pages[n.id] || 0,Math.ceil(children.length/PAGE_SIZE)-1);state.pages[n.id]=page;
  const start=page*PAGE_SIZE,closed=!!state.collapsed[n.id];
  return `<button class="text-button" id="toggle-children" aria-expanded="${!closed}">${closed?'Expand':'Collapse'} children</button><div ${closed?'hidden':''}><div class="child-list scroll-region" tabindex="0" aria-label="Observed child rows">${children.slice(start,start+PAGE_SIZE).map(id=>{
    const child=state.model.nodes[id];return `<button class="inspect-row" data-child-id="${esc(id)}" aria-label="Inspect ${esc(child.label)}"><span><strong>${esc(child.label)}</strong><small>${esc(child.summary)}</small></span><span aria-hidden="true">↗</span></button>`;
  }).join('')}</div><div class="child-pager"><button class="text-button" id="children-prev" ${page===0?'disabled':''} aria-label="Previous children">← Previous</button><span id="child-page">${start+1}–${Math.min(start+PAGE_SIZE,children.length)} of ${children.length} projected children</span><button class="text-button" id="children-next" ${start+PAGE_SIZE>=children.length?'disabled':''} aria-label="Next children">Next →</button></div></div>`;
}
const pane = (title, body, label='', classes='') => `<section class="pane hud-brackets ${classes}"><div class="pane-heading"><h3>${title}</h3><span class="hud-label">${label}</span></div>${body}</section>`;
function servicePane() {
  const s = state.snapshot;
  return pane('Services', [
    ['z0_health','Service process',s.z0_service?.health?.ok],
    ['z0_readiness','Dispatch readiness',s.z0_service?.readiness?.ok],
    ['host_metadata','Permission metadata',s.security?.status],
    ['z0_outcomes','Outcome eligible',s.z0_service?.outcome_coverage?.promotion_gate?.eligible],
  ].map(([key,name,value]) => item('source',key,`<span>${name}</span>${badge(value)}`)).join('') + '<p class="pane-note">Readiness is not model or deployment acceptance.</p>' + item('metrics','service metrics','<span>Inspect service metrics</span>') + item('runtime','runtime fields','<span>Inspect runtime fields</span>'), 'observed');
}
function providerPane() {
  const rows = state.snapshot.z0_service?.providers;
  return pane('Providers', `<p class="pane-note">Availability reported by the source, not independent model qualification.</p><div class="mini-columns"><span>provider</span><span>inflight / cap</span></div><div class="provider-list scroll-region" tabindex="0" aria-label="Provider rows">${Array.isArray(rows) && rows.length ? rows.map(p => item('provider',p.provider,`<span><strong>${esc(p.provider)}</strong><small>${esc(human(p.reason))}</small></span><span class="mono">${esc(shown(p.inflight))} / ${esc(shown(p.cap))}</span>`, `data-provider="${esc(p.provider)}"`)).join('') : `<p class="empty">No provider rows observed. ${esc(human(source('z0_providers').reason))}.</p>`}</div>`, esc(source('z0_providers').status || 'unknown'));
}
function k8sPane() {
  const k = state.snapshot.k8s || {};
  return pane('Kubernetes', `<div class="k8s-summary"><span>Workloads Ready ${badge(k.ready)}</span><span>Inventory ${badge(k.available)}</span><span>${esc(k.coverage?.scope || 'unknown')} / truncated ${esc(shown(k.coverage?.truncated))}</span></div><div class="mini-columns"><span>pod reference / phase</span><span>ready / containers · restarts</span></div><div class="k8s-list scroll-region" tabindex="0" aria-label="Kubernetes observed pods">${(k.pods || []).map(p => item('pod',`${p.namespace}:${p.name}`,`<span><strong>${esc(p.name)}</strong><small>${esc(p.phase)} / workload ready ${esc(shown(p.workload_ready))}</small></span><span class="mono">${esc(shown(p.ready))}/${esc(shown(p.containers))} · ${esc(shown(p.restarts))}</span>`, `data-pod="${esc(p.name)}"`)).join('') || '<p class="empty">No pod inventory observed.</p>'}</div>`, esc(source('k8s').status || 'unknown'), 'k8s-pane');
}
function processesPane() {
  const s = state.snapshot;
  return pane('Process presence', `<p class="pane-note">Presence is not governed work. No task, session or heartbeat is inferred.</p><div class="process-list scroll-region" tabindex="0" aria-label="Observed process rows">${(s.fleet || []).map(p => item('process',String(p.pid),`<span>${esc(p.name)}<small>PID ${esc(p.pid)} / ${esc(p.status)}</small></span><span class="mono">${esc(shown(p.governed))}</span>`)).join('') || '<p class="empty">No matched processes in this snapshot.</p>'}</div><p class="pane-note">${esc(s.coverage?.scope || 'unknown')} / limit ${esc(shown(s.coverage?.fleet_limit))} / truncated ${esc(shown(s.coverage?.fleet_truncated))}</p>`, source('processes').status==='ok' ? String((s.fleet || []).length) : 'unknown', 'process-pane');
}
function sourcesPane() {
  return pane('Source freshness', `<p class="pane-note">State at source check. A successful GET does not imply a fresh upstream observation.</p><div class="source-list">${Object.entries(state.snapshot.sources || {}).map(([key,s]) => item('source', key, `<span><strong>${esc(key)}</strong><small>${esc(s.status)} / ${esc(freshness(s))}</small></span>`, `data-source="${esc(key)}" aria-label="Inspect source ${esc(key)}"`)).join('')}</div>`, 'inspect bytes & time', 'sources-pane');
}
function gapsPane() {
  const s = state.snapshot;
  return pane('Coverage & gaps', `<p class="gap-lead">Verified outcome <strong>unknown</strong></p><p class="pane-note">No qualified outcome delta or joined control/episode contract is supplied.</p><div class="gap-list scroll-region" tabindex="0" aria-label="Coverage gaps">${(s.coverage?.gaps || []).map(g => item('gap',g,`<span>${esc(human(g))}</span>`)).join('')}</div><dl class="economics"><div><dt>Observed cost USD</dt><dd data-economics="observed_cost_usd">${esc(shown(s.economics?.observed_cost_usd))}</dd></div><div><dt>Actual tokens</dt><dd>${esc(shown(s.economics?.actual_tokens))}</dd></div></dl>`, 'not zero', 'gaps-pane');
}
function orbitPane() {
  return `<section class="orbit-pane" aria-label="Source index, not progress"><div class="orbit"><svg viewBox="0 0 420 350" aria-hidden="true"><g fill="none" stroke="currentColor" stroke-linecap="round"><circle cx="210" cy="175" r="151" stroke-dasharray=".1 9" stroke-width="2"/><circle cx="210" cy="175" r="119" stroke-dasharray=".1 10"/><circle cx="210" cy="175" r="87" stroke-dasharray=".1 9"/><path d="M210 24V65M59 175H90M330 175H362M210 285V326" class="orbit-connectors"/></g><circle cx="210" cy="175" r="24" class="hud-core"/></svg><button class="orbit-label orbit-top" data-kind="group" data-id="services">Services <small>${esc(source('z0_health').status)}</small></button><button class="orbit-label orbit-left" data-kind="group" data-id="capacity">Capacity <small>${esc(source('z0_providers').status)}</small></button><button class="orbit-label orbit-right" data-kind="group" data-id="resources">Resources <small>${esc(source('k8s').status)}</small></button><button class="orbit-label orbit-bottom" data-kind="group" data-id="sources">Sources &amp; gaps <small>${esc(shown(state.snapshot.coverage?.gaps?.length))} observed</small></button><button class="orbit-core" data-kind="group" data-id="network" aria-label="Inspect network groups"></button></div><p class="orbit-caption">SOURCE INDEX</p><p class="pane-note">Orientation, not topology or percent complete.</p></section>`;
}
function inspector() {
  return `<aside class="pane inspector hud-brackets" aria-label="Evidence inspector"><div class="pane-heading"><h3>Inspect evidence</h3><span class="hud-label">read only</span></div><div id="inspect-navigation"></div><p class="inspect-category" id="inspect-category"></p><h4 id="inspect-title" tabindex="-1"></h4><div id="inspect-body"></div><button id="return-row" class="text-button">Return to selected row</button></aside>`;
}
function detail() {
  if(!state.model || !$('#inspect-body'))return;
  const d=selectedDetail();if(!d)return;
  const n=d.node;
  $('#inspect-title').textContent=n.label;$('#inspect-title').dataset.nodeId=n.id;
  $('#inspect-category').textContent=`${n.parent ? 'Source-backed inspection' : 'Representative network'} / ${n.sources.join(', ')}`;
  $('#inspect-navigation').innerHTML=breadcrumbs(d.trail);
  $('#inspect-body').innerHTML=`${d.stale ? `<p class="detail-stale" role="status">Stale / last-known. ${esc(d.reason)} Snapshot ${esc(stamp(d.generated_at))}</p>` : ''}<p class="detail-note">${esc(n.meaning)}</p><p class="pane-note">${esc(n.limitation)}</p><p class="pane-note">${esc(n.summary)}</p>${childContent(n)}${fields(n.data)}<details class="raw"><summary id="raw-summary">Exact snapshot fields</summary><pre>${esc(JSON.stringify(n.data,null,2))}</pre></details><details class="provenance"><summary id="provenance-summary">Source provenance / coverage</summary>${Object.entries(d.sources).map(([key,s])=>`<div class="group-provenance"><p class="hud-label">${esc(key)}</p>${fields({status:s.status,freshness:d.stale ? 'last known / '+shown(s.freshness) : freshness(s),checked_at:stamp(s.checked_at),observed_at:stamp(s.observed_at),assessed_at:stamp(s.assessed_at),producer_revision:s.producer_revision,source_version:s.source_version,endpoint:s.endpoint,coverage:s.coverage,reason:s.reason})}${state.model.nodes['source:'+key] ? `<button class="text-button" data-child-id="source:${esc(key)}">Inspect full source ${esc(key)}</button>` : ''}</div>`).join('')}</details>`;
  document.querySelectorAll('[data-kind]').forEach(el=>el.setAttribute('aria-pressed',String(nodeKey(el.dataset.kind,el.dataset.id)===n.id)));
  $('#return-row').disabled=!Array.from(document.querySelectorAll('[data-kind]')).some(el=>nodeKey(el.dataset.kind,el.dataset.id)===n.id);
}
function inspect(id,{backFrom=null}={}) {
  if(!state.model.nodes[id])return;
  state.selected=id;state.retained=null;
  if(backFrom) {
    const index=state.model.nodes[id].children.indexOf(backFrom);
    if(index>=0){state.pages[id]=Math.floor(index/PAGE_SIZE);state.collapsed[id]=false;}
  }
  detail();
  const target=backFrom ? $(`.child-list [data-child-id="${CSS.escape(backFrom)}"]`) : $('.child-list [data-child-id]');
  (target || $('#inspect-title')).focus({preventScroll:true});
}
function sourceMatrix() {
  return pane('Source freshness', `<p class="pane-note">Checked vs observed. Freshness is source-supplied, never inferred from a successful request.</p><div class="source-list matrix"><div class="matrix-head"><span>Source</span><span>Status</span><span>Freshness</span><span>Observed UTC</span></div>${Object.entries(state.snapshot.sources || {}).map(([key,s]) => item('source',key,`<span>${esc(key)}</span><span>${esc(s.status)}</span><span>${esc(freshness(s))}</span><span>${esc(stamp(s.observed_at))}</span>`, `data-source="${esc(key)}" aria-label="Inspect source ${esc(key)}"`)).join('')}</div>`, 'bounded source ledger', 'sources-pane matrix-pane');
}
function deskSection(title, body) {
  return `<details class="desk-section" data-section="${title}" open><summary id="section-${title.replaceAll(' ','-')}">${title}<span class="hud-label">expand / collapse</span></summary>${body}</details>`;
}
function render() {
  if (!state.snapshot) return;
  const focusId=document.activeElement?.id;
  const focus = document.activeElement?.dataset;
  const focused = focus?.kind ? `[data-kind="${CSS.escape(focus.kind)}"][data-id="${CSS.escape(focus.id)}"]` : focus?.childId ? `[data-child-id="${CSS.escape(focus.childId)}"]` : null;
  const openDetails=Array.from(document.querySelectorAll('#inspect-body details')).map(el=>[el.className,el.open]);
  const sections = Array.from(document.querySelectorAll('[data-section]')).map(el => [el.dataset.section,el.open]);
  const scrolls = Array.from(document.querySelectorAll('.scroll-region')).map(el => [el.getAttribute('aria-label'),el.scrollTop]);
  const layouts = {
    spatial: () => `<div class="pane-grid spatial-grid"><div class="service-rail">${servicePane()}${providerPane()}${processesPane()}</div><div class="map-column">${orbitPane()}${sourcesPane()}${k8sPane()}</div><div class="inspect-column">${inspector()}${gapsPane()}</div></div>`,
    balanced: () => `<div class="balanced-grid"><div class="split-operational"><div class="split-title"><span class="hud-dot"></span>Service & supply</div><div class="split-service">${servicePane()}${providerPane()}</div>${sourcesPane()}</div><div class="split-workloads"><div class="split-title"><span class="diamond"></span>Workloads & presence</div>${k8sPane()}${processesPane()}</div><div class="split-evidence">${inspector()}${gapsPane()}</div></div>`,
    dense: () => `<div class="desk-toolbar"><span class="hud-label">Source ledger / expandable instruments</span><div><button class="text-button" data-sections="expand">Expand sections</button><button class="text-button" data-sections="collapse">Collapse sections</button></div></div><div class="dense-grid"><div class="desk-rail">${servicePane()}${gapsPane()}</div><div class="desk-main">${sourceMatrix()}${deskSection('Providers',providerPane())}${deskSection('Kubernetes',k8sPane())}${deskSection('Process presence',processesPane())}</div><div class="desk-inspector">${inspector()}</div></div>`,
  };
  $('#workspace').innerHTML = groupStrip() + layouts[state.layout]();
  $('#workspace').dataset.loaded = 'true';
  $('#snapshot-time').textContent = `Snapshot ${stamp(state.snapshot.generated_at)}`;
  detail();
  openDetails.forEach(([key,open])=>{const el=document.querySelector(`#inspect-body details.${CSS.escape(key)}`);if(el)el.open=open;});
  sections.forEach(([key,open]) => {const el=document.querySelector(`[data-section="${CSS.escape(key)}"]`);if(el)el.open=open;});
  scrolls.forEach(([key,top]) => {const el=document.querySelector(`.scroll-region[aria-label="${CSS.escape(key)}"]`);if(el)el.scrollTop=top;});
  if(focused)(document.querySelector(focused) || $('#inspect-title')).focus({preventScroll:true});
  else if(focusId && $('#workspace').querySelector(`#${CSS.escape(focusId)}`)) document.getElementById(focusId).focus({preventScroll:true});
  transport();
}
$('#workspace').addEventListener('click', event => {
  if(event.target.id==='return-row') {
    const row=Array.from(document.querySelectorAll('[data-kind]')).find(el=>nodeKey(el.dataset.kind,el.dataset.id)===state.selected);
    if(row){const section=row.closest('details');if(section)section.open=true;row.focus();}return;
  }
  const sectionControl=event.target.closest('[data-sections]');
  if(sectionControl){document.querySelectorAll('.desk-section').forEach(s=>{s.open=sectionControl.dataset.sections==='expand';});return;}
  if(event.target.id==='toggle-children'){state.collapsed[state.selected]=!state.collapsed[state.selected];detail();$('#toggle-children').focus();return;}
  if(['children-next','children-prev'].includes(event.target.id)){
    const direction=event.target.id==='children-next'?1:-1;state.pages[state.selected]=(state.pages[state.selected]||0)+direction;detail();
    ($(`#${event.target.id}:not(:disabled)`) || $('.child-list [data-child-id]') || $('#inspect-title')).focus({preventScroll:true});return;
  }
  const child=event.target.closest('[data-child-id]');
  if(child){inspect(child.dataset.childId,{backFrom:event.target.id==='inspect-back'?state.selected:null});return;}
  const button=event.target.closest('[data-kind]');if(!button)return;
  inspect(nodeKey(button.dataset.kind,button.dataset.id));$('.inspector').scrollIntoView({block:'nearest'});
});
$('#workspace').addEventListener('keydown', event=>{
  if(event.key==='ArrowRight') {
    const child=event.target.closest('[data-child-id]'),button=event.target.closest('[data-kind]');
    const id=child?.dataset.childId || (button?nodeKey(button.dataset.kind,button.dataset.id):null);
    if(id){event.preventDefault();inspect(id);}
  } else if(['ArrowLeft','Escape'].includes(event.key)) {
    const parent=selectedDetail()?.trail.at(-2)?.id;
    if(parent){event.preventDefault();inspect(parent,{backFrom:state.selected});}
  }
});
function transport() {
  $('#workspace').dataset.transport = state.error ? 'stale' : state.paused ? 'paused' : 'connected';
  $('#snapshot-status').textContent = state.error ? state.snapshot ? 'Stale / last-known snapshot' : 'Source unavailable / no snapshot observed' : state.paused ? 'Paused / last-known snapshot' : state.snapshot ? `${state.snapshot.status} / source-reported projection` : 'Retrieving source snapshot';
  $('#outage-banner').hidden = !state.error;
  $('#outage-banner').textContent = state.snapshot ? 'Source retrieval failed. All panes show a stale, last-known snapshot. No current availability or freshness is implied. Retry with Refresh snapshot.' : 'No snapshot observed. The source is unavailable; no operational data has been invented. Retry with Refresh snapshot.';
  // Keep these controls mounted so polling cannot discard keyboard focus.
  if(!$('#refresh')) $('#refresh-controls').innerHTML = '<button class="text-button" id="refresh">Refresh snapshot</button><button class="text-button" id="pause">Pause updates</button><span class="poll-label"></span>';
  $('#refresh').disabled=state.pending;
  $('#pause').textContent=state.paused ? 'Resume updates' : 'Pause updates';
  $('#refresh-controls .poll-label').textContent=state.pending ? 'retrieving' : state.paused ? 'manual inspection' : 'every 5s';
}
let timer;
function schedule() { clearTimeout(timer); if(!state.paused) timer=setTimeout(refresh,5000); }
async function refresh() {
  if(state.pending) return;
  state.pending=true;transport();
  try {
    const response = await fetch(API, {cache:'no-store',credentials:'omit',signal:AbortSignal.timeout(20000)});
    if (!response.ok) throw new Error('source unavailable');
    const data = await response.json();
    if (data.schema !== 'company_os.snapshot.v1' || !data.sources || !Number.isFinite(data.generated_at)) throw new Error('unexpected source contract');
    if(Date.now() - data.generated_at*1000 > 30000) throw new Error('expired snapshot');
    state.snapshot = data;state.model=buildInspectionModel(data);state.error=false;
    render();
  } catch (_) {
    state.error=true;
    if(state.snapshot) render();
    else $('#workspace').innerHTML='<div class="loading hud-brackets">No snapshot observed. Services, providers and workloads remain unknown until the existing source responds.</div>';
  } finally {state.pending=false;transport();schedule();}
}
$('#refresh-controls').addEventListener('click', e => {
  if(e.target.id === 'refresh')refresh();
  if(e.target.id === 'pause') {state.paused=!state.paused;clearTimeout(timer);if(state.snapshot)render();transport();if(!state.paused)refresh();}
});
refresh();
