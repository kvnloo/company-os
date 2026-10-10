import assert from 'node:assert/strict';
import test from 'node:test';
import {buildInspectionModel as model} from '../plugin/inspection-model.mjs';

test('standalone adapter exposes ten meaningful groups and stable identity after reorder',()=>{
  const fixture={sources:{processes:{status:'ok'}},fleet:[{pid:42,harness:'omp'},{pid:5,harness:'hermes'}]};
  const a=model(fixture),b=model({...fixture,fleet:[...fixture.fleet].reverse()});
  assert.equal(a.nodes.network.children.length,10);
  assert.equal(a.nodes.agents.observedCount,2);
  assert.equal(a.nodes.work.observedCount,null);
  assert.deepEqual(a.nodes['process:42'],b.nodes['process:42']);
  for(const n of Object.values(a.nodes))assert.ok(n.meaning && n.limitation && n.sources.length);
  assert.equal(model({fleet:[]}).nodes.agents.observedCount,null);
  assert.equal(model({fleet:[],sources:{processes:{status:'ok'}}}).nodes.agents.observedCount,0);
});

test('measured zero, false, absent capacity and unjoined work remain distinct',()=>{
  const m=model({sources:{hermes_cluster:{status:'ok'},z0_metrics:{status:'ok'}},
    hermes_cluster:{node_count:1,task_count:0,tasks_by_status:{running:0}},
    k8s:{available:true,nodes:[{name:'ref-node',ready:false}]},
    flow:[{trace_id:'fixture-not-live',verified:true}],
    z0_service:{metrics:[{metric:'z0intelligence_dispatch_active',value:0}]}});
  assert.equal(m.nodes['cluster:tasks'].observedCount,0);
  assert.equal(m.nodes.work.observedCount,null);
  assert.equal(m.nodes['metric:z0intelligence_dispatch_active::'].summary,'0 · current dispatches');
  assert.equal(m.nodes['kube-node:ref-node'].data.ready,false);
  assert.equal(m.nodes.hosts.observedCount,null);
  assert.equal(m.nodes['stage:Execution'].data.state,'unknown');
  assert.equal(m.nodes['stage:Verification'].data.state,'unknown');
  assert.ok(m.nodes.cognition.summary.includes('not observed'));
});

test('namespace-bound pods and bounded rows do not create inferred identity joins',()=>{
  const m=model({k8s:{pods:[{namespace:'a',name:'same'},{namespace:'b',name:'same'}]},
    fleet:Array.from({length:130},(_,pid)=>({pid}))});
  assert.equal(m.nodes.pods.children.length,2);
  assert.equal(m.nodes['pod:a:same'].data.namespace,'a');
  assert.equal(m.nodes['pod:b:same'].data.namespace,'b');
  assert.equal(m.nodes.agents.children.filter(id=>id.startsWith('process:')).length,100);
});
