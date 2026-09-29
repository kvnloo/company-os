/**
 * Company OS — live read-only projection of the local z0 network.
 */
import {
  host,
  useValue,
  ROUTES_AREA,
  SIDEBAR_NAV_AREA,
  PALETTE_AREA
} from '@hermes/plugin-sdk'
import { useEffect, useState } from 'react'
import { jsx, jsxs } from 'react/jsx-runtime'

const ID = 'company-os'
const POLL_MS = 2000

const CSS = [
  '.cos{position:absolute;inset:0;background:#090909;color:#e8e8e8;font-family:ui-sans-serif,system-ui,sans-serif;overflow:auto;letter-spacing:.04em}',
  '.cos *{box-sizing:border-box}',
  '.cos-top{display:grid;grid-template-columns:1fr 1fr 1fr;padding:24px 30px 12px;border-bottom:1px solid #181818;align-items:start}',
  '.cos-brand{font-family:ui-monospace,Menlo,monospace;font-size:24px;letter-spacing:.16em}',
  '.cos-sub{color:#777;font-size:10px;letter-spacing:.14em;margin-top:5px}',
  '.cos-clock{text-align:center;font-family:ui-monospace,Menlo,monospace;font-size:16px;letter-spacing:.14em}',
  '.cos-meta{text-align:right;font-size:10px;color:#999;line-height:1.7}',
  '.cos-status{margin-top:8px;font-size:10px;display:flex;align-items:center;gap:7px}',
  '.cos-dot{width:7px;height:7px;border-radius:50%;background:#7dff9a;box-shadow:0 0 12px rgba(125,255,154,.35)}',
  '.cos-dot.warn{background:#f2cf72;box-shadow:none}.cos-dot.bad{background:#ff8c72;box-shadow:none}',
  '.cos-grid{display:grid;grid-template-columns:230px minmax(460px,1fr) 300px;gap:10px;padding:12px 28px 0}',
  '.cos-panel{border:1px solid #1e1e1e;background:#0c0c0c;padding:12px;min-height:92px}',
  '.cos-k{font-size:9px;letter-spacing:.24em;color:#8b8b8b;text-transform:uppercase;margin-bottom:8px}',
  '.cos-row{display:flex;justify-content:space-between;gap:12px;font-size:10px;margin:5px 0;align-items:baseline}',
  '.cos-val{font-family:ui-monospace,Menlo,monospace;color:#ddd;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}',
  '.cos-muted{color:#666;font-size:9px;line-height:1.45}.cos-ok{color:#7dff9a}.cos-warn{color:#f2cf72}.cos-bad{color:#ff8c72}',
  '.cos-flow{min-height:380px;border:1px solid #1e1e1e;background:radial-gradient(circle at 50% 34%,#111 0,#0b0b0b 44%,#090909 75%);padding:16px}',
  '.cos-pipe{display:grid;grid-template-columns:repeat(5,1fr);gap:6px;margin:10px 0 18px}',
  '.cos-node{border:1px solid #292929;padding:9px 6px;text-align:center;font-size:9px;letter-spacing:.15em;position:relative}',
  '.cos-node.live{border-color:#395b40}.cos-node.live:after{content:"";position:absolute;width:5px;height:5px;border-radius:50%;background:#7dff9a;right:5px;top:5px;animation:pulse 1.2s infinite}',
  '@keyframes pulse{0%,100%{opacity:.25;transform:scale(.75)}50%{opacity:1;transform:scale(1.2)}}',
  '.cos-stream{height:270px;overflow:hidden;border-top:1px solid #171717;padding-top:7px}',
  '.cos-event{display:grid;grid-template-columns:62px 72px 1fr 105px 58px;gap:7px;padding:5px 1px;border-bottom:1px solid #151515;font-size:9px;font-family:ui-monospace,Menlo,monospace}',
  '.cos-event:first-child{animation:arrive .45s ease-out}@keyframes arrive{from{opacity:.2;transform:translateY(-5px)}to{opacity:1;transform:none}}',
  '.cos-tag{border:1px solid #242424;padding:1px 4px;overflow:hidden;text-overflow:ellipsis;white-space:nowrap}',
  '.cos-list{max-height:190px;overflow:hidden}.cos-cap{padding:7px 0;border-bottom:1px solid #171717}',
  '.cos-bar{height:2px;background:#191919;margin-top:5px}.cos-bar>i{display:block;height:100%;background:#7dff9a;opacity:.65}',
  '.cos-foot{display:grid;grid-template-columns:repeat(5,1fr);gap:10px;padding:10px 28px 22px}',
  '.cos-metric{border:1px solid #1e1e1e;padding:11px}.cos-num{font-family:ui-monospace,Menlo,monospace;font-size:18px}',
  '.cos-sources{display:flex;gap:5px;flex-wrap:wrap}.cos-source{border:1px solid #222;padding:3px 5px;font-size:8px;text-transform:uppercase}',
  '.cos-source.ok{border-color:#29442e;color:#7dff9a}.cos-source.degraded,.cos-source.missing{color:#f2cf72}.cos-source.unavailable{color:#777}'
].join('\n')

