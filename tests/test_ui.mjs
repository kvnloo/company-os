import assert from 'node:assert/strict'
import fs from 'node:fs'
import vm from 'node:vm'
import test from 'node:test'

const source = fs.readFileSync(new URL('../plugin/plugin.js', import.meta.url), 'utf8')
async function desktop(snapshot = null, error = null) {
  let state = 0
  const jsx = (type, props, key) => ({type, props: {...props, key}})
  const sdk = {host: {state: {busy: true, model: null, profile: 'diagnostic', gateway: 'unknown', cwd: null}, navigate(){}}, useValue: v => v, ROUTES_AREA: 'routes', SIDEBAR_NAV_AREA: 'nav', PALETTE_AREA: 'palette'}
  const react = {useEffect(){}, useState: initial => [state++ === 0 ? snapshot : state === 2 ? error : typeof initial === 'function' ? initial() : initial, () => {}]}
  const context = vm.createContext({console, Date, document: {getElementById(){return null}}, AbortController, setTimeout, clearTimeout})
  const mod = new vm.SourceTextModule(source + '\nexport {count,money,firstRemaining,firstLimit,bytes,t,resetDetail,buildHierarchy};', {context})
  await mod.link(name => {
    const values = name === '@hermes/plugin-sdk' ? sdk : name === 'react' ? react : {jsx, jsxs: jsx}
    return new vm.SyntheticModule(Object.keys(values), function(){for(const [k,v] of Object.entries(values)) this.setExport(k,v)}, {context})
  })
  await mod.evaluate()
  return mod.namespace
}
function render(node) {
  if (Array.isArray(node)) return node.map(render)
  if (!node || typeof node !== 'object') return node
  if (typeof node.type === 'function') return render(node.type(node.props))
  return {tag: node.type, ...node.props, children: render(node.props?.children)}
}

test('production numeric/time formatters preserve unknown, false, zero and exhaustion', async () => {
  const m = await desktop()
  for (const v of [null, undefined, '', false, {}, '0', NaN]) {
    assert.equal(m.count(v), 'unknown')
    assert.equal(m.money(v), 'unknown')
    assert.equal(m.bytes(v), 'unknown')
  }
  assert.equal(m.count(0), '0')
  assert.equal(m.money(0), '$0.0000')
  assert.equal(m.firstRemaining({remaining: null, remaining_tokens: 0}), 0)
  assert.equal(m.firstRemaining({remaining: null}), null)
  assert.equal(m.firstLimit({limit: null}), null)
  assert.equal(m.t(null), 'unknown')
  assert.equal(m.t('invalid'), 'unknown')
  assert.equal(m.resetDetail({reset_at: null, time_to_reset: null}), 'reset unknown')
})

test('real desktop render cannot light stages from host busy or historical flow', async () => {
  const fixture = {schema: 'company_os.snapshot.v1', status: 'degraded', generated_at: 1,
    flow: [{ts: 1, verified: true, trace_id: 'dispatch-old'}], sources: {}, economics: {observed_cost_usd: null}}
  const m = await desktop(fixture, 'API unavailable')
  const registrations = []
  m.default.register({register: item => registrations.push(item)})
  const tree = render(registrations.find(x => x.area === 'routes').render())
  const text = JSON.stringify(tree)
  assert.ok(!text.includes('cos-node live'))
  assert.ok(text.includes('stale'))
  assert.ok(!text.includes('verified outcome'))
  assert.ok(text.includes('source revision'))
  assert.ok(text.includes('coverage'))
})

test('missing inventory never claims shadow activation or measured fleet zero', async () => {
  const fixture = {schema:'company_os.snapshot.v1', status:'degraded', sources:{processes:{status:'unavailable'}},
    k8s:{available:false}, capacity_plane:null, fleet:[], coverage:{gaps:['shadow_activation_unproven']}}
  const m = await desktop(fixture)
  const hierarchy = JSON.stringify(m.buildHierarchy(fixture, null))
  assert.ok(!hierarchy.includes('shadow only'))
  assert.ok(hierarchy.includes('lease / shadow activation unknown'))
  const registrations=[]
  m.default.register({register:item=>registrations.push(item)})
  const text=JSON.stringify(render(registrations.find(x=>x.area==='routes').render()))
  assert.ok(text.includes('process source unavailable'))
  assert.ok(text.includes('FAIL / DISCARD'))
  assert.ok(text.includes('audit context, not live deployment'))
})

test('shipped browser entry registers the existing HUD through Hermes SDK', () => {
  const registered = [], appended = []
  const context = vm.createContext({window: {
    __HERMES_PLUGIN_SDK__: {sdkVersion: '1.1.0', React: {createElement(){}, useEffect(){}, useState(){}}, fetchJSON(){}},
    __HERMES_PLUGINS__: {register: (...v) => registered.push(v)}
  }, document: {createElement(){return {style:{}}}, currentScript: {parentElement: {appendChild: x => appended.push(x)}}}, console})
  vm.runInContext(fs.readFileSync(new URL('../hermes-plugin/dashboard/dist/index.js', import.meta.url), 'utf8'), context)
  assert.equal(registered.length, 1)
  assert.equal(registered[0][0], 'company-os')
  assert.equal(typeof registered[0][1], 'function')
  assert.equal(appended.length, 0)
})
