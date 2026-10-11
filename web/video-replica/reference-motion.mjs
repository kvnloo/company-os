import timeline from './motion-timeline.mjs';
import {sampleAt,clockStep} from './motion-model.mjs';
import {summaryObservations,laneOrders} from './observed-states.mjs';
const NS='http://www.w3.org/2000/svg',I=[1,0,0,1,0,0];
const radii=[80.317,97.038,113.86,130.601,147.415,164.167,180.992,197.726,214.531,231.3];
export function mountReferenceMotion({resetInitial,setView,satellites}){
 const $=s=>document.querySelector(s),frame=$('#replica-frame');
 const layer=document.createElement('div');layer.id='camera-layer';Object.assign(layer.style,{position:'absolute',inset:'0',transformOrigin:'0 0'});
 layer.append($('.wallpaper'),$('.shell'));frame.prepend(layer);
 const control=document.createElement('div');control.className='controls-row timeline-controls';
 control.innerHTML=`<label>Reference time <input id="motion-scrub" type="range" min="0" max="${timeline.duration}" value="0" step="0.000001" aria-label="Reference time in seconds"></label><output id="motion-time">0.000 / ${timeline.duration.toFixed(3)} s</output><button id="camera-toggle" aria-pressed="true">Recording transform: on</button><span>20 Hz measurements · 60 fps source · not live</span>`;
 $('#study-controls').insertBefore(control,$('#motion-note'));
 $('.fixture-notice span').textContent='Full reference sequence · measured image-space replay · independent HTML/CSS/SVG · no operational backend';
 $('#motion-note').textContent='Measured camera/content transforms, ring tracks, chart paths, cursor and P4 disclosure. Later browser-zoom layout and revealed lower panels are approximated. Source video is comparison-only; invisible inputs and backend causality remain unknown.';
 const detail=document.createElement('p');detail.id='measurement-status';$('#study-controls').append(detail);
 const flightLayer=document.createElementNS(NS,'g');flightLayer.id='measured-flights';$('#rings').append(flightLayer);
 const dots=Array.from({length:80},()=>{const g=document.createElementNS(NS,'g');for(const[r,o,f]of[[5,.5,'url(#glow)'],[1.7,.8,'none']]){const c=document.createElementNS(NS,'circle');c.setAttribute('r',r);c.setAttribute('fill','#b7ffe6');c.setAttribute('opacity',o);c.setAttribute('filter',f);g.append(c);}flightLayer.append(g);return g;});
 const cross=document.createElementNS(NS,'svg');cross.setAttribute('viewBox','0 0 28 29');cross.id='reference-cross';cross.innerHTML='<path d="M12 2h4v10h10v4H16v11h-4V16H2v-4h10Z" fill="#171d19" stroke="#e2eae6" stroke-width="2"/>';Object.assign(cross.style,{position:'absolute',width:'28px',height:'29px',pointerEvents:'none'});frame.append(cross);
 const tip=$('#ring-tooltip'),recordedTip=tip.cloneNode(true);recordedTip.id='recorded-tooltip';Object.assign(recordedTip.style,{position:'absolute',zIndex:9,transformOrigin:'0 0'});frame.append(recordedTip);
 const parts={ring:[$('#objective-ring'),102,112],outcome:[$('#outcome'),789,140],metrics:[$('#metric-strip'),789,382],lanes:[$('#lane-panel'),102,638],header:[$('.dash-header'),102,71]};
 const referenceVideos=[];
 for(const[parent,id]of[[$('#stage-holder'),'moving-reference'],[$('#side-reference'),'side-moving-reference']]){
  const v=document.createElement('video');v.id=id;v.src='/video-replica/assets/reference.mp4';v.muted=true;v.preload='auto';v.playsInline=true;v.hidden=true;Object.assign(v.style,{position:id==='moving-reference'?'absolute':'relative',inset:'0',width:'100%',height:'100%',pointerEvents:'none',objectFit:'fill'});parent.append(v);referenceVideos.push(v);
 }
 const originalCharts=new Map([...document.querySelectorAll('[data-spark],#lane-spark')].map(e=>[e,{html:e.innerHTML,viewBox:e.getAttribute('viewBox')}]));
 const lower=document.createElement('div');lower.className='revealed-lower';lower.innerHTML='<div class="launch-fixture">'+Array.from({length:6},(_,i)=>`<span><i>L${i+1}</i><small>open</small></span>`).join('')+'</div><div class="outreach-fixture">'+Array.from({length:10},(_,i)=>`<i class="${[2,3].includes(i)?'dim':''}">${i+1}</i>`).join('')+'</div><div class="road-fixture"><span>M1</span><span>M2</span><span>M3</span><span>M4</span><span>M5</span><span>M6</span></div>';
 $('.bottom-strip').append(lower);
 const original={metric:$('#metric-strip').getAttribute('style'),bottom:$('.bottom-strip').getAttribute('style'),lane:$('#lane-panel').getAttribute('style')};
 let state={time:0,playing:false},camera=true,raf=0,last=0;
 const laneColumns=[...document.querySelectorAll('.lane-column')];
 const initialRows=laneColumns.map(col=>[...col.children]);
 const rowMap=new Map(initialRows.flat().map(row=>[row.querySelector('.lane-name').lastChild.textContent,row]));
 const m6=rowMap.get('ltg-max-m6-robustness').cloneNode(true);
 m6.querySelector('.lane-name').lastChild.textContent='ltg-m6-fix-wolfxl-xlsx-render-png-crash';
 m6.querySelector('.lane-detail').textContent='';
 m6.querySelector('.lane-state').innerHTML='<i></i>idle';
 rowMap.set('ltg-m6-fix-wolfxl-xlsx-render-png-crash',m6);
 let appliedOrder=-1;
 const apply=(el,m,x,y)=>{const[a,b,c,d,e,f]=m;el.style.transformOrigin='0 0';el.style.transform=`matrix(${a},${b},${c},${d},${a*x+c*y+e-x},${b*x+d*y+f-y})`;};
 const uncam=(xy,c)=>{const[a,b,k,d,x,y]=c,det=a*d-b*k;return [(d*(xy[0]-x)-k*(xy[1]-y))/det,(-b*(xy[0]-x)+a*(xy[1]-y))/det];};
 function syncVideo(){const view=$('#comparison').dataset.view,active=state.time>0;
  referenceVideos[0].hidden=!(active&&['original','overlay'].includes(view));referenceVideos[0].style.opacity=view==='original'?'1':String(Number($('#overlay-opacity').value)/100);
  referenceVideos[1].hidden=!(active&&view==='side');$('#side-reference img').hidden=active;
  if(active&&view==='original')$('#original-overlay').hidden=true;
  for(const v of referenceVideos){if(!v.hidden&&v.readyState>=1&&Math.abs(v.currentTime-state.time)>.02)v.currentTime=state.time;}
 }
 for(const b of document.querySelectorAll('button[data-view]'))b.addEventListener('click',syncVideo);
 $('#overlay-opacity').addEventListener('input',syncVideo);for(const v of referenceVideos)v.addEventListener('loadedmetadata',syncVideo);
 function draw(){
  const sample=sampleAt(timeline.samples,state.time),initial=state.time===0;
  const totals=summaryObservations.filter(x=>x.t<=state.time).at(-1);
  [...document.querySelectorAll('#lane-totals b')].forEach((e,i)=>{e.textContent=totals.values[i];});
  const orderIndex=laneOrders.findLastIndex(x=>x.t<=state.time);
  if(orderIndex!==appliedOrder){
   const desired=orderIndex<0?initialRows:[laneOrders[orderIndex].left.map(x=>rowMap.get(x)),laneOrders[orderIndex].right.map(x=>rowMap.get(x))];
   laneColumns.forEach((col,j)=>{col.replaceChildren(...desired[j]);[...col.children].forEach((e,i)=>e.classList.toggle('featured',i===0));});
   appliedOrder=orderIndex;
  }
  m6.querySelector('.lane-rate b').textContent=state.time>=11?'10':'1';
  const cameraMatrix=camera?sample.camera:I;
  layer.style.transform=initial||cameraMatrix.every((v,i)=>v===I[i])?'none':`matrix(${cameraMatrix.join(',')})`;
  for(const[k,[el,x,y]]of Object.entries(parts))apply(el,initial?I:sample.parts[k]??I,x,y);
  const rm=sample.parts.ring??I,us=Math.hypot(rm[0],rm[1]);
  // Layout approximation for actual browser zoom/reflow, distinct from recording transform.
  if(state.time>=10.15){
   const fontScale=Math.max(.60,Math.min(1,us));
   const top=fontScale<.78?380:337;
   $('#metric-strip').style.transform=`translateY(${top-382}px)`;
   $('#metric-strip').style.gridTemplateRows=`${120*fontScale}px ${89*fontScale}px`;
   $('#metric-strip').style.gap=`${8*fontScale}px`;
   for(const e of document.querySelectorAll('.metric-value'))e.style.fontSize=`${24*fontScale}px`;
   for(const e of document.querySelectorAll('.metric-label,.metric-description'))e.style.fontSize=`${9*fontScale}px`;
   const lanes=$('#lane-panel'),lm=sample.parts.lanes??I,ls=Math.max(.6,Math.min(1,Math.hypot(lm[0],lm[1])));
   if(sample.partConfidence.lanes.startsWith('held')&&Math.abs(ls-fontScale)>.08){apply(lanes,[fontScale,0,0,fontScale,102*(1-fontScale),650-638*fontScale],102,638);lanes.style.width=`${1292/fontScale}px`;}
   else lanes.style.width=`${1292/ls}px`;
   $('.bottom-strip').style.top=`${fontScale<.78?866:865}px`;
   $('.bottom-strip').style.transform='none';
  }else{
   $('#metric-strip').style.gridTemplateRows='';$('#metric-strip').style.gap='';$('#lane-panel').style.width='';
   for(const e of document.querySelectorAll('.metric-value,.metric-label,.metric-description'))e.style.fontSize='';
   $('.bottom-strip').style.top='978px';apply($('.bottom-strip'),sample.parts.lanes??I,102,1019);
  }
  lower.hidden=initial;apply($('.ring-legend'),initial?I:rm,121,611);
  for(const p of satellites){p.g.style.display=initial?'':'none';p.trail.style.display=initial?'':'none';}
  if(initial)resetInitial();
  dots.forEach((g,i)=>{const p=sample.flights?.[i];g.style.display=!initial&&p?'':'none';if(p){const[r,a,o]=p,rad=a*Math.PI/180;g.setAttribute('transform',`translate(${333.25+radii[r]*Math.sin(rad)} ${248.13-radii[r]*Math.cos(rad)})`);g.setAttribute('opacity',o);}});
  const ptr=$('#recorded-pointer');ptr.style.display=initial||sample.pointer?'':'none';
  if(initial){ptr.style.left='856px';ptr.style.top='560px';ptr.style.width='29px';ptr.style.height='44px';}
  else if(sample.pointer){const p=sample.pointer,xy=camera?p.source_xy:uncam(p.source_xy,sample.camera),s=camera?1:1/Math.hypot(sample.camera[0],sample.camera[1]);ptr.style.left=`${xy[0]}px`;ptr.style.top=`${xy[1]}px`;ptr.style.width=`${p.source_wh[0]*s}px`;ptr.style.height=`${p.source_wh[1]*s}px`;}
  for(const[k,el]of[['crossPointer',cross],['tooltip',recordedTip]]){const p=sample[k];el.hidden=initial||!p;el.style.display=initial||!p?'none':'';if(p&&!initial){const xy=camera?p.xy:uncam(p.xy,sample.camera),s=camera?Math.hypot(sample.camera[0],sample.camera[1]):1;el.style.left=`${xy[0]}px`;el.style.top=`${xy[1]}px`;el.style.transform=`scale(${s})`;if(k==='crossPointer')ptr.style.display='none';}}
  for(const[svg,originalChart]of originalCharts){const name=svg.dataset.spark??'lanes',track=sample.charts?.[name];if(initial||!track){if(initial){svg.innerHTML=originalChart.html;svg.setAttribute('viewBox',originalChart.viewBox);}continue;}const paths=svg.querySelectorAll('path'),d=track.points.map(([x,y],i)=>`${i?'L':'M'}${x},${y}`).join(' ');svg.setAttribute('viewBox',`0 0 ${track.box[2]-track.box[0]} ${track.box[3]-track.box[1]}`);if(paths[0])paths[0].setAttribute('d',`${d}L175,31L0,31Z`);if(paths[1])paths[1].setAttribute('d',d);}
  frame.dataset.motionSeconds=state.time.toFixed(3);$('#motion-scrub').value=String(state.time);$('#motion-time').textContent=`${state.time.toFixed(3)} / ${timeline.duration.toFixed(3)} s`;
  $('#motion').setAttribute('aria-pressed',String(state.playing));$('#motion').textContent=state.playing?'Pause reference':'Play reference';
  detail.textContent=`Frame ${sample.frame} · ${sample.cameraBasis} · ${sample.flights?.length??0} accepted glow observations. ${state.time>=10.15?'Late grid reflow is approximate.':''} Inputs/backend: unobservable.`;
  syncVideo();
 }
 function tick(now){if(!state.playing)return;state=clockStep(state,(now-last)/1000,timeline.duration);last=now;draw();if(state.playing)raf=requestAnimationFrame(tick);}
 function play(value){cancelAnimationFrame(raf);state.playing=value;if(value){if(state.time>=timeline.duration)state.time=0;last=performance.now();raf=requestAnimationFrame(tick);}draw();}
 $('#motion').addEventListener('click',()=>play(!state.playing));
 $('#motion-scrub').addEventListener('input',e=>{const value=Number(e.target.value);play(false);state.time=Math.max(0,Math.min(timeline.duration,value));draw();});
 $('#motion-scrub').addEventListener('keydown',e=>{
  const delta={ArrowRight:.05,ArrowUp:.05,ArrowLeft:-.05,ArrowDown:-.05,PageUp:1,PageDown:-1};
  if(!(e.key in delta)&&!['Home','End'].includes(e.key))return;
  e.preventDefault();const t=e.key==='Home'?0:e.key==='End'?timeline.duration:state.time+delta[e.key];
  e.target.value=String(Math.max(0,Math.min(timeline.duration,t)));e.target.dispatchEvent(new Event('input',{bubbles:true}));
 });
 $('#reset').addEventListener('click',()=>{
  state={time:0,playing:false};cancelAnimationFrame(raf);tip.hidden=true;setView('replica');draw();
  // Recreate the paint layer (not DOM nodes/listeners): Chromium can retain
  // stale scaled clip/SVG pixels after matrix changes. One reset-only layout
  // flush restores the exact initial raster; keyboard focus is outside it.
  layer.remove();void frame.offsetWidth;frame.prepend(layer);
 });
 $('#camera-toggle').addEventListener('click',e=>{camera=!camera;e.target.setAttribute('aria-pressed',String(camera));e.target.textContent=`Recording transform: ${camera?'on':'off'}`;draw();});
 matchMedia('(prefers-reduced-motion: reduce)').addEventListener('change',e=>{if(e.matches)play(false);});
 window.motionReference=Object.freeze({state:()=>({...state,camera}),seek:t=>{play(false);state.time=Math.max(0,Math.min(timeline.duration,t));draw();},sourceSha256:timeline.sourceSha256,measuredSamples:timeline.samples.length,liveConnected:false});
 draw();
}
