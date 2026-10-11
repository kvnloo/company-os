import test from 'node:test';
import assert from 'node:assert/strict';
import {existsSync} from 'node:fs';

const moduleURL = new URL('../web/motion-lab/model.mjs', import.meta.url);
test('ephemeral lenses preserve stable selection and restore without persisting source data', async () => {
  const m=await import(moduleURL);
  assert.equal(typeof m.createScene,'function','versioned scene reducer must exist');
  let s=m.createScene();
  s=m.transition(s,{type:'SELECT',id:'z0_outcomes'});
  const base={selected:s.selected,variant:s.variant};
  s=m.transition(s,{type:'ENTER'});
  s=m.transition(s,{type:'VARIANT',id:'focus'});
  s=m.transition(s,{type:'SELECT',id:'hermes_cluster'});
  assert.equal(s.lens.base.selected,base.selected);
  const pinned=m.recipe(s);
  assert.deepEqual(Object.keys(pinned).sort(),['schema','selected','variant']);
  assert.equal(pinned.selected,'hermes_cluster');
  const revision=s.revision;
  assert.throws(()=>m.transition(s,{type:'SELECT',id:'z0',expectedRevision:revision-1}),/stale/i);
  s=m.transition(s,{type:'RESTORE'});
  assert.equal(s.selected,base.selected);assert.equal(s.variant,base.variant);assert.equal(s.lens,null);
  assert.throws(()=>m.transition(s,{type:'SELECT',id:'javascript:alert(1)'}),/unknown/i);
  assert.throws(()=>m.restoreRecipe({...pinned,private:'secret'}),/recipe/i);
  assert.deepEqual(m.restoreRecipe(pinned),pinned);
});
test('a revoked source clears an older comparison anchor', async () => {
  const m=await import(moduleURL);
  assert.equal(typeof m.revalidateAnchor,'function');
  const anchor=m.project({schema:'company_os.snapshot.v1',sources:{z0_readiness:{status:'ok'}},z0_service:{readiness:{max_active:42}}});
  const denied=m.project({schema:'company_os.snapshot.v1',sources:{z0_readiness:{status:'denied'}}});
  assert.equal(m.revalidateAnchor(anchor,denied),null);
  assert.equal(m.revalidateAnchor(anchor,anchor),anchor);
});
test('denied or missing provenance cannot disclose source fields', async () => {
  const {project,bindingFor}=await import(moduleURL);
  for(const sources of [{}, {z0_readiness:{status:'denied',freshness:'fresh'}}]){
    const s=project({schema:'company_os.snapshot.v1',sources,z0_service:{readiness:{ok:true,max_active:919191}}});
    assert.equal(bindingFor(s,'z0_readiness').fields.find(f=>f.path.endsWith('max_active')).value,null);
    assert.equal(JSON.stringify(s).includes('919191'),false);
  }
});
test('snapshot projection binds selection to exact source fields without invented values', async () => {
  assert.ok(existsSync(moduleURL), 'motion model must exist');
  const {project, bindingFor, RINGS, LANES, CARDS} = await import(moduleURL);
  const s=project({schema:'company_os.snapshot.v1',generated_at:123,status:'degraded',sources:{z0_readiness:{status:'ok',freshness:'unknown',observed_at:null,source_version:'sha256:'+'a'.repeat(64)}},z0_service:{readiness:{ok:true,governed_remote_enabled:false,max_active:0,private_prompt:'NEVER-SHOW'}}});
  const b=bindingFor(s,'z0_readiness');
  assert.equal(b.id,'z0_readiness');
  assert.equal(b.fields.find(f=>f.path==='z0_service.readiness.max_active').value,0);
  assert.equal(b.fields.find(f=>f.path==='z0_service.readiness.governed_remote_enabled').value,false);
  assert.equal(b.source.freshness,'unknown');
  assert.equal(b.source.observed_at,null);
  assert.equal(bindingFor(s,'z0_capacity').fields[0].value,null);
  assert.equal(JSON.stringify(s).includes('NEVER-SHOW'),false);
  assert.equal(RINGS.length,10);assert.equal(LANES.length,14);assert.equal(CARDS.length,6);
  assert.equal(new Set(LANES.map(x=>x.id)).size,14);
});
