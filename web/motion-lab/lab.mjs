import {LANES,RINGS,CARDS,bindingFor,project,formatValue,createScene,transition,recipe,restoreRecipe,revalidateAnchor} from './model.mjs';
const $=s=>document.querySelector(s);
const $$=s=>Array.from(document.querySelectorAll(s));
const NS='http://www.w3.org/2000/svg';
const STORAGE='companyos.motion-lab.pin.v1';
const configs={
 trace:{tag:'01 · EVIDENCE TRACE',question:'Why should I trust this summary?',title:'Follow one binding, not a network light show.',explain:'A single reveal travels from your selected source ring to its related card and evidence pane. It teaches where the displayed facts came from. The connection is a checked-in source binding, not a witnessed causal chain. All facts and warnings stay available at every phase.',meaning:'Selection → related card → provenance. A reading path, never a runtime or causal event.',steps:['01 / Locate the selected source','02 / Connect its related card','03 / Check the source boundary']},
 focus:{tag:'02 · CONTEXT LENS',question:'What does this source actually explain?',title:'Pull one question forward. Keep the rest in place.',explain:'The selected category expands away from the orbit stack while unrelated tracks recede. The same source ID lights its card, binding row and evidence. This is semantic zoom in presentation only: no new metric, hidden authority or task join is inferred. Restore brings back the original selected object.',meaning:'Ring separation + linked-pane emphasis. Context is retained; data is never enlarged into certainty.',steps:['01 / Keep the cockpit as context','02 / Separate the selected source','03 / Read its scope and limits']},
 compare:{tag:'03 · TIME & HYPOTHESIS',question:'What changed—and what is only a hypothesis?',title:'Hold A. Read B. Refuse to invent the interval.',explain:'Capture a received snapshot in this tab, then refresh B through the same read-only GET. A ghost orbit separates held context from latest received facts. The slider is choreography, not historical time. The optional source-withheld branch only removes evidence; it predicts no output, quality or causal effect.',meaning:'Ghost = held context; solid = latest received. No A exists until you explicitly capture one.',steps:['01 / Hold a source context','02 / Separate A from B','03 / Compare only matched fields']}
};
let scene=createScene(),snapshot=null,anchor=null,transport='loading',receivedAt=null;
let phase=1,playing=false,raf=0,lastTick=0,motionOff=false,outage=false,hypothesis=false,busy=false,pinned=null;
let returnView=null,loadSequence=0;
const reduced=matchMedia('(prefers-reduced-motion: reduce)');
motionOff=reduced.matches;
const el=(tag,className,text)=>{const n=document.createElement(tag);if(className)n.className=className;if(text!==undefined)n.textContent=text;return n;};
const svg=(tag,attrs,parent)=>{const n=document.createElementNS(NS,tag);for(const [key,value]of Object.entries(attrs))n.setAttribute(key,String(value));parent?.append(n);return n;};
const text=(selector,value)=>{const n=$(selector);if(n.textContent!==String(value))n.textContent=String(value);};
const pressed=(node,v)=>node.setAttribute('aria-pressed',String(v));
const notice=value=>text('#notice',value);
const iso=n=>typeof n==='number'&&Number.isFinite(n)?new Date(n*1000).toISOString().replace('.000Z','Z'):'not reported';
const defFor=id=>LANES.find(d=>d.id===id);
const get=()=>bindingFor(snapshot,scene.selected);
try{const raw=localStorage.getItem(STORAGE);if(raw)pinned=restoreRecipe(JSON.parse(raw));}catch{notice('Storage unavailable or invalid saved recipe; using quiet cockpit.');}

