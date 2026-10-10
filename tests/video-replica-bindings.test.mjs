import { test } from 'node:test';
import assert from 'node:assert/strict';
import { issueBindings, acceptSourceBinding, fixture } from '../web/video-replica/bindings.mjs';
test('reference content is isolated from the issue-defined adapter seam',()=>{
  assert.equal(fixture.mode,'reference-fixture');
  assert.equal(fixture.initialFrameSeconds,0);
  assert.equal(issueBindings.length,7);
  assert.equal(issueBindings.find(x=>x.id==='rings').widget,'ObjectiveRing / ReadinessBand');
  assert.throws(()=>acceptSourceBinding('rings',fixture),/source-bound/);
  assert.throws(()=>acceptSourceBinding('rings',{mode:'source-bound',value:77}),/provenance/);
  const unknown={mode:'source-bound',status:'unknown',value:null,sourceRefs:['canonical:test'],observedAt:'2026-10-10T00:00:00Z',unit:'percent',denominator:null};
  assert.equal(acceptSourceBinding('rings',unknown).value,null);
  assert.equal(acceptSourceBinding('metrics',{...unknown,value:0,unit:'count',status:'observed'}).value,0);
  assert.equal(acceptSourceBinding('metrics',{...unknown,value:false,unit:'boolean',status:'observed'}).value,false);
  assert.throws(()=>acceptSourceBinding('rings',{...unknown,value:77,status:'observed'}),/denominator/);
  assert.equal(acceptSourceBinding('rings',{...unknown,value:77,status:'observed',denominator:100}).value,77);
  assert.throws(()=>acceptSourceBinding('invented',unknown),/Unknown/);
});
