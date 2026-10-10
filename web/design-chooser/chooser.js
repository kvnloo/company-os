'use strict';
// Presentation only. The critical-path backend remains the only data authority.
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
const state = {snapshot:null, selected:{kind:'group',id:'network'},
  layout:Object.hasOwn(DESIGNS,query.get('design')) ? query.get('design') : choice?.design || 'spatial',
  theme:['dark','light'].includes(query.get('theme')) ? query.get('theme') : stored(STORE.theme) === 'light' ? 'light' : 'dark',
  choice, choiceStored:!!choice, error:false, pending:false, paused:false};
function controls() {
  document.documentElement.dataset.hudTheme = state.theme;
  $('#theme-controls').innerHTML = `<div class="hud-theme-switch" role="group" aria-label="Color theme">${['dark','light'].map(theme => `<button data-theme="${theme}" aria-pressed="${theme === state.theme}">${theme[0].toUpperCase()+theme.slice(1)}</button>`).join('<span aria-hidden="true">/</span>')}</div>`;
  $('#design-tabs').innerHTML = `<div role="tablist" aria-label="Pane design">${Object.entries(DESIGNS).map(([key,d]) => `<button role="tab" id="tab-${key}" aria-label="${d.title}" aria-selected="${key === state.layout}" aria-controls="workspace" tabindex="${key === state.layout ? 0 : -1}" data-design="${key}"><span class="tab-number">${d.number}</span>${d.title}${state.choice?.design === key ? '<span class="choice-mark" aria-label="chosen">◉</span>' : ''}</button>`).join('')}</div>`;
  $('#choice-controls').innerHTML = `<button class="primary-button" id="choose" aria-pressed="${state.choice?.design === state.layout}">Choose this design</button><button class="text-button" id="download" ${state.choice ? '' : 'disabled'}>Download choice</button>`;
  $('#choice-state').textContent = state.choice ? `${state.choiceStored ? 'Saved locally' : 'Session only (storage unavailable)'}: ${DESIGNS[state.choice.design].title} / ${state.choice.theme}. Production unchanged.` : 'Preview only. No production layout changes.';
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
  $('#compare').textContent=open ? 'Back to live design' : 'Compare images';
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
    $('#gallery').innerHTML=`<div class="gallery-heading"><p class="hud-label">Browser-rendered comparisons</p><h2>Same evidence. Different attention.</h2><p>Captured views, not current telemetry. Open an image to return to its live read-only design. Previewing does not choose it.</p></div><div class="gallery-grid">${images.map(image=>`<article class="gallery-image hud-brackets"><button data-gallery-design="${image.layout}" data-gallery-theme="${image.theme}" aria-label="Open ${DESIGNS[image.layout].title} / ${image.theme} live design"><img src="/design-chooser/gallery/${image.file}" alt="Actual browser capture of ${DESIGNS[image.layout].title} in ${image.theme} theme" width="1536" height="1800"><span class="gallery-caption"><strong>${DESIGNS[image.layout].title}</strong><span>${image.theme} / Open live ↗</span></span></button><p class="capture-time">Captured ${esc(stamp(image.captured_at))} <a href="/design-chooser/gallery/${image.file}" target="_blank" rel="noreferrer">Full PNG ↗</a></p></article>`).join('')}</div>${images.length ? '' : '<p class="empty">No captured images are available yet. The live designs are still usable.</p>'}`;
  } catch (_) {$('#gallery').innerHTML='<p class="loading">Captured images could not be retrieved. Use the design tabs to compare live views.</p>';}
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
const GROUPS = {network:'Network',services:'Services',providers:'Providers',k8s:'Kubernetes',pods:'Pods',nodes:'Nodes',processes:'Processes',sources:'Sources',capacity:'Capacity',gaps:'Gaps'};
const ROOT_GROUPS = ['services','providers','k8s','processes','sources','capacity','gaps'];
const GROUP_SOURCE = {services:'z0_health',providers:'z0_providers',k8s:'k8s',pods:'k8s',nodes:'k8s',processes:'processes',capacity:'z0_capacity'};
function capacityRows() {
  // `capacity` is the backend's legacy provider alias, not host capacity.
  return ['hosts','sessions','offers','leases'].flatMap(collection=>(state.snapshot.capacity_plane?.[collection] || []).map((row,index)=>{
    const ref=row[{hosts:'host_id',sessions:'session_id',offers:'offer_id',leases:'placement_id'}[collection]];
    return {id:`${collection}:${ref ?? index}`,title:`${collection} / ${ref ?? 'unknown reference'}`,row};
  }));
}
function childrenOf(group) {
  const s=state.snapshot;
  const child=(kind,id,title,caption='')=>({kind,id:String(id),title,caption});
  if(group==='network') return ROOT_GROUPS.map(id=>child('group',id,GROUPS[id],groupSummary(id)));
  if(group==='services') return [child('source','z0_health','Service health',shown(s.z0_service?.health?.ok)),child('source','z0_readiness','Dispatch readiness',shown(s.z0_service?.readiness?.ok)),child('source','z0_outcomes','Outcome coverage',shown(s.sources?.z0_outcomes?.status)),child('metrics','service metrics','Service metrics','counters, not economics'),child('runtime','runtime fields','Runtime fields','readiness, host metadata, capacity, revisions')];
  if(group==='providers')return (s.z0_service?.providers || []).map(p=>child('provider',p.provider,p.provider,`${human(p.reason)} / inflight ${shown(p.inflight)} / cap ${shown(p.cap)}`));
  if(group==='k8s')return [child('group','pods','Pods',`${(s.k8s?.pods || []).length} observed rows`),child('group','nodes','Nodes',`${(s.k8s?.nodes || []).length} observed rows`)];
  if(group==='pods')return (s.k8s?.pods || []).map(p=>child('pod',p.name,p.name,`${shown(p.phase)} / workload ready ${shown(p.workload_ready)}`));
  if(group==='nodes')return (s.k8s?.nodes || []).map(n=>child('node',n.name,n.name,`Ready ${shown(n.ready)}`));
  if(group==='processes')return (s.fleet || []).map(p=>child('process',p.pid,`${p.name} / ${p.pid}`,'observed process, governed unknown'));
  if(group==='sources')return Object.entries(s.sources || {}).map(([id,v])=>child('source',id,id,`${v.status} / ${freshness(v)}`));
  if(group==='capacity')return capacityRows().map(c=>child('capacity',c.id,c.title,'unqualified source projection'));
  if(group==='gaps')return (s.coverage?.gaps || []).map(g=>child('gap',g,human(g),'missing / unqualified contract'));
  return [];
}
function groupSummary(id) {
  const s=state.snapshot;
  if(id==='providers')return Array.isArray(s.z0_service?.providers) ? `${s.z0_service.providers.length} observed rows` : `rows unknown / ${shown(source('z0_providers').status)}`;
  if(id==='capacity')return capacityRows().length ? `${capacityRows().length} unqualified rows` : 'not observed / unknown';
  if(id==='k8s')return `${s.k8s?.pods?.length ?? 'unknown'} pods / Ready ${shown(s.k8s?.ready)}`;
  if(id==='processes')return `${s.fleet?.length ?? 'unknown'} present / not governed tasks`;
  if(id==='services')return `health ${shown(s.z0_service?.health?.ok)} / readiness ${shown(s.z0_service?.readiness?.ok)}`;
  return `${childrenOf(id).length} ${id==='gaps' ? 'coverage gaps' : 'source records'}`;
}
function groupStrip() {
  return `<nav class="group-strip" aria-label="Compressed network groups">${ROOT_GROUPS.map(id=>`<button data-kind="group" data-id="${id}" aria-label="Browse ${GROUPS[id]} group"><span class="group-name"><i class="hud-orb" aria-hidden="true"></i>${GROUPS[id]}<span aria-hidden="true">↗</span></span><small>${esc(groupSummary(id))}</small></button>`).join('')}</nav>`;
}
function trailFor(kind,id) {
  const node=(kind,id,title)=>({kind,id,title});
  const root=node('group','network','Network');
  if(kind==='group')return id==='network' ? [root] : [root,...(['pods','nodes'].includes(id) ? [node('group','k8s','Kubernetes')] : []),node(kind,id,GROUPS[id])];
  const parent={provider:'providers',pod:'pods',node:'nodes',process:'processes',source:'sources',gap:'gaps',capacity:'capacity',runtime:'services',metrics:'services'}[kind] || 'sources';
  return [...trailFor('group',parent),node(kind,id,id)];
}
function breadcrumbs(kind,id) {
  const trail=trailFor(kind,id),parent=trail.at(-2);
  return `<nav class="breadcrumbs" aria-label="Inspection breadcrumb">${trail.map((node,index)=>index===trail.length-1 ? `<span aria-current="page">${esc(node.title)}</span>` : `<button data-child-kind="${node.kind}" data-child-id="${esc(node.id)}">${esc(node.title)}</button><span aria-hidden="true">/</span>`).join('')}</nav><button class="text-button" id="inspect-back" ${parent ? `data-child-kind="${parent.kind}" data-child-id="${esc(parent.id)}"` : 'disabled'}>Back one level</button>`;
}
function groupContent(id) {
  const children=childrenOf(id),sourceId=GROUP_SOURCE[id],info=sourceId ? source(sourceId) : null;
  const empty=id==='capacity' ? 'No capacity rows observed. Capacity is unknown, not zero or idle.' : id==='providers' ? 'No provider rows observed. Availability is unknown, not offline.' : 'No child rows observed in this bounded snapshot.';
  return `<p class="detail-note">${id==='network' ? 'Choose a group, then a child. These are source categories, not an authority graph or inferred task hierarchy.' : groupSummary(id)}</p><div class="child-list scroll-region" tabindex="0" aria-label="Observed child rows">${children.map(c=>`<button class="inspect-row" data-child-kind="${c.kind}" data-child-id="${esc(c.id)}" aria-label="Inspect ${c.kind} ${esc(c.title)}"><span><strong>${esc(c.title)}</strong><small>${esc(c.caption)}</small></span><span aria-hidden="true">↗</span></button>`).join('') || `<p class="empty">${empty}</p>`}</div>${info ? `<div class="group-provenance"><p class="hud-label">Source / ${sourceId}</p>${fields({status:info.status,freshness:freshness(info),observed_at:stamp(info.observed_at),coverage:info.coverage,reason:human(info.reason)})}<button class="text-button" data-child-kind="source" data-child-id="${sourceId}">Inspect provenance</button></div>` : fields({coverage:state.snapshot.coverage?.scope,generated_at:stamp(state.snapshot.generated_at)})}`;
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
  return pane('Kubernetes', `<div class="k8s-summary"><span>Workloads Ready ${badge(k.ready)}</span><span>Inventory ${badge(k.available)}</span><span>${esc(k.coverage?.scope || 'unknown')} / truncated ${esc(shown(k.coverage?.truncated))}</span></div><div class="mini-columns"><span>pod reference / phase</span><span>ready / containers · restarts</span></div><div class="k8s-list scroll-region" tabindex="0" aria-label="Kubernetes observed pods">${(k.pods || []).map(p => item('pod',p.name,`<span><strong>${esc(p.name)}</strong><small>${esc(p.phase)} / workload ready ${esc(shown(p.workload_ready))}</small></span><span class="mono">${esc(shown(p.ready))}/${esc(shown(p.containers))} · ${esc(shown(p.restarts))}</span>`, `data-pod="${esc(p.name)}"`)).join('') || '<p class="empty">No pod inventory observed.</p>'}</div>`, esc(source('k8s').status || 'unknown'), 'k8s-pane');
}
function processesPane() {
  const s = state.snapshot;
  return pane('Process presence', `<p class="pane-note">Presence is not governed work. No task, session or heartbeat is inferred.</p><div class="process-list scroll-region" tabindex="0" aria-label="Observed process rows">${(s.fleet || []).map(p => item('process',String(p.pid),`<span>${esc(p.name)}<small>PID ${esc(p.pid)} / ${esc(p.status)}</small></span><span class="mono">${esc(shown(p.governed))}</span>`)).join('') || '<p class="empty">No matched processes in this snapshot.</p>'}</div><p class="pane-note">${esc(s.coverage?.scope || 'unknown')} / limit ${esc(shown(s.coverage?.fleet_limit))} / truncated ${esc(shown(s.coverage?.fleet_truncated))}</p>`, String((s.fleet || []).length), 'process-pane');
}
function sourcesPane() {
  return pane('Source freshness', `<p class="pane-note">State at source check. A successful GET does not imply a fresh upstream observation.</p><div class="source-list">${Object.entries(state.snapshot.sources || {}).map(([key,s]) => item('source', key, `<span><strong>${esc(key)}</strong><small>${esc(s.status)} / ${esc(freshness(s))}</small></span>`, `data-source="${esc(key)}" aria-label="Inspect source ${esc(key)}"`)).join('')}</div>`, 'inspect bytes & time', 'sources-pane');
}
function gapsPane() {
  const s = state.snapshot;
  return pane('Coverage & gaps', `<p class="gap-lead">Verified outcome <strong>unknown</strong></p><p class="pane-note">No qualified outcome delta or joined control/episode contract is supplied.</p><div class="gap-list scroll-region" tabindex="0" aria-label="Coverage gaps">${(s.coverage?.gaps || []).map(g => item('gap',g,`<span>${esc(human(g))}</span>`)).join('')}</div><dl class="economics"><div><dt>Observed cost USD</dt><dd data-economics="observed_cost_usd">${esc(shown(s.economics?.observed_cost_usd))}</dd></div><div><dt>Actual tokens</dt><dd>${esc(shown(s.economics?.actual_tokens))}</dd></div></dl>`, 'not zero', 'gaps-pane');
}
function orbitPane() {
  return `<section class="orbit-pane" aria-label="Source index, not progress"><div class="orbit"><svg viewBox="0 0 420 350" aria-hidden="true"><g fill="none" stroke="currentColor" stroke-linecap="round"><circle cx="210" cy="175" r="151" stroke-dasharray=".1 9" stroke-width="2"/><circle cx="210" cy="175" r="119" stroke-dasharray=".1 10"/><circle cx="210" cy="175" r="87" stroke-dasharray=".1 9"/><path d="M210 24V65M59 175H90M330 175H362M210 285V326" class="orbit-connectors"/></g><circle cx="210" cy="175" r="24" class="hud-core"/></svg><button class="orbit-label orbit-top" data-kind="group" data-id="services">Services <small>${esc(source('z0_health').status)}</small></button><button class="orbit-label orbit-left" data-kind="group" data-id="providers">Providers <small>${esc(source('z0_providers').status)}</small></button><button class="orbit-label orbit-right" data-kind="group" data-id="k8s">Kubernetes <small>${esc(source('k8s').status)}</small></button><button class="orbit-label orbit-bottom" data-kind="group" data-id="gaps">Gaps <small>${esc(shown(state.snapshot.coverage?.gaps?.length))} observed</small></button><button class="orbit-core" data-kind="group" data-id="network" aria-label="Inspect network groups"></button></div><p class="orbit-caption">SOURCE INDEX</p><p class="pane-note">Orientation, not topology or percent complete.</p></section>`;
}
function inspector() {
  return `<aside class="pane inspector hud-brackets" aria-label="Evidence inspector"><div class="pane-heading"><h3>Inspect evidence</h3><span class="hud-label">read only</span></div><div id="inspect-navigation"></div><p class="inspect-category" id="inspect-category"></p><h4 id="inspect-title" tabindex="-1"></h4><div id="inspect-body"></div><button id="return-row" class="text-button">Return to selected row</button></aside>`;
}
function detail() {
  if (!state.snapshot || !$('#inspect-body')) return;
  const s = state.snapshot, {kind,id} = state.selected;
  $('#return-row').disabled=!document.querySelector(`[data-kind="${CSS.escape(kind)}"][data-id="${CSS.escape(id)}"]`);
  $('#inspect-navigation').innerHTML=breadcrumbs(kind,id);
  if(kind==='group') {
    $('#inspect-title').textContent=GROUPS[id];$('#inspect-category').textContent='network group / observed children';
    $('#inspect-body').innerHTML=groupContent(id);
    document.querySelectorAll('[data-kind]').forEach(el=>el.setAttribute('aria-pressed',String(el.dataset.kind===kind && el.dataset.id===id)));
    return;
  }
  let data, origin, note;
  if (kind === 'source') {
    data = s.sources?.[id]; origin = id;
    note = 'Check time is not observation time. Source-content hash is not a deployed producer revision.';
  } else if (kind === 'provider') {
    data = s.z0_service?.providers?.find(p => p.provider === id); origin = 'z0_providers';
    note = 'Availability is source-reported. Empty quota and unknown model do not prove usable quota or model behavior.';
  } else if (kind === 'pod') {
    data = s.k8s?.pods?.find(p => p.name === id); origin = 'k8s';
    note = 'Opaque pod reference. Ready conditions, not inventory count, describe workload readiness.';
  } else if (kind === 'process') {
    data = s.fleet?.find(p => String(p.pid) === id); origin = 'processes';
    note = 'Process presence only. Age is process age, not task age. A missing heartbeat is unknown, not alive or dead.';
  } else if (kind === 'node') {
    data=s.k8s?.nodes?.find(n=>n.name===id);origin='k8s';note='Node Ready is source-reported, not application readiness or deployment qualification.';
  } else if (kind === 'capacity') {
    data=capacityRows().find(row=>row.id===id)?.row;origin='z0_capacity';note='Optional capacity remains an unqualified source projection, not schedulable authority.';
  } else if (kind === 'metrics') {
    data = s.z0_service?.metrics; origin = 'z0_metrics';
    note = 'Observed service metrics, not economics. No cost, savings, quality or progress is inferred from counters.';
  } else if (kind === 'runtime') {
    data = {health:s.z0_service?.health,readiness:s.z0_service?.readiness,outcome_coverage:s.z0_service?.outcome_coverage,disks:s.disks,security:s.security,k8s_nodes:s.k8s?.nodes,capacity_plane:s.capacity_plane,implementation:s.implementation}; origin = 'snapshot';
    note = 'Read-only source fields. False and measured zero are preserved. Unknown remains unknown. Disk and permission data are metadata only.';
  } else {
    data = {gap:id,scope:s.coverage?.scope,next_action:s.coverage?.next_action,control:s.control}; origin = 'coverage';
    note = 'Missing evidence is not a request for authorization. CompanyOS cannot repair or qualify this contract.';
  }
  $('#inspect-title').textContent = id;
  $('#inspect-category').textContent = `${kind} / ${origin}`;
  const content = kind === 'metrics' && Array.isArray(data) ? `<div class="metric-list scroll-region" tabindex="0" aria-label="Service metrics">${data.map(row => `<div><strong>${esc(row.metric)}</strong><span>${esc(shown(row.value))}</span><small>provider ${esc(shown(row.provider))} / HTTP ${esc(shown(row.http_status))}</small></div>`).join('')}</div>` : data ? fields(kind === 'source' ? {status:data.status,freshness:freshness(data),checked_at:stamp(data.checked_at),observed_at:stamp(data.observed_at),producer_revision:data.producer_revision,source_version:data.source_version,coverage:data.coverage,reason:data.reason} : data) : '<p>This row is no longer in the latest snapshot.</p>';
  $('#inspect-body').innerHTML = `<p class="detail-note">${esc(note)}</p>${content}<details class="raw"><summary id="raw-summary">Exact snapshot fields</summary><pre>${esc(JSON.stringify(data ?? null,null,2))}</pre></details>`;
  if(kind !== 'source' && s.sources?.[origin]) {
    const info=s.sources[origin];
    $('#inspect-body').insertAdjacentHTML('beforeend',`<details class="provenance"><summary id="provenance-summary">Source provenance / ${esc(origin)}</summary>${fields({status:info.status,freshness:freshness(info),observed_at:stamp(info.observed_at),checked_at:stamp(info.checked_at),coverage:info.coverage,source_version:info.source_version})}<button class="text-button" data-child-kind="source" data-child-id="${esc(origin)}">Inspect full source</button></details>`);
  }
  document.querySelectorAll('[data-kind]').forEach(el => el.setAttribute('aria-pressed', String(el.dataset.kind === kind && el.dataset.id === id)));
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
  const focused = focus?.kind ? {kind:focus.kind,id:focus.id,prefix:'data-'} : focus?.childKind ? {kind:focus.childKind,id:focus.childId,prefix:'data-child-'} : null;
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
  if(focused)document.querySelector(`[${focused.prefix}kind="${CSS.escape(focused.kind)}"][${focused.prefix}id="${CSS.escape(focused.id)}"]`)?.focus({preventScroll:true});
  else if(focusId && $('#workspace').querySelector(`#${CSS.escape(focusId)}`)) document.getElementById(focusId).focus({preventScroll:true});
  transport();
}
$('#workspace').addEventListener('click', event => {
  if(event.target.id === 'return-row') { const row=document.querySelector(`[data-kind="${CSS.escape(state.selected.kind)}"][data-id="${CSS.escape(state.selected.id)}"]`);if(row){const section=row.closest('details');if(section)section.open=true;row.focus();} return; }
  const child=event.target.closest('[data-child-kind]');
  if(child){state.selected={kind:child.dataset.childKind,id:child.dataset.childId};detail();$('#inspect-title').focus({preventScroll:true});return;}
  const sectionControl = event.target.closest('[data-sections]');
  if (sectionControl) { document.querySelectorAll('.desk-section').forEach(section => { section.open = sectionControl.dataset.sections === 'expand'; }); return; }
  const button = event.target.closest('[data-kind]');
  if (!button) return;
  state.selected = {kind:button.dataset.kind,id:button.dataset.id};
  detail();
  $('#inspect-title').focus({preventScroll:true});
  $('.inspector').scrollIntoView({block:'nearest'});
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
    state.snapshot = data;state.error=false;
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
