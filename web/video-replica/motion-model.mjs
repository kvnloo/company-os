export function sampleAt(rows,time){
 const t=Math.max(rows[0].t,Math.min(rows.at(-1).t,Number.isFinite(time)?time:0));
 let i=rows.findIndex(x=>x.t>=t);if(i<1)return {...rows[Math.max(i,0)]};
 if(rows[i].t===t)return {...rows[i]};
 const a=rows[i-1],b=rows[i],f=(t-a.t)/(b.t-a.t);
 const mix=(x,y)=>x.map((v,j)=>v+(y[j]-v)*f);
 const parts={};for(const k of Object.keys(a.parts??{})){parts[k]=a.parts[k]&&b.parts?.[k]?mix(a.parts[k],b.parts[k]):a.parts[k];}
 return {...a,t,camera:mix(a.camera,b.camera),parts};
}
export function clockStep(state,delta,duration){
 if(!state.playing)return {...state};
 const time=Math.min(duration,Math.max(0,state.time+delta));
 return {time,playing:time<duration};
}