// Mount all interactive identities once. Poll/refresh only rebinds their text.
const cx=260,cy=242;
const polar=(r,a)=>[cx+r*Math.sin(a*Math.PI/180),cy-r*Math.cos(a*Math.PI/180)];
const arc=(r,end)=>{const a=polar(r,0),b=polar(r,end);return `M${a[0]},${a[1]} A${r},${r} 0 ${end>180?1:0} 1 ${b[0]},${b[1]}`;};
const ends=[333,324,291,327,248,252,233,327,339,270];
const map=$('#ring-map');
const defs=svg('defs',{},map);
const glow=svg('filter',{id:'orbit-glow',x:'-100%',y:'-100%',width:'300%',height:'300%'},defs);svg('feGaussianBlur',{stdDeviation:3,result:'blur'},glow);const merge=svg('feMerge',{},glow);svg('feMergeNode',{in:'blur'},merge);svg('feMergeNode',{in:'SourceGraphic'},merge);
const gradient=svg('radialGradient',{id:'core-glow'},defs);svg('stop',{offset:0,'stop-color':'#59bd82','stop-opacity':.12},gradient);svg('stop',{offset:1,'stop-color':'#59bd82','stop-opacity':0},gradient);
svg('circle',{cx,cy,r:215,fill:'url(#core-glow)'},map);
const ghost=svg('g',{id:'ghost-orbit','aria-hidden':'true'},map);
const ghostPath=svg('path',{fill:'none',stroke:'#b39de3','stroke-width':2,'stroke-dasharray':'2 5'},ghost);
const orbit=svg('g',{id:'orbits'},map);
const ringNodes=new Map();
RINGS.forEach((def,i)=>{
 const r=75+i*17;
 const group=svg('g',{class:'ring-control','data-source':def.id,role:'button',tabindex:0,'aria-label':`${def.label}: inspect source binding`,'aria-pressed':false},orbit);
 const track=svg('path',{class:'ring-track',d:arc(r,ends[i]),stroke:def.color},group);
 const hit=svg('path',{class:'ring-hit',d:arc(r,ends[i])},group);
 const label=svg('text',{x:cx-7,y:cy-r+3,'text-anchor':'end',class:'ring-label'},group);label.textContent=String(i).padStart(2,'0');
 const marker=svg('circle',{cx:polar(r,ends[i])[0],cy:polar(r,ends[i])[1],r:3.3,fill:'#d2c09d'},group);
 ringNodes.set(def.id,{group,track,hit,label,marker,r,index:i});
 group.addEventListener('click',()=>select(def.id));
 group.addEventListener('keydown',e=>{if(['Enter',' '].includes(e.key)){e.preventDefault();select(def.id);}if(['ArrowDown','ArrowRight','ArrowUp','ArrowLeft'].includes(e.key)){e.preventDefault();const delta=['ArrowDown','ArrowRight'].includes(e.key)?1:-1;ringNodes.get(RINGS[(i+delta+RINGS.length)%RINGS.length].id).group.focus();}});
});
svg('circle',{cx,cy,r:61,fill:'#07160f',stroke:'#2b4c37','stroke-width':.6},map);
const coreTitle=svg('text',{x:cx,y:cy-3,'text-anchor':'middle',class:'ring-core-title'},map);
const coreSub=svg('text',{x:cx,y:cy+17,'text-anchor':'middle',class:'ring-core-sub'},map);
const coreStatus=svg('text',{x:cx,y:cy+33,'text-anchor':'middle',class:'ring-selection'},map);
const modeLabel=svg('text',{x:cx,y:482,'text-anchor':'middle',class:'ring-mode-label'},map);
const focusLeader=svg('path',{fill:'none',stroke:'#a8e2bd','stroke-width':.75,'stroke-dasharray':'2 3'},map);
const focusLabel=svg('text',{x:520,y:65,'text-anchor':'end',class:'ring-selection'},map);
for(const c of CARDS){
 const button=el('button','metric-card');button.dataset.card=c.id;button.dataset.source=c.source;button.setAttribute('aria-label',`Inspect ${c.label}`);pressed(button,false);
 button.append(el('span','label',c.label),el('strong','value','unknown'),el('span','note',c.note));
 button.addEventListener('click',()=>select(button.dataset.source));$('#metric-strip').append(button);
}
for(const [index,d]of LANES.entries()){
 const button=el('button','lane-row');button.dataset.source=d.id;button.setAttribute('aria-label',`Inspect ${d.label}`);pressed(button,false);
 const copy=el('span','lane-copy');copy.append(el('strong','',d.label),el('small','',d.id));
 const state=el('span','lane-status');state.append(el('span','source-state','unknown'),el('small','source-freshness','freshness unknown'));
 button.append(el('span','number',String(index+1).padStart(2,'0')),copy,state);button.addEventListener('click',()=>select(d.id));$('#lanes').append(button);
 const article=el('article');article.dataset.source=d.id;const control=el('button','',d.label);control.addEventListener('click',()=>select(d.id));article.append(control,el('p','static-facts'));$('#static-table').append(article);
}
function apply(command,{animate=true}={}){
 scene=transition(scene,{...command,expectedRevision:scene.revision});
 render();
 if(animate&&!motionOff){phase=0;start();}else setPhase(1);
}
function select(id){apply({type:'SELECT',id});notice(`${defFor(id).label} selected. Related card, binding row and evidence share ${id}.`);}
function captureView(){return {scrollX,scrollY,focus:document.activeElement?.id||null,provenance:$('#provenance').open,phase};}
function enter(){if(!scene.lens){returnView=captureView();apply({type:'ENTER'},{animate:false});notice('Temporary question lens. No data copied to storage; restore keeps the latest allowed source.');}}
function restore(type='RESTORE'){
 const previous=returnView;
 stop();hypothesis=false;$('#hypothesis').checked=false;anchor=null;
 apply({type},{animate:false});returnView=null;
 if(previous){$('#provenance').open=previous.provenance;setPhase(previous.phase);window.scrollTo(previous.scrollX,previous.scrollY);if(previous.focus)document.getElementById(previous.focus)?.focus({preventScroll:true});}
 notice(type==='DISCARD'?'Temporary lens and in-memory comparison discarded.':'Cockpit restored. Selection, disclosure and reading position returned; source data was not rewound.');
}
function render(){
 const def=defFor(scene.selected),binding=get(),config=configs[scene.variant];
 $('#cockpit').className=`cockpit variant-${scene.variant}`;
 $('#cockpit').dataset.selection=scene.selected;
 $('#cockpit').dataset.revision=String(scene.revision);
 text('#question',config.question);text('#proposal-title',config.tag);text('#selected-title',def.label);text('#selection-badge',scene.selected);
 text('#explain-title',config.title);text('#explain-text',config.explain);text('#motion-meaning',config.meaning);
 text('#scene-status',`${scene.lens?'Temporary question lens':'Quiet cockpit'} · revision ${scene.revision}`);
 text('#snapshot-at',snapshot?`Snapshot generated ${iso(snapshot.generated_at)} · manual GET`:'No snapshot received · manual GET only');
 text('#transport',transport==='connected'?'GET connected · '+snapshot.status:transport==='denied'?'Access denied · cleared':transport==='unavailable'?(snapshot?'Last received · NOT current':'Source unavailable'):'Awaiting snapshot');
 $('#transport').dataset.status=transport;
 for(const button of $$('[data-variant]'))pressed(button,button.dataset.variant===scene.variant);
 for(const {group}of ringNodes.values())pressed(group,group.dataset.source===scene.selected);
 for(const c of CARDS){const card=$(`[data-card=${c.id}]`),selected=def.card===c.id,source=bindingFor(snapshot,selected?scene.selected:c.source);const field=selected?source.fields[0]:source.fields.find(f=>f.path===c.path);const value=field?.value??null;const v=card.querySelector('.value');v.textContent=formatValue(value);v.classList.toggle('unknown',value===null);pressed(card,selected);card.dataset.boundSource=source.id;card.dataset.source=source.id;card.querySelector('.label').textContent=selected?field.label:c.label;card.querySelector('.note').textContent=selected?source.id+' · '+source.source.freshness:c.note;card.setAttribute('aria-label',`Inspect ${defFor(source.id).label}`);}
 for(const row of $$('.lane-row')){const b=bindingFor(snapshot,row.dataset.source);pressed(row,b.id===scene.selected);row.querySelector('.source-state').textContent=b.source.status;row.querySelector('.source-freshness').textContent=`freshness ${b.source.freshness}`;}
 $('#evidence').dataset.source=scene.selected;text('#evidence-title',def.label);text('#boundary',def.boundary);
 const facts=binding.fields.map(f=>{const row=el('div','fact-row');const label=el('span','',f.label);label.append(el('small','',f.path));const value=el('b','',formatValue(f.value));value.dataset.value=f.value===null?'null':String(f.value);row.append(label,value);return row;});$('#facts').replaceChildren(...facts);
 const meta={source_id:scene.selected,snapshot_schema:snapshot?.schema??'not received',snapshot_generated:iso(snapshot?.generated_at),received_in_tab:iso(receivedAt),source_status:binding.source.status,freshness:binding.source.freshness,observed_at:iso(binding.source.observed_at),checked_at:iso(binding.source.checked_at),assessed_at:iso(binding.source.assessed_at),coverage_scope:binding.source.scope??'not reported',source_digest:binding.source.source_version??'not reported',producer_revision:binding.source.producer_revision??'not reported',source_reason:binding.source.reason??'not reported'};
 $('#source-meta').replaceChildren(...Object.entries(meta).flatMap(([key,value])=>[el('dt','',key),el('dd','',value)]));
 for(const article of $$('#static-table article')){const d=defFor(article.dataset.source),b=bindingFor(snapshot,d.id);article.querySelector('.static-facts').textContent=[b.source.status+' / freshness '+b.source.freshness,...b.fields.map(f=>`${f.label}: ${formatValue(f.value)}\n${f.path}`),`Observed: ${iso(b.source.observed_at)}`,`Scope: ${b.source.scope??'not reported'}`,d.boundary].join('\n');}
 $('#compare-panel').hidden=scene.variant!=='compare';$('#facts').hidden=scene.variant==='compare';renderComparison();
 $('#back').disabled=!scene.history.length;$('#enter-lens').disabled=Boolean(scene.lens);for(const id of ['restore','pin','discard'])$('#'+id).disabled=!scene.lens;$('#recall').disabled=!pinned;
 $('#capture-anchor').disabled=!snapshot||transport!=='connected';
 pressed($('#outage'),outage);pressed($('#motion-off'),motionOff);$('#play').disabled=motionOff;
 coreTitle.textContent=scene.variant==='compare'?(anchor?'A / B':'A ? / B'):def.short;
 coreTitle.style.fontSize=scene.variant==='compare'?'21px':def.short.length>8?'20px':'28px';
 coreSub.textContent=scene.variant==='compare'?'LOCAL COMPARE':'SOURCE LENS';
 coreStatus.textContent=binding.source.status+' / '+binding.source.freshness;
 coreStatus.style.fill=binding.source.freshness==='fresh'?'#b4ddc9':'#d8bc97';
 coreStatus.style.fontSize='8px';
 modeLabel.textContent=scene.variant==='trace'?'SELECT → BIND → INSPECT':scene.variant==='focus'?'FOCUS WITHOUT LOSING CONTEXT':anchor?'HELD A ↔ LATEST RECEIVED B':'CAPTURE A TO BEGIN';
 document.body.classList.toggle('motion-disabled',motionOff);
 drawPhase();
}
function renderComparison(){
 const current=get(),held=bindingFor(anchor,scene.selected);
 text('#anchor-at',anchor?iso(anchor.generated_at):'No historical snapshot inferred');text('#current-at',snapshot?iso(snapshot.generated_at):'Not received');
 text('#b-label',hypothesis?'B* · hypothesis, source withheld':'B · latest received');
 let changed=0;
 $('#compare-rows').replaceChildren(...current.fields.map((f,i)=>{const prior=held.fields[i]?.value??null;if(anchor&&!Object.is(prior,f.value))changed++;const row=el('div','compare-row');row.dataset.path=f.path;for(const [label,value]of [[f.label,anchor?formatValue(prior):'not captured'],[f.label,hypothesis?'withheld · hypothesis':formatValue(f.value)]]){const side=el('div');side.append(el('small','',label),el('b','',value));row.append(side);}return row;}));
 text('#compare-note',hypothesis?'ILLUSTRATIVE BRANCH: removing this source withholds these facts. No predicted outcomes or causal effect.':anchor?`${changed} matched field${changed===1?'':'s'} changed between captured A and latest B. This is not an upstream history or trend.`:'Capture A explicitly, then Refresh GET for B. No historical, trend or counterfactual data is invented.');
}
function linkPath(){
 const stage=$('.scene-upper').getBoundingClientRect(),card=$(`[data-card=${defFor(scene.selected).card}]`).getBoundingClientRect(),evidence=$('#evidence').getBoundingClientRect();
 const active=ringNodes.get(scene.selected);
 const radius=active?active.r+(scene.variant==='focus'?8*phase:0):60;
 const selectedPoint=new DOMPoint(...polar(radius,90)).matrixTransform((active?.track??map).getScreenCTM());
 const startX=selectedPoint.x-stage.x,startY=selectedPoint.y-stage.y;
 const cardX=card.x-stage.x+5,cardY=card.y-stage.y+card.height*.55;
 const endX=evidence.x-stage.x+4,endY=evidence.y-stage.y+28;
 const d=`M${startX},${startY} C${startX+60},${startY} ${cardX-30},${cardY} ${cardX},${cardY} L${cardX},${card.y-stage.y+card.height+5} L${endX},${endY}`;
 $('#binding-path').setAttribute('d',d);
 return $('#binding-path');
}
function drawPhase(){
 $('#cockpit').dataset.phase=phase.toFixed(3);$('#scrub').value=String(Math.round(phase*1000));text('#phase-value',`${Math.round(phase*100)}%`);
 const step=Math.min(2,Math.floor(phase*3));text('#phase-step',configs[scene.variant].steps[step]);
 const active=ringNodes.get(scene.selected);
 for(const [id,n]of ringNodes){const selected=id===scene.selected;const focus=scene.variant==='focus';const rr=n.r+(focus&&selected?8*phase:0);n.track.setAttribute('d',arc(rr,ends[n.index]));n.hit.setAttribute('d',arc(rr,ends[n.index]));n.track.setAttribute('opacity',selected?1:focus?1-.72*phase:.75);n.track.setAttribute('stroke-width',selected?8.5:6.5);n.track.setAttribute('filter',selected?'url(#orbit-glow)':'none');const point=polar(rr,ends[n.index]);n.marker.setAttribute('cx',point[0]);n.marker.setAttribute('cy',point[1]);n.marker.setAttribute('fill',bindingFor(snapshot,id).source.freshness==='fresh'?'#ccecd9':'#d8bc97');n.label.setAttribute('opacity',focus&&!selected?.55:1);}
 orbit.setAttribute('transform',scene.variant==='compare'&&anchor?`translate(${-phase*21} 0)`:'translate(0 0)');
 ghost.setAttribute('opacity',scene.variant==='compare'&&anchor?String(.2+.7*phase):'0');
 ghost.setAttribute('transform',`translate(${phase*24} 0)`);
 ghostPath.setAttribute('d',arc(active?.r??160,ends[active?.index??4]));
 focusLeader.setAttribute('opacity',scene.variant==='focus'?'1':'0');focusLabel.setAttribute('opacity',scene.variant==='focus'?'1':'0');
 const fp=polar((active?.r??160)+8*phase,60);focusLeader.setAttribute('d',`M${fp[0]},${fp[1]} L${fp[0]+35},65 L520,65`);focusLabel.textContent=defFor(scene.selected).short+' / SCOPE FIRST';
 const path=linkPath();const length=path.getTotalLength();const point=path.getPointAtLength(length*phase);$('#binding-pulse').setAttribute('cx',point.x);$('#binding-pulse').setAttribute('cy',point.y);$('#binding-pulse').setAttribute('opacity',scene.variant==='trace'&&phase<1?.9:0);path.style.opacity=scene.variant==='trace'?'.5':'.15';
 const e=$('#evidence');e.style.boxShadow=scene.variant==='trace'?`0 0 0 1px rgba(138,231,177,${phase>.64?.2:0})`:scene.variant==='focus'?`0 0 ${phase*20}px rgba(92,190,125,${phase*.08})`:'none';
}
function setPhase(value){phase=Math.max(0,Math.min(1,Number(value)));drawPhase();}
function stop(){playing=false;cancelAnimationFrame(raf);pressed($('#play'),false);text('#play','Play reveal');}
function tick(now){if(!playing)return;if(document.hidden){stop();return;}const delta=(now-lastTick)/6500;lastTick=now;setPhase(phase+delta);if(phase>=1)stop();else raf=requestAnimationFrame(tick);}
function start(){if(motionOff)return;cancelAnimationFrame(raf);if(phase>=1)phase=0;playing=true;lastTick=performance.now();pressed($('#play'),true);text('#play','Pause reveal');raf=requestAnimationFrame(tick);}
async function refresh(){
 if(busy||outage)return;busy=true;const sequence=++loadSequence;$('#refresh').disabled=true;
 try{const response=await fetch('/api/plugins/company-os/snapshot',{method:'GET',credentials:'omit',cache:'no-store',redirect:'error',signal:AbortSignal.timeout(24000)});if(sequence!==loadSequence||outage)return;
  if(response.status===401||response.status===403){snapshot=null;anchor=null;receivedAt=null;transport='denied';notice('Access denied. Current and held facts cleared; restore cannot reveal revoked data.');}
  else{if(!response.ok)throw new Error('Source unavailable');const raw=await response.json();if(sequence!==loadSequence||outage)return;snapshot=project(raw);anchor=revalidateAnchor(anchor,snapshot);receivedAt=Date.now()/1000;transport='connected';notice('Snapshot rebound by stable source ID. Selection, focus and disclosures unchanged.');}
 }catch{if(sequence===loadSequence&&!outage){transport='unavailable';notice(snapshot?'Source unavailable. Last received facts retained, explicitly not current.':'No source data received; all unbound values remain unknown.');}}
 finally{busy=false;$('#refresh').disabled=outage;render();}
}
for(const button of $$('[data-variant]'))button.addEventListener('click',()=>{apply({type:'VARIANT',id:button.dataset.variant});notice('Proposal switched. Selection is stable; data and production layout are unchanged.');});
$('#play').addEventListener('click',()=>playing?stop():start());
$('#scrub').addEventListener('input',e=>{stop();setPhase(Number(e.target.value)/1000);});
$('#motion-off').addEventListener('click',()=>{motionOff=!motionOff;if(motionOff){stop();phase=1;}render();notice(motionOff?'Motion off. Every fact and interaction stays available.':'Motion enabled; play or select to reveal one reading path.');});
reduced.addEventListener('change',e=>{if(e.matches){motionOff=true;stop();phase=1;render();}});
$('#enter-lens').addEventListener('click',enter);
$('#restore').addEventListener('click',()=>restore());$('#discard').addEventListener('click',()=>restore('DISCARD'));
$('#back').addEventListener('click',()=>apply({type:'BACK'}));
$('#pin').addEventListener('click',()=>{pinned=recipe(scene);try{localStorage.setItem(STORAGE,JSON.stringify(pinned));notice('Pinned recipe only: variant + source ID. No facts, snapshot, prompt or meeting content saved.');}catch{notice('Storage unavailable. Pin held in this tab only.');}render();});
$('#recall').addEventListener('click',()=>{if(!pinned)return;enter();apply({type:'VARIANT',id:pinned.variant},{animate:false});apply({type:'SELECT',id:pinned.selected});notice('Pinned presentation recalled; current source access and freshness still apply.');});
$('#forget-pin').addEventListener('click',()=>{pinned=null;try{localStorage.removeItem(STORAGE);}catch{}render();notice('Local saved pin removed. Sources and operational state untouched.');});
$('#source-challenge').addEventListener('click',()=>{$('#provenance').open=!$('#provenance').open;notice('Exact source metadata shown below the selected facts.');});
$('#provenance').addEventListener('toggle',()=>requestAnimationFrame(drawPhase));
$('#capture-anchor').addEventListener('click',()=>{if(snapshot&&transport==='connected'){enter();anchor=structuredClone(snapshot);render();notice('A held in memory only. Refresh GET for a new B; restore or discard removes A.');}});
$('#hypothesis').addEventListener('change',e=>{enter();hypothesis=e.target.checked;render();notice(hypothesis?'Illustrative evidence-withheld branch. No source state or forecast changed.':'Returned to actual latest received B.');});
$('#refresh').addEventListener('click',refresh);
$('#outage').addEventListener('click',()=>{outage=!outage;if(outage){loadSequence++;transport='unavailable';$('#refresh').disabled=true;render();notice('Local outage preview only. No service stopped; facts marked NOT current.');}else{$('#refresh').disabled=false;refresh();}});
$('#equal-table').addEventListener('click',()=>{const show=$('#table-control').hidden;$('#table-control').hidden=!show;pressed($('#equal-table'),show);});
$('#baseline-toggle').addEventListener('click',()=>{const show=$('#reference-panel').hidden;$('#reference-panel').hidden=!show;$('#comparison-layout').classList.toggle('side',show);pressed($('#baseline-toggle'),show);if(show&&$('#reference-frame').getAttribute('src')==='about:blank')$('#reference-frame').src='/video-replica';requestAnimationFrame(drawPhase);});
$('#gallery').addEventListener('toggle',async()=>{if(!$('#gallery').open||$('#capture-gallery').childElementCount)return;try{const response=await fetch('/motion-lab/captures/gallery.json',{credentials:'omit',cache:'no-store'});if(!response.ok)throw new Error();const manifest=await response.json();for(const name of ['baseline','trace','focus','compare']){if(!manifest.images?.some(x=>x.file===name+'.png'))continue;const a=el('a');a.href='/motion-lab/captures/'+name+'.png';a.target='_blank';a.rel='noopener noreferrer';const img=el('img');img.src=a.href;img.alt=name+' actual browser capture';a.append(img,el('small','',name==='baseline'?'00 · Reference fixture':name+' · creative proposal'));$('#capture-gallery').append(a);}if(manifest.video==='motion-tour.webm'){const video=el('video');video.controls=true;video.preload='none';video.src='/motion-lab/captures/motion-tour.webm';video.setAttribute('aria-label','Actual browser motion tour');$('#capture-gallery').append(video);}text('#gallery-note','Actual browser captures · '+manifest.captured_at+' · historical views, not current telemetry.');}catch{text('#gallery-note','No capture manifest yet. The interactive proposals above remain available.');}});
addEventListener('keydown',e=>{if(e.key==='Escape'&&scene.lens){e.preventDefault();restore();}});
addEventListener('resize',()=>requestAnimationFrame(drawPhase));
addEventListener('pagehide',()=>{stop();snapshot=null;anchor=null;});
document.addEventListener('visibilitychange',()=>{if(document.hidden)stop();});
Object.defineProperty(window,'motionReceipt',{get:()=>Object.freeze({schema:'companyos.motion_lab_receipt.v1',variant:scene.variant,selected:scene.selected,revision:scene.revision,lens:Boolean(scene.lens),phase,playing,motionOff,transport,snapshotAt:snapshot?.generated_at??null,anchorAt:anchor?.generated_at??null,hypothesis,pin:pinned?{...pinned}:null,source:'GET /api/plugins/company-os/snapshot',authority:'none',sourcePayloadPersisted:false})});
render();refresh();