const str = v => (v == null || v === '' ? '—' : String(v))
const short = (v,n=18) => { const s=str(v); return s.length>n ? s.slice(0,n-1)+'…' : s }
const count = v => Number.isFinite(Number(v)) ? Number(v).toLocaleString() : '—'
const money = v => Number.isFinite(Number(v)) ? '$'+Number(v).toFixed(Number(v)<1?4:2) : '—'
function t(v){try{const d=typeof v==='number'&&v<1e12?new Date(v*1000):new Date(v);return d.toLocaleTimeString('en-GB',{hour12:false})}catch{return '—'}}
function cls(v){return v==='ok'||v==='running'?'cos-ok':v==='failed'||v==='critical'||v==='offline'?'cos-bad':'cos-warn'}

function useProjection(ctx){
  const [snap,setSnap]=useState(null)
  const [err,setErr]=useState(null)
  useEffect(()=>{
    let alive=true
    const load=async()=>{
      try{const next=await ctx.rest('/snapshot');if(alive){setSnap(next);setErr(null)}}catch(e){if(alive)setErr(e?.message||'projection unavailable')}
    }
    load()
    const cancel=ctx.setInterval(load,POLL_MS)
    return()=>{alive=false;cancel()}
  },[ctx])
  return [snap,err]
}

function firstRemaining(q={}){
  for(const v of [q.remaining_free_quota,q.remaining_tokens,q.remaining,q.day_tokens_remaining]) if(Number.isFinite(Number(v))) return Number(v)
  for(const v of Object.values(q.dimensions||{})) if(v&&Number.isFinite(Number(v.remaining))) return Number(v.remaining)
  return null
}
function firstLimit(q={}){
  for(const v of [q.limit,q.daily_limit,q.day_tokens_limit]) if(Number.isFinite(Number(v))) return Number(v)
  for(const v of Object.values(q.dimensions||{})) if(v&&Number.isFinite(Number(v.limit))) return Number(v.limit)
  return null
}

function Panel({title,children}){return jsxs('div',{className:'cos-panel',children:[jsx('div',{className:'cos-k',children:title}),children]})}

