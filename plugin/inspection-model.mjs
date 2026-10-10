// Generated from plugin/plugin.js; React/SDK/network-free chooser adapter. Do not edit.
const str = v => (v == null || v === '' ? '—' : String(v))
const short = (v,n=18) => { const s=str(v); return s.length>n ? s.slice(0,n-1)+'…' : s }
const numeric = v => typeof v === 'number' && Number.isFinite(v) && v >= 0
const count = v => numeric(v) ? v.toLocaleString() : 'unknown'
const money = v => numeric(v) ? '$'+v.toFixed(v<1?4:2) : 'unknown'
function buildInspectionModel(s={}){
  const nodes={}, src=s.sources||{}, service=s.z0_service||{}, cp=s.capacity_plane||{}, k=s.k8s||{}
  const add=(id,label,parent,sources,meaning,limitation,data={},observedCount=null)=>{
    const node={id,label,parent,sources,meaning,limitation,data,observedCount,children:[]}
    nodes[id]=node
    if(parent)nodes[parent].children.push(id)
    return node
  }
  const group=(id,label,sources,question,limit,data,count)=>add(id,label,'network',sources,question,limit,data,count)
  const rows=(parent,values,identity,label,sources,meaning,limit)=>{
    const seen=new Set()
    for(const row of (values||[]).slice(0,100)){
      const id=identity(row)
      if(!id || seen.has(id))continue
      seen.add(id);add(id,label(row),parent,sources,meaning,limit,row)
    }
  }
  add('network','Network',null,['projection'],'What is observable across the local z0 system?',
      'Representative source groups, not an authoritative topology or global inventory.',s.coverage||{})
  group('agents','Agents',['processes'],'Which agent processes are present? Process presence is not active work.',
        'Exact local comm matches only; Python/node-hosted and remote agents may be missing. No session/task join.',
        s.coverage||{},src.processes?.status==='ok'?(s.fleet||[]).length:null)
  rows('agents',s.fleet,r=>'process:'+r.pid,r=>(r.harness||'process')+' · pid '+r.pid,['processes'],
       'Inspect an observed local process.', 'PID can be reused. Process age is not task age; heartbeat, session, trace and governance remain unknown.')
  add('cluster:nodes','Cluster registry','agents',['hermes_cluster'],'How many nodes are registered with Hermes Cluster?',
      'A separate registry, not process inventory or proof of active work. No identity join is inferred.',
      {node_count:s.hermes_cluster?.node_count,online_nodes:s.hermes_cluster?.online_nodes},s.hermes_cluster?.node_count??null)
  group('services','Services',['z0_health','z0_readiness','z0_bridge','z0_metrics'],
        'Is the shared service reachable and dispatch-ready? What has its own process counted?',
        'Health is not active work, a loaded model, successful tasks or deployed quality.')
  for(const [key,label,source] of [['health','Health','z0_health'],['readiness','Readiness','z0_readiness'],['bridge_capabilities','Bridge capabilities','z0_bridge']]){
    add('service:'+key,label,'services',[source],'Inspect the existing shared-service GET contract.',
        'Advertised support/readiness does not establish harness consumption or permission.',service[key]||{})
  }
  add('service:metrics','Service counters','services',['z0_metrics'],'Which dispatch/admission counters are observed?',
      'Process-lifetime counters only; reads can affect connection counters. Not cost, task totals or quality.',{},
      service.metrics?service.metrics.length:null)
  rows('service:metrics',service.metrics,r=>'metric:'+r.metric+':'+(r.provider||'')+':'+(r.http_status||''),
       r=>r.metric.replace('z0intelligence_','')+(r.provider?' · '+r.provider:''),['z0_metrics'],
       'Inspect one owner-reported counter or gauge and its labels.', 'No inferred savings, rate, completed task or cross-process join.')
  group('resources','Resources',['host_metadata','k8s','z0_capacity'],
        'Which storage or workload readiness constraints need attention?',
        'Current kube context and optional host export are independent inventories, not joined hosts.')
  for(const [label,data] of Object.entries(s.disks||{}))add('disk:'+label,label+' storage','resources',['host_metadata'],
        'Inspect free space and pressure at the configured mount.', 'Storage pressure alone says nothing about task or inference quality.',data)
  add('permissions','Environment permissions','resources',['host_metadata'],'Are environment files writable by other users?',
      'Metadata-only check; contents and filenames are never exposed. Not a complete security audit.',s.security||{})
  add('pods','Kubernetes pods','resources',['k8s'],'Which pods are not ready?',
      'Bounded current-context projection; a running pod is not necessarily ready.',k.coverage||{},k.available?(k.pods||[]).length:null)
  rows('pods',k.pods,r=>'pod:'+r.namespace+':'+r.name,r=>r.name||'unknown pod',['k8s'],
       'Inspect pod phase, Ready condition and restart evidence.', 'Opaque names preserve privacy; no task/agent linkage is asserted.')
  add('kube-nodes','Kubernetes nodes','resources',['k8s'],'Which current-context nodes report Ready?',
      'Kubernetes node identities are not joined to the optional host export.',k.coverage||{},k.available?(k.nodes||[]).length:null)
  rows('kube-nodes',k.nodes,r=>r.name?'kube-node:'+r.name:null,r=>r.name,['k8s'],
       'Inspect the node Ready condition from the existing inventory.', 'Ready is workload-substrate evidence, not model capability or task quality.')
  add('hosts','Hosts and devices','resources',['z0_capacity'],'Which hosts have observed resources?',
      'Optional source-owned export; absent export means unknown inventory.',cp.coverage||{},s.capacity_plane?(cp.hosts||[]).length:null)
  rows('hosts',cp.hosts,r=>r.host_id?'host:'+r.host_id:null,r=>r.label||r.host_id,['z0_capacity'],
       'Inspect the producer-observed host resource vector.', 'Reachability is not migratability or semantic capability.')
  add('sessions','Sessions','resources',['z0_capacity'],'Which sessions did the Tern export observe?',
      'No process/session join is inferred. Sessions stay sticky and non-migratable.',{},s.capacity_plane?(cp.sessions||[]).length:null)
  rows('sessions',cp.sessions,r=>r.session_id?'session:'+r.session_id:null,r=>r.name||r.session_id,['z0_capacity'],
       'Inspect producer-reported session state.', 'Attached does not imply working, governed or safely migratable.')
  group('capacity','Capacity',['z0_providers','z0_capacity'],'What admission headroom is known, separately from quota?',
        'Provider inflight/cap is not remaining tokens, rate quota, budget, or semantic eligibility.',{},service.providers?service.providers.length:null)
  rows('capacity',service.providers,r=>'provider:'+r.provider,r=>r.provider,['z0_providers'],
       'Inspect in-flight admission, cap, cooldown and the source reason.', 'Unprobed availability is not a successful provider call. Quota remains unknown here.')
  add('offers','Capacity offers','capacity',['z0_capacity'],'Which source-owned capacity offers are published?',
      'Optional and unqualified export; stale/reset remaining quota is withheld.',cp.coverage||{},s.capacity_plane?(cp.offers||[]).length:null)
  rows('offers',cp.offers,r=>r.offer_id?'offer:'+r.offer_id:null,r=>r.provider||r.actor_id||r.offer_id,['z0_capacity'],
       'Inspect dimensional quota/resources and observation time.', 'Different quota dimensions must not be combined into a single remaining score.')
  add('leases','Placement leases','capacity',['z0_capacity'],'Are placement references observable?',
      'lease / shadow activation unknown; a placement recommendation grants no execution authority.',{},s.capacity_plane?(cp.leases||[]).length:null)
  rows('leases',cp.leases,r=>r.placement_id?'lease:'+r.placement_id:null,r=>r.placement_id,['z0_capacity'],
       'Inspect a producer-owned placement reference.', 'No task or admission is inferred from this optional projection.')
  group('work','Work & authority',['z0'],'Which task and authority stages are actually joined?',
        'The inspected shared GET contracts do not expose the #47/#54 selected-work read model.',s.control||{})
  add('cluster:tasks','Cluster task registry','work',['hermes_cluster'],'What task states does the existing cluster registry report?',
      'Registry-only counts, not all local work. Completed is not independently verified. Blocked/cancelled states are not reported by this endpoint; do not infer zero.',
      s.hermes_cluster||{},s.hermes_cluster?.task_count??null)
  for(const label of ['Objective / tracker','AODL','Placement','Dispatch','Admission','Execution','Verification']){
    add('stage:'+label,label,'work',['z0'],'Inspect the source requirement for this work stage.',
        'Unobserved. Requires owner-bound task/trace/attempt, revision and consumer evidence; process health is not authority.',
        {state:'unknown',next_action:'source-owner read-contract integration; do not synthesize an episode'})
  }
  group('cognition','Cognition',['z0_bridge','memory'],'What can the bridge describe, and what consumer use is qualified?',
        'Protocol support is separate from loaded models, model input, use and independent behavior.',service.bridge_capabilities||{})
  rows('cognition',service.bridge_capabilities?.endpoints,r=>r.path?'protocol:'+r.path:null,r=>r.path,['z0_bridge'],
       'Inspect advertised endpoint semantics, without calling it.', 'Shadow mode can still perform physical model execution. CompanyOS never invokes these endpoints.')
  add('memory','Memory / reuse','cognition',['memory'],'Is useful continuity qualified for this consumer?',
      'Archive availability, retrieval, model-visible injection, use and verification are separate; no automatic activation.',s.memory||{})
  group('evidence','Evidence coverage',['z0_outcomes'],'Which expected outcome windows are missing or incomplete?',
        'AgentWeb registered expectations only, not all z0 work. as_of is assessment time, not latest evidence.',service.outcome_coverage||{},service.outcome_coverage?.expectations??null)
  for(const w of ['1h','24h','7d'])add('window:'+w,w+' outcome window','evidence',['z0_outcomes'],
        'Inspect eligible denominator, observed/complete/missing counts and source gate reasons.',
        'Coverage is necessary, not sufficient for causal quality; a null ratio is not zero.',service.outcome_coverage?.by_window?.[w]||{})
  group('evaluation','Evaluation',['z0_evaluation'],'Is any registered experiment ready for human review?',
        'Review readiness is not causal quality, deployment acceptance, or promotion permission.',service.randomized_evidence||{},service.randomized_evidence?.coverage?.total??null)
  rows('evaluation',service.randomized_evidence?.experiments,r=>r.experiment_ref?'experiment:'+r.experiment_ref:null,r=>r.experiment_ref,['z0_evaluation'],
       'Inspect source-owned sample gates and review prerequisites.', 'Metric effects, treatment hashes and free-text reasons are intentionally omitted; no global model score.')
  group('economics','Economics',['tokenomics'],'What measured usage, cost and verified work can be credited?',
        'Canonical Tokenomics window/join is unavailable; service metrics cannot substitute for it.',s.economics||{})
  group('sources','Sources & gaps',Object.keys(src).length?Object.keys(src):['projection'],
        'Which exact input is missing, stale, bounded or only partially qualified?',
        'Fresh HTTP transport and a response hash do not attest the loaded producer revision.',s.coverage||{},Object.keys(src).length||null)
  for(const [name,data] of Object.entries(src))add('source:'+name,name,'sources',[name],
      'Inspect source status, origin, times, revision, coverage and blocker.', 'Availability, freshness, coverage and qualification are independent.',data)
  const summaries={agents:count(nodes.agents.observedCount)+' process matches',services:'Dispatch readiness '+str(service.readiness?.ok),
    resources:'Independent host / kube inventories',capacity:count(nodes.capacity.observedCount)+' provider admission rows',
    work:'Authority join unknown · cluster registry separate',cognition:service.bridge_capabilities?'Protocol advertised · consumer use unqualified':'Protocol not observed · consumer use unknown',
    evidence:count(nodes.evidence.observedCount)+' registered expectations',evaluation:count(nodes.evaluation.observedCount)+' registered experiments',
    economics:'Measured cost '+money(s.economics?.observed_cost_usd),sources:count(nodes.sources.observedCount)+' source inputs'}
  const metricUnits={dispatch_active:'current dispatches',dispatch_peak:'peak concurrent dispatches',provider_inflight:'current provider admissions',
    provider_cap:'provider admission cap',provider_unhealthy:'unhealthy flag (0 / 1)'}
  for(const n of Object.values(nodes)){
    n.summary=summaries[n.id]||(n.observedCount==null?'State / coverage detail':count(n.observedCount)+' observed')
    if(n.data.metric){
      const key=n.data.metric.replace('z0intelligence_',''),unit=metricUnits[key]||(key.endsWith('_seconds_sum')?'cumulative seconds':'process-lifetime count')
      n.summary=count(n.data.value)+' · '+unit
      n.data={...n.data,unit}
    }
  }
  return {nodes,root:'network'}
}

export {buildInspectionModel};
