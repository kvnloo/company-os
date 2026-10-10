/** @typedef {'unknown'|'observed'|'stale'|'conflict'|'pending-proof'|'verified'} EvidenceStatus */
/** @template T @typedef {{mode:'source-bound',status:EvidenceStatus,value:T|null,sourceRefs:string[],observedAt:string,unit:string,denominator:number|null}} SourceBinding */
/** @typedef {{id:string,widget:string,region:string,meaning:string,source:string,guard:string,issueLines:string}} IssueBinding */
/** @type {ReadonlyArray<IssueBinding>} */
export const issueBindings=Object.freeze([
 {id:'rings',widget:'ObjectiveRing / ReadinessBand',region:'Concentric North Star rings',meaning:'3–7 prioritized objectives/workstreams with horizon, status and ownership; declared progress is distinct from verified outcomes and missing coverage.',source:'Issue candidate objectives[]; z0intelligence State Packets (#22/#137) and outcome/evidence lineage (#54), via existing CompanyOS #2 / PR #3 read-only snapshot. Exact field binding remains unconnected.',guard:'Never derive an overall percent from activity. Preserve denominator, source and unknowns.',issueLines:'43, 164, 178, 191–192'},
 {id:'metrics',widget:'OutcomeDelta / MetricStrip',region:'Readiness headline, small trends, six metric cards',meaning:'Independently verified outcome delta against one versioned objective. Cards may represent blockers, approvals, stale/ungoverned coverage, active lanes and measured economics; issue does not assign each of the six video cards.',source:'Existing CompanyOS snapshot/source IDs; z0intelligence #54 outcome lineage; Tokenomics owns measured cost. Reference XLSX/DOCX/PPTX/commercial readiness is NOT a live mapping.',guard:'Exact window, denominator, units, source and observation age; throughput is not outcome.',issueLines:'44, 165–166, 211'},
 {id:'lanes',widget:'FactoryLaneMatrix',region:'Lanes right now matrix',meaning:'Task/owner, last useful event, waiting reason, supported ETA and verifier state. Group by objective rather than model.',source:'Issue candidate workstreams[]; Hermes/OMP execution; Linear/GitHub canonical work items; z0intelligence #47 control/agent snapshot. CompanyOS only projects those sources.',guard:'Heartbeat ≠ work completed ≠ verified outcome; preserve stale, blocked and unknown distinctions.',issueLines:'45, 167, 180, 193–195, 207–211'},
 {id:'attention',widget:'WhatChanged / AttentionQueue',region:'Issue-defined compact rails; not inserted into the faithful first frame',meaning:'Deduplicated consequential deltas plus prioritized human decision requests: reason, urgency, uncertainty and owner.',source:'Issue candidate attention_items[] and existing AODL/Hermes/Linear authority path; source packet must supply evidence and timestamps.',guard:'No invented urgency or implicit approval; repeated receipts are not repeated progress.',issueLines:'46, 179–181, 196–199'},
 {id:'dependency',widget:'DependencyLens / RevOpsFunnel',region:'Issue future relationship displays; not shown in initial frame',meaning:'Source-scoped PR dependencies or RevOps cohort/funnel comparison, only with real demand and authorized source-backed fixtures.',source:'Linear/GitHub canonical dependencies; RevOps feed is unconnected in this study and must remain unavailable until authorized.',guard:'Hypothesis is not causation; no fabricated CRM/BI data.',issueLines:'47, 51, 55–65'},
 {id:'evidence',widget:'EvidenceDrawer / ResolutionLens',region:'Hidden detail; reference P4 tooltip retained separately',meaning:'Known / unknown / conflict / next probe linked to canonical facts and receipts.',source:'z0intelligence State Packet → outcome/causal/evidence lineage → canonical original source (#22/#54).',guard:'Unknown never paints green; the reference tooltip is NOT a CompanyOS evidence receipt.',issueLines:'48, 88, 169'},
 {id:'hypothesis',widget:'CompareBranch / ImpactPath',region:'Issue future meeting scratch investigation; absent from the video initial frame',meaning:'Reversible hypothesis branch, preview then Back / restore / pin / discard. No implied observed business fact.',source:'Pinned existing snapshot, intent refs and source IDs; AODL authority remains with existing owner.',guard:'Hypothetical projections visibly distinct from observed state. No generated executable code or automatic publication.',issueLines:'49, 35–37, 93–114'}
]);