function Hud({ctx}){
  const busy=useValue(host.state.busy)
  const model=useValue(host.state.model)
  const profile=useValue(host.state.profile)
  const gateway=useValue(host.state.gateway)
  const cwd=useValue(host.state.cwd)
  const [s,err]=useProjection(ctx)
  const fleet=s?.fleet||[]
  const flow=s?.flow||[]
  const caps=s?.capacity||[]
  const k=s?.k8s||{}
  const mem=s?.memory||{}
  const econ=s?.economics||{}
  const disks=s?.disks||{}
  const status=err?'offline':(s?.status||'loading')
  const live=Boolean(busy||flow.length)

  return jsxs('div',{className:'cos',children:[
    jsx('style',{children:CSS}),
    jsxs('div',{className:'cos-top',children:[
      jsxs('div',{children:[
        jsx('div',{className:'cos-brand',children:'zer0'}),
        jsx('div',{className:'cos-sub',children:'company os · live network'}),
        jsxs('div',{className:'cos-status '+cls(status),children:[jsx('span',{className:'cos-dot '+(status==='offline'?'bad':status==='degraded'?'warn':'')}),status]})
      ]}),
      jsxs('div',{className:'cos-clock',children:[jsx('div',{children:t(Date.now())}),jsx('div',{className:'cos-sub',children:str(profile)})]}),
      jsxs('div',{className:'cos-meta',children:[jsx('div',{children:str(model)}),jsx('div',{children:'gateway '+str(gateway)}),jsx('div',{children:'cwd '+short(cwd,34)})]})
    ]}),
    jsxs('div',{className:'cos-grid',children:[
      jsxs('div',{children:[
        jsx(Panel,{title:'fleet',children:jsxs('div',{children:[
          jsxs('div',{className:'cos-row',children:[jsx('span',{children:'visible'}),jsx('span',{className:'cos-val',children:count(fleet.length)})]}),
          fleet.slice(0,8).map((a,i)=>jsxs('div',{className:'cos-row',children:[
            jsx('span',{children:short(a.harness||a.name||a.capability||'agent',14)}),
            jsx('span',{className:'cos-val '+cls(a.status),children:short(a.status||a.provider||'seen',13)})
          ]},a.trace_id||a.pid||i))
        ]})}),
        jsx('div',{style:{height:10}}),
        jsx(Panel,{title:'substrate',children:jsxs('div',{children:[
          jsxs('div',{className:'cos-row',children:[jsx('span',{children:'k8s nodes'}),jsx('span',{className:'cos-val',children:count((k.nodes||[]).length)})]}),
          jsxs('div',{className:'cos-row',children:[jsx('span',{children:'pods'}),jsx('span',{className:'cos-val',children:count((k.pods||[]).length)})]}),
          jsxs('div',{className:'cos-row',children:[jsx('span',{children:'memory runtime'}),jsx('span',{className:'cos-val '+(mem.runtime_usable?'cos-ok':'cos-warn'),children:mem.runtime_usable?'usable':'degraded'})]}),
          jsxs('div',{className:'cos-row',children:[jsx('span',{children:'sessions'}),jsx('span',{className:'cos-val',children:count(mem.sessions)})]}),
          mem.home_symlink?jsx('div',{className:'cos-muted cos-warn',children:'AgentsView root is symlink → '+short(mem.symlink_target,30)}):null
        ]})})
      ]}),
      jsxs('div',{className:'cos-flow',children:[
        jsx('div',{className:'cos-k',children:'data flow'}),
        jsx('div',{className:'cos-pipe',children:['AODL','PLACE','LEASE','EXEC','VERIFY'].map((x,i)=>jsx('div',{className:'cos-node '+(live&&i<=(flow[0]?.verified?4:3)?'live':''),children:x},x))}),
        jsx('div',{className:'cos-stream',children:flow.slice(0,13).map((e,i)=>jsxs('div',{className:'cos-event',children:[
          jsx('span',{children:t(e.ts)}),
          jsx('span',{className:'cos-tag',children:short(e.harness||'—',11)}),
          jsx('span',{children:short(e.capability||e.trace_id||'event',31)}),
          jsx('span',{children:short((e.provider||'')+(e.model?' / '+e.model:''),19)}),
          jsx('span',{className:e.verified===true?'cos-ok':cls(e.status),children:e.verified===true?'verified':short(e.status||'seen',9)})
        ]},(e.trace_id||'e')+'-'+i))})
      ]}),
      jsxs('div',{children:[
        jsx(Panel,{title:'provider capacity',children:jsxs('div',{children:[
          caps.slice(0,9).map((r,i)=>{const rem=firstRemaining(r.quota||{}),lim=firstLimit(r.quota||{}),pct=rem!=null&&lim>0?Math.max(0,Math.min(100,rem/lim*100)):0;return jsxs('div',{className:'cos-cap',children:[
            jsxs('div',{className:'cos-row',children:[jsx('span',{children:short(r.provider||'provider',13)}),jsx('span',{className:'cos-val',children:rem==null?'unknown':count(rem)})]}),
            jsx('div',{className:'cos-muted',children:short(r.model||'—',30)}),
            jsx('div',{className:'cos-bar',children:jsx('i',{style:{width:pct+'%'}})})
          ]},(r.provider||'p')+'-'+(r.model||i))}),
          caps.length===0?jsx('div',{className:'cos-muted',children:'quota ledger not yet observed'}):null
        ]})}),
        jsx('div',{style:{height:10}}),
        jsx(Panel,{title:'source health',children:jsxs('div',{children:[
          jsx('div',{className:'cos-sources',children:Object.entries(s?.sources||{}).map(([n,v])=>jsx('span',{className:'cos-source '+str(v?.status),title:v?.reason||'',children:n+':'+str(v?.status)},n))}),
          disks.home?jsx('div',{className:'cos-row',children:[jsx('span',{children:'home free'}),jsx('span',{className:'cos-val '+cls(disks.home.status),children:disks.home.free_pct+'%'})]}):null,
          disks.mnt?jsx('div',{className:'cos-row',children:[jsx('span',{children:'/mnt free'}),jsx('span',{className:'cos-val '+cls(disks.mnt.status),children:disks.mnt.free_pct+'%'})]}):null
        ]})})
      ]})
    ]}),
    jsxs('div',{className:'cos-foot',children:[
      jsx('div',{className:'cos-metric',children:jsxs('div',{children:[jsx('div',{className:'cos-k',children:'tokens observed'}),jsx('div',{className:'cos-num',children:count(econ.actual_tokens)})]})}),
      jsx('div',{className:'cos-metric',children:jsxs('div',{children:[jsx('div',{className:'cos-k',children:'cached input'}),jsx('div',{className:'cos-num',children:count(econ.cached_input_tokens)})]})}),
      jsx('div',{className:'cos-metric',children:jsxs('div',{children:[jsx('div',{className:'cos-k',children:'observed cost'}),jsx('div',{className:'cos-num',children:money(econ.observed_cost_usd)})]})}),
      jsx('div',{className:'cos-metric',children:jsxs('div',{children:[jsx('div',{className:'cos-k',children:'verified'}),jsx('div',{className:'cos-num',children:count(econ.verified_events)})]})}),
      jsx('div',{className:'cos-metric',children:jsxs('div',{children:[jsx('div',{className:'cos-k',children:'governed events'}),jsx('div',{className:'cos-num',children:count(econ.governed_events)})]})})
    ]})
  ]})
}

export default {
  id: ID,
  name: 'Company OS',
  defaultEnabled: true,
  register(ctx) {
    ctx.register({id:'page',area:ROUTES_AREA,data:{path:'/company-os'},render:()=>jsx(Hud,{ctx})})
    ctx.register({id:'nav',area:SIDEBAR_NAV_AREA,order:58,data:{path:'/company-os',label:'Company OS',codicon:'dashboard'}})
    ctx.register({id:'open',area:PALETTE_AREA,data:{id:'company-os.open',label:'Open Company OS',run:()=>host.navigate('/company-os')}})
  }
}
