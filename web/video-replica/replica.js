import { fixture, issueBindings } from './bindings.mjs';
import charts from './chart-points.mjs';
const $=s=>document.querySelector(s);
const NS='http://www.w3.org/2000/svg';
function element(tag,attrs,parent){const e=document.createElementNS(NS,tag);for(const[k,v]of Object.entries(attrs))e.setAttribute(k,String(v));if(parent)parent.append(e);return e;}
const ring=$('#rings'),cx=333.25,cy=248.13;
const defs=element('defs',{},ring);
const glow=element('filter',{id:'glow',x:'-100%',y:'-100%',width:'300%',height:'300%'},defs);element('feGaussianBlur',{stdDeviation:3},glow);
const soft=element('radialGradient',{id:'core-halo'},defs);element('stop',{offset:0,'stop-color':'#36b47c','stop-opacity':.16},soft);element('stop',{offset:1,'stop-color':'#27af70','stop-opacity':0},soft);
const colors=['#48eaa3','#46e3aa','#49ddb8','#53d0ce','#60cbe2','#69b6e5','#7aa4ee','#8894ed','#8e89ed','#9c7eec'];
const ends=[333,324,291,327,248,252,233,327,339,270];
const radii=[80.317,97.038,113.86,130.601,147.415,164.167,180.992,197.726,214.531,231.3];
const polar=(r,a)=>[cx+r*Math.sin(a*Math.PI/180),cy-r*Math.cos(a*Math.PI/180)];
const arc=(r,a,b)=>{const s=polar(r,a),e=polar(r,b);return `M${s[0]},${s[1]} A${r},${r} 0 ${b-a>180?1:0} 1 ${e[0]},${e[1]}`;};
element('circle',{cx,cy,r:165,fill:'url(#core-halo)'},ring);
// Reference geometry: initial native frame, no screenshot surfaces in this SVG.
for(let i=9;i>=0;i--){
 const r=radii[i],color=colors[i];
 const gradient=element('linearGradient',{id:`ring-color-${i}`,x1:'0%',y1:'0%',x2:'50%',y2:'100%'},defs);
 element('stop',{offset:0,'stop-color':color,'stop-opacity':.84},gradient);element('stop',{offset:1,'stop-color':color},gradient);
 element('circle',{cx,cy,r,stroke:'#798a80','stroke-opacity':.06,'stroke-width':.8,fill:'none'},ring);
 element('path',{d:arc(r,0,ends[i]),stroke:color,'stroke-width':10,opacity:.20,filter:'url(#glow)',fill:'none','stroke-linecap':'round'},ring);
 element('path',{d:arc(r,0,ends[i]),stroke:`url(#ring-color-${i})`,'stroke-width':7.7,fill:'none','stroke-linecap':'round'},ring);
 const[x,y]=polar(r,ends[i]);
 if([0,1,3,5,6,7,8,9].includes(i)){
  element('circle',{cx:x,cy:y,r:6,fill:'#b9ffdf',filter:'url(#glow)',opacity:.55},ring);
  element('circle',{cx:x,cy:y,r:2.5,fill:'#ddfff4'},ring);
 }
 const label=element('text',{x:cx-5,y:cy-r+3,'text-anchor':'end',class:'priority'},ring);label.textContent=`P${i}`;
}
// Missing arc portions contain the observed rose blocked nodes, not random noise.
for(const[i,angles]of [[2,[292,295,298,301,304,307,310,313,316,319,322,325,328,331,334,337,340,343,346,349,352]], [4,[254.5,262,269.75,277.25,284.75,292.25,299.75,307.5,314.75,322.5,329.75,337.5,345,352.75]], [7,[332,337,342,347,352]]])for(const a of angles){const[x,y]=polar(radii[i],a);element('circle',{cx:x,cy:y,r:i===2?1.8:1.5,fill:'#cd6586',opacity:i===2?.86:.65},ring);}
element('path',{d:arc(radii[4],248,359),stroke:'#82b39f','stroke-width':.6,opacity:.45,fill:'none'},ring);
element('circle',{cx,cy,r:66.8,fill:'#08170f40',stroke:'#436253','stroke-width':.55,'stroke-opacity':.6},ring);
element('path',{d:`M${cx} ${cy-64} L${cx+6} ${cy-9} L${cx+50} ${cy} L${cx+6} ${cy+6} L${cx} ${cy+58} L${cx-4} ${cy+5} L${cx-53} ${cy} L${cx-4} ${cy-5}Z`,fill:'#5ff5aa',opacity:.018},ring);
let text=element('text',{x:cx-9,y:cy-1,'text-anchor':'middle','font-size':38.4,'font-weight':650,fill:'#f0f9f0','letter-spacing':-1.2},ring);text.textContent='77';
text=element('text',{x:cx+16,y:cy,'font-size':18,fill:'#74d4a3'},ring);text.textContent='%';
text=element('text',{x:cx,y:cy+17,'text-anchor':'middle',fill:'#88bd9d',style:'font:7px monospace;letter-spacing:1px'},ring);text.textContent='PROGRAM WORK DONE';
text=element('text',{x:cx,y:cy+31,'text-anchor':'middle',fill:'#718274','font-size':8},ring);text.textContent='1,324 of 1,730';
// Tracked bright flight positions are separated from fixed completion arcs.
const sampleTimes=[0,.1,.2,.3,.4,.5,1,1.5];
// Only six clear, matched angular tracks are animated. The other initial glows
// remain static because their later identities are ambiguous (occlusion/ripples).
// Measurements are in evidence/flight-measurements.json, before camera zoom.
const satellites=[
 {i:0,a:46,track:[46,46.75,52.5,57.25,60.25,62.5,81.25,99]},
 {i:0,a:222,track:[222,228.5,235,241.5,247.75,253,286,317]},
 {i:1,a:5.5},
 {i:4,a:24.25},{i:4,a:45.75},
 {i:4,a:59,track:[59,61.75,64,67,69,70.75,84.25,96.25]},
 {i:4,a:110.75,track:[110.75,113,115.5,118,120.25,121.5,133.5,144.75]},
 {i:4,a:151.5,track:[151.5,152.25,154.5,155.75,157,158.5,165.5,172.5]},
 {i:4,a:157.75,track:[157.75,160,162.5,165.25,167.5,169.25,182.25,194.25]},
 {i:4,a:285},{i:4,a:307.25},{i:4,a:327.25},{i:4,a:345}
].map(p=>{
 const trail=element('path',{stroke:'#aaffd5','stroke-width':2.4,opacity:.27,filter:'url(#glow)',fill:'none'},ring);
 const g=element('g',{'data-flight':p.i},ring);element('circle',{r:6,fill:'#b1ffe4',filter:'url(#glow)',opacity:.58},g);element('circle',{r:2,fill:'#d0fff0',opacity:.35},g);return {...p,g,trail};
});
const hit=element('circle',{cx,cy,r:radii[4],class:'ring-hit','stroke-width':15,tabindex:0,role:'button','aria-label':'P4 Breadth census reference details'},ring);
const tooltip=$('#ring-tooltip');
for(const name of ['pointerenter','focus'])hit.addEventListener(name,()=>{tooltip.hidden=false;});
for(const name of ['pointerleave','blur'])hit.addEventListener(name,()=>{tooltip.hidden=true;});
hit.addEventListener('keydown',e=>{if(e.key==='Escape')tooltip.hidden=true;});
function drawChart(svg,name,color){const c=charts[name],d=c.points.map(([x,y],i)=>`${i?'L':'M'}${x},${y}`).join(' ');svg.setAttribute('viewBox',`0 0 ${c.width} ${c.height}`);element('path',{d:`${d} L${c.width},${c.height} L0,${c.height}Z`,fill:color,opacity:.06},svg);element('path',{d,fill:'none',stroke:color,'stroke-width':1.1,'stroke-linecap':'round','stroke-linejoin':'round'},svg);}
$('#readiness-bars').innerHTML=[['XLSX',24.9],['DOCX',19.4],['PPTX',22.8]].map(([label,p])=>`<div class="readiness-row"><span>${label}</span><div class="bar-track"><div class="bar-fill" style="width:${p}%"></div></div><span class="percent">${p.toFixed(1)}%</span></div>`).join('');
drawChart($('#parity-line'),'parity','#d6ded9');
$('#metric-strip').innerHTML=fixture.metrics.map(m=>`<article class="metric-card ${m.id}"><div class="metric-label">${m.label}</div><div class="metric-value">${m.value}${m.suffix?`<small>${m.suffix}</small>`:''}</div><div class="metric-description">${m.description}</div>${m.ticks?`<div class="agent-ticks">${Array.from({length:m.ticks},(_,i)=>`<i class="${i<m.on?'on':''}"></i>`).join('')}</div>`:''}${m.spark?`<svg class="metric-spark" data-spark="${m.spark}" aria-hidden="true"></svg>`:`${m.progress?`<div class="metric-track ${m.purple?'purple':''}"><div class="bar-fill" style="width:${m.progress}%"></div></div>`:''}`}</article>`).join('');
for(const s of document.querySelectorAll('[data-spark]'))drawChart(s,s.dataset.spark,s.dataset.spark==='merged'?'#b19ae7':'#81ddbb');
drawChart($('#lane-spark'),'lanes','#86e7c0');
$('#lane-totals').innerHTML=fixture.totals.map(([value,unit])=>`<span class="lane-total"><b>${value}</b>${unit}</span>`).join('');
$('#lane-columns').innerHTML=fixture.lanes.map(column=>`<div class="lane-column">${column.map(([role,name,detail,rate,state,time,mix],i)=>`<div class="lane-row ${i===0?'featured':''}"><i class="lane-dot ${role}"></i><div class="lane-copy"><div class="lane-name"><em>${role}</em>${name}</div><div class="lane-detail">${detail}</div></div><div class="lane-mix">${mix.map(([kind,percent])=>`<i class="${kind}" style="width:${percent}%"></i>`).join('')}</div><div class="lane-rate"><b>${rate}</b>/min</div><div class="lane-state ${state}"><i></i>${state} ${time}</div></div>`).join('')}</div>`).join('');
$('#binding-map').innerHTML=issueBindings.map(b=>`<article><h3>${b.widget}</h3><p><b>Region:</b> ${b.region}</p><p>${b.meaning}</p><p><b>Existing owner / adapter slot:</b> ${b.source}</p><p><b>Guard:</b> ${b.guard}</p><small>Issue #5 body lines ${b.issueLines} · <code>${b.id}</code> · unconnected</small></article>`).join('');
const reduced=matchMedia('(prefers-reduced-motion: reduce)');
let playing=false,start=0,elapsed=0,animation=0;
function updateMotion(t){for(const p of satellites){let a=p.a;if(p.track){const end=sampleTimes.findIndex(x=>x>=t);const j=Math.max(1,end<0?sampleTimes.length-1:end),f=(t-sampleTimes[j-1])/(sampleTimes[j]-sampleTimes[j-1]);a=p.track[j-1]+(p.track[j]-p.track[j-1])*f;}const [x,y]=polar(radii[p.i],a);p.g.setAttribute('transform',`translate(${x} ${y})`);p.trail.setAttribute('d',arc(radii[p.i],a-10,a));} $('#replica-frame').dataset.motionSeconds=t.toFixed(3);}
function tick(now){if(!playing)return;elapsed=(now-start)/1000;updateMotion(elapsed%1.5);animation=requestAnimationFrame(tick);}
function setPlaying(value){playing=value;$('#motion').setAttribute('aria-pressed',String(value));$('#motion').textContent=value?'Pause ring motion':'Play measured ring motion';$('#motion-note').textContent=value?'Six measured flight tracks replay 0–1.5 s in a loop. Other glows and all metric values remain frozen to the first frame. No camera movement, polling, or live activity inference.':'Paused reference fixture. Six matched ring-flight tracks are available; remaining event-ripple choreography is not reconstructed. Hover/focus P4 for its observed tooltip.';cancelAnimationFrame(animation);if(value){start=performance.now()-elapsed*1000;animation=requestAnimationFrame(tick);}}
$('#motion').addEventListener('click',()=>setPlaying(!playing));
reduced.addEventListener('change',e=>{if(e.matches)setPlaying(false);});
$('#reset').addEventListener('click',()=>{setPlaying(false);elapsed=0;updateMotion(0);tooltip.hidden=true;setView('replica');});
updateMotion(0);
const native=new URLSearchParams(location.search).has('native');if(native)document.body.classList.add('native');
let view='replica';
function resize(){const availableWidth=innerWidth/(view==='side'?2:1);const scale=native&&view!=='side'?1:Math.min(availableWidth/1496,Math.max(200,innerHeight-126)/1080);$('#stage-holder').style.width=`${1496*scale}px`;$('#stage-holder').style.height=`${1080*scale}px`;$('#replica-frame').style.transform=`scale(${scale})`;$('#side-reference').style.width=`${1496*scale}px`;}
function setView(value){view=value;$('#comparison').dataset.view=value;$('#original-overlay').hidden=!['original','overlay'].includes(value);$('#original-overlay').style.opacity=value==='original'?'1':String(Number($('#overlay-opacity').value)/100);$('#side-reference').hidden=value!=='side';$('#opacity-control').hidden=value!=='overlay';for(const b of document.querySelectorAll('button[data-view]'))b.setAttribute('aria-pressed',String(b.dataset.view===value));resize();}
for(const b of document.querySelectorAll('button[data-view]'))b.addEventListener('click',()=>setView(b.dataset.view));
$('#overlay-opacity').addEventListener('input',e=>{$('#original-overlay').style.opacity=String(Number(e.target.value)/100);});
addEventListener('resize',resize);resize();
window.replicaReceipt=Object.freeze({mode:fixture.mode,width:1496,height:1080,frameSeconds:0,sourceSha256:fixture.sourceSha256,issueBindingSlots:issueBindings.length,liveConnected:false});