/** Pure opt-in seam for a future reviewed source adapter; never fetches or mutates. @template T @param {string} id @param {SourceBinding<T>} binding @returns {Readonly<SourceBinding<T>>} */
export function acceptSourceBinding(id,binding){
 if(!issueBindings.some(x=>x.id===id))throw new Error('Unknown issue-defined binding');
 if(binding?.mode!=='source-bound')throw new Error('Explicit source-bound value required; reference fixture cannot become live');
 if(!Array.isArray(binding.sourceRefs)||!binding.sourceRefs.length||binding.sourceRefs.some(x=>typeof x!=='string'||!x)||!binding.observedAt||!Number.isFinite(Date.parse(binding.observedAt))||!binding.unit||!Object.hasOwn(binding,'denominator')||!Object.hasOwn(binding,'value'))throw new Error('Required provenance, unit, time, denominator and value missing');
 if(!['unknown','observed','stale','conflict','pending-proof','verified'].includes(binding.status))throw new Error('Explicit evidence status required');
 if(binding.unit==='percent'&&binding.value!==null&&(!Number.isFinite(binding.denominator)||binding.denominator<=0))throw new Error('A displayed percent requires a positive source denominator');
 return Object.freeze({...binding,sourceRefs:Object.freeze([...binding.sourceRefs])});
}

export const fixture=Object.freeze({
 mode:'reference-fixture',initialFrameSeconds:0,source:'https://github.com/user-attachments/assets/18dc5eb2-e513-4486-a33b-5937f8d176ef',sourceSha256:'84a29e4fafea04c7a4b945f7db4f6c5b09877ba8996572d244662996093063b5',
 metrics:[
  {id:'lanes-working',label:'Agent lanes working',value:'17',suffix:'/26',description:'4 claimed in the last hour',ticks:26,on:17},
  {id:'completed',label:'Completed · 24 h',value:'138',description:'311 added · hourly trend',spark:'completed'},
  {id:'merged',label:'Merged · 24 h',value:'136',description:'64% of 212 attempts landed',spark:'merged',purple:true},
  {id:'census',label:'Census evidence',value:'11.5',suffix:'%',description:'+1,018 leaves today · 890,646 total',progress:11.5},
  {id:'capabilities',label:'WolfXL capabilities',value:'71',suffix:'/80',description:'88.8% verified on the capability board',progress:88.8,purple:true},
  {id:'tracker',label:'Tracker items done',value:'2,772',description:'of 3,278 · 52 blocked now',progress:84.56}
 ],
 totals:[['18','agents'],['16','tool calls/min'],['9,847','tokens/min'],['0','files edited/min'],['3','commits/h']],
 lanes:[
  [
   ['central','ltg-wave0','3 agents · 1 commit this hour · <span class="errors">3 tool errors</span> · tools 102 in 10 min',12,'ask','24s',[['edit',33],['run',67]]],
   ['P0','ltg-ops-pr106-release-owner','tools 8 in 10 min',1,'bash','43s',[['delegate',100]]],
   ['P0','ltg-ops-parity-host-ltg-self-gates','tools 22 in 10 min',0,'wait','3m 02s',[]],
   ['P4','xl-cap-custom-geometry-editing-metadata','1 uncommitted · tools 0 in 10 min',0,'wait','22m 08s',[]],
   ['P4','xl-x14-data-validations-read','1 uncommitted · tools 0 in 10 min',0,'wait','25m 15s',[]],
   ['P0','ltg-ops-gate-host-verda-env-parity','tools 0 in 10 min',0,'wait','29m 36s',[]],
   ['owner','ltg-owner-docx','tools 0 in 10 min',0,'idle','',[]]
  ],[
   ['owner','ltg-owner-xl','2 agents · tools 1 in 10 min',3,'bash','3s',[['run',67],['delegate',33]]],
   ['P4','xl-lambda-parameter-validation','2 uncommitted · tools 16 in 10 min',0,'wait','1m 17s',[]],
   ['P4','xl-cap-fillgeom-camera-lighting-authoring','tools 0 in 10 min',0,'wait','15m 30s',[]],
   ['P4','xl-cap-drawing-reflection-glow-shadow','1 uncommitted · tools 0 in 10 min',0,'wait','24m 59s',[]],
   ['P4','xl-cap-sparkline-preset-choices','1 uncommitted · tools 0 in 10 min',0,'wait','26m 45s',[]],
   ['P1','ltg-max-m6-robustness','tools 0 in 10 min',0,'idle','',[]],
   ['owner','ltg-owner-gap','tools 0 in 10 min',0,'idle','',[]]
  ]
 ]
});
