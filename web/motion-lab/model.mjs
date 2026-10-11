// Closed, source-owned scalar bindings. No arbitrary paths, prompt text or actions.
const field=(label,path)=>({label,path});
export const LANES=Object.freeze([
 {id:'z0_health',label:'Service health',short:'Health',card:'dispatch',color:'#4be8a7',fields:[field('Service reports OK','z0_service.health.ok')],boundary:'Process health is not behavior or deployment acceptance.'},
 {id:'z0_readiness',label:'Dispatch readiness',short:'Dispatch',card:'dispatch',color:'#4ce0b4',fields:[field('Ready response','z0_service.readiness.ok'),field('Admission ready','z0_service.readiness.aodl_admission_ready'),field('Remote enabled','z0_service.readiness.governed_remote_enabled'),field('Remote ready','z0_service.readiness.governed_remote_ready'),field('Max active','z0_service.readiness.max_active')],boundary:'Admission readiness is not authority, model quality, or deployed acceptance.'},
 {id:'z0_providers',label:'Provider admission',short:'Providers',card:'dispatch',color:'#54d7c4',fields:[field('Returned provider entries','z0_service.providers.length')],boundary:'Provider entries are not host capacity, quota or worker outcomes.'},
 {id:'z0_outcomes',label:'Registered outcomes',short:'Outcomes',card:'outcomes',color:'#60cddb',fields:[field('Registered expectations','z0_service.outcome_coverage.expectations'),field('Observations','z0_service.outcome_coverage.observations'),field('Promotion eligible','z0_service.outcome_coverage.promotion_gate.eligible'),field('Causal quality proven','z0_service.outcome_coverage.promotion_gate.causal_quality_proven')],boundary:'This covers registered expectations only, not company-wide objective completion.'},
 {id:'z0_evaluation',label:'Randomized evidence',short:'Evidence',card:'evaluation',color:'#6ebee7',fields:[field('Returned experiments','z0_service.randomized_evidence.experiments.length'),field('Review ready','z0_service.randomized_evidence.review_ready_any'),field('Human review required','z0_service.randomized_evidence.human_review_required'),field('Causal quality proven','z0_service.randomized_evidence.causal_quality_proven')],boundary:'An empty registered experiment set is not proof of quality or failure.'},
 {id:'hermes_cluster',label:'Hermes registry',short:'Hermes',card:'hermes',color:'#7ba9f0',fields:[field('Registered nodes','hermes_cluster.node_count'),field('Online nodes','hermes_cluster.online_nodes'),field('Registered tasks','hermes_cluster.task_count'),field('Running registered tasks','hermes_cluster.tasks_by_status.running')],boundary:'Registry counts do not join a process to a governed task or independent outcome.'},
 {id:'z0_capacity',label:'Host capacity',short:'Capacity',card:'capacity',color:'#859af2',fields:[field('Capacity plane available','capacity_plane.available')],boundary:'capacity_plane is canonical. The legacy capacity provider alias is not host capacity.'},
 {id:'z0',label:'Control episodes',short:'Control',card:'capacity',color:'#928cf0',fields:[field('Control contract available','control.available'),field('Reported stages','control.stages.length')],boundary:'The control episode read contract is unavailable until its source provides it.'},
 {id:'tokenomics',label:'Measured economics',short:'Economics',card:'economics',color:'#a184ee',fields:[field('Observed cost · USD','economics.observed_cost_usd'),field('Actual tokens','economics.actual_tokens'),field('Verified events','economics.verified_events')],boundary:'No cost window is inferred from token throughput or provider counters.'},
 {id:'memory',label:'Memory runtime',short:'Memory',card:'capacity',color:'#b080e9',fields:[field('Runtime usable','memory.runtime_usable')],boundary:'Archive presence is not a qualified runtime or memory binding.'},
 {id:'z0_metrics',label:'Service counters',short:'Counters',card:'dispatch',color:'#66cabc',fields:[field('Allowlisted metric rows','z0_service.metrics.length')],boundary:'Counters are process metrics, not economics, work done or quality.'},
 {id:'z0_bridge',label:'Bridge capability',short:'Bridge',card:'dispatch',color:'#70c4ce',fields:[field('Execution permission','z0_service.bridge_capabilities.execution_permission'),field('Advertised endpoints','z0_service.bridge_capabilities.endpoints.length')],boundary:'An advertised endpoint is not observed consumer use or permission to act.'},
 {id:'processes',label:'Process presence',short:'Presence',card:'hermes',color:'#879dd9',fields:[field('Projected process entries','fleet.length')],boundary:'Presence is not an active agent, useful work or a task-authority join.'},
 {id:'k8s',label:'Kubernetes inventory',short:'Kubernetes',card:'capacity',color:'#b190ca',fields:[field('Returned nodes','k8s.nodes.length'),field('Returned pods','k8s.pods.length')],boundary:'Inventory readiness is not a delivery acceptance receipt.'}
]);
export const RINGS=Object.freeze(LANES.slice(0,10));
export const CARDS=Object.freeze([
 {id:'dispatch',label:'Dispatch readiness',source:'z0_readiness',path:'z0_service.readiness.ok',note:'Admission only · not authority'},
 {id:'outcomes',label:'Outcome observations',source:'z0_outcomes',path:'z0_service.outcome_coverage.observations',note:'Registered expectations only'},
 {id:'evaluation',label:'Evidence experiments',source:'z0_evaluation',path:'z0_service.randomized_evidence.experiments.length',note:'No causal claim implied'},
 {id:'hermes',label:'Hermes registry tasks',source:'hermes_cluster',path:'hermes_cluster.task_count',note:'Registry only · not delivery'},
 {id:'capacity',label:'Capacity plane',source:'z0_capacity',path:'capacity_plane.available',note:'Missing is never idle'},
 {id:'economics',label:'Observed cost · USD',source:'tokenomics',path:'economics.observed_cost_usd',note:'Exact source window required'}
]);
const enumValue=(v,allowed,fallback='unknown')=>allowed.includes(v)?v:fallback;
const finite=v=>typeof v==='number'&&Number.isFinite(v)?v:null;
const token=v=>typeof v==='string'&&/^[a-z0-9_:.\/-]{1,160}$/i.test(v)?v:null;
const scalar=v=>typeof v==='boolean'?v:finite(v);
function read(o,path){let v=o;for(const key of path.split('.')){if(key==='length'){return Array.isArray(v)?v.length:null;}if(!v||typeof v!=='object'||!Object.hasOwn(v,key))return null;v=v[key];}return scalar(v);}
export function project(raw){
 if(raw?.schema!=='company_os.snapshot.v1')throw new Error('Unsupported snapshot contract');
 const bindings=LANES.map(def=>{const s=raw.sources?.[def.id]??{};return {id:def.id,fields:def.fields.map(f=>({...f,value:['ok','degraded','stale'].includes(s.status)?read(raw,f.path):null})),source:{status:enumValue(s.status,['ok','degraded','unavailable','denied','stale','error']),freshness:enumValue(s.freshness,['fresh','stale','unknown']),observed_at:finite(s.observed_at),checked_at:finite(s.checked_at),assessed_at:finite(s.assessed_at),age_s:finite(s.age_s),source_version:typeof s.source_version==='string'&&/^sha256:[a-f0-9]{64}$/.test(s.source_version)?s.source_version:null,producer_revision:token(s.producer_revision),scope:token(typeof s.coverage==='string'?s.coverage:s.coverage?.scope),reason:token(s.reason)}};});
 return {schema:raw.schema,generated_at:finite(raw.generated_at),status:enumValue(raw.status,['ok','degraded','unavailable']),bindings};
}
export function bindingFor(snapshot,id){
 const def=LANES.find(x=>x.id===id);if(!def)throw new Error('Unknown source selection');
 return snapshot?.bindings.find(x=>x.id===id)??{id,fields:def.fields.map(f=>({...f,value:null})),source:{status:'unknown',freshness:'unknown',observed_at:null,checked_at:null,assessed_at:null,age_s:null,source_version:null,producer_revision:null,scope:null,reason:'not_received'}};
}
export const formatValue=value=>value===null?'unknown':String(value);
export function revalidateAnchor(anchor,current){return current?.bindings.some(b=>b.source.status==='denied')?null:anchor;}

export const VARIANTS=Object.freeze(['trace','focus','compare']);
export function createScene(){return {revision:1,variant:'trace',selected:'z0_readiness',lens:null,history:[]};}
const view=s=>({variant:s.variant,selected:s.selected});
export function transition(state,command){
 if(command.expectedRevision!==undefined&&command.expectedRevision!==state.revision)throw new Error('Stale scene revision');
 const s=structuredClone(state);
 if(command.type==='SELECT'&&!LANES.some(x=>x.id===command.id))throw new Error('Unknown source');
 if(command.type==='VARIANT'&&!VARIANTS.includes(command.id))throw new Error('Unknown variant');
 if(['SELECT','VARIANT'].includes(command.type)){s.history=[...s.history.slice(-19),view(s)];s[command.type==='SELECT'?'selected':'variant']=command.id;}
 else if(command.type==='ENTER'){if(!s.lens)s.lens={base:view(s),parentRevision:s.revision};}
 else if(['RESTORE','DISCARD'].includes(command.type)){if(s.lens)Object.assign(s,s.lens.base);s.lens=null;s.history=[];}
 else if(command.type==='BACK'){const previous=s.history.pop();if(previous)Object.assign(s,previous);}
 else throw new Error('Unknown view command');
 s.revision++;return s;
}
export function recipe(s){return {schema:'companyos.motion_recipe.v1',...view(s)};}
export function restoreRecipe(value){
 if(!value||Object.keys(value).sort().join(',')!=='schema,selected,variant'||value.schema!=='companyos.motion_recipe.v1'||!VARIANTS.includes(value.variant)||!LANES.some(x=>x.id===value.selected))throw new Error('Invalid recipe');
 return recipe(value);
}

