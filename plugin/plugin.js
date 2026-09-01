/**
 * Company OS HUD — thin Hermes projection.
 * Visual language: Kevin's cockpit reference.
 * Nodes: Voice, First Mate, Linear, Kanban, Third Mate, OSS, Host (PER-299 v3).
 * Disk door: $HERMES_HOME/desktop-plugins/company-os/plugin.js
 */
import {
  host,
  useValue,
  ROUTES_AREA,
  SIDEBAR_NAV_AREA,
  PALETTE_AREA
} from '@hermes/plugin-sdk'
import { jsx, jsxs } from 'react/jsx-runtime'

const ID = 'company-os'

const CSS = [
  '.cos{position:absolute;inset:0;background:#0a0a0a;color:#e8e8e8;font-family:ui-sans-serif,system-ui,sans-serif;overflow:hidden;letter-spacing:.04em}',
  '.cos *{box-sizing:border-box}',
  '.cos-top{display:grid;grid-template-columns:1fr 1fr 1fr;padding:28px 40px 0;align-items:start}',
  '.cos-brand{font-family:ui-monospace,Menlo,monospace;font-size:26px;letter-spacing:.14em}',
  '.cos-sub{color:#888;font-size:11px;letter-spacing:.22em;text-transform:lowercase;margin-top:6px}',
  '.cos-status{color:#7dff9a;font-size:12px;margin-top:12px;display:flex;align-items:center;gap:8px}',
  '.cos-dot{width:7px;height:7px;border-radius:50%;background:#7dff9a}',
  '.cos-clock{text-align:center;font-family:ui-monospace,Menlo,monospace;font-size:18px;letter-spacing:.18em}',
  '.cos-meta{text-align:right;font-size:12px;color:#aaa;letter-spacing:.12em}',
  '.cos-body{display:grid;grid-template-columns:200px 1fr 260px;gap:8px;padding:8px 36px;height:calc(100% - 150px)}',
  '.cos-rail .box{border:1px solid #1c1c1c;padding:14px 12px;margin-bottom:10px;min-height:88px}',
  '.cos-k{font-size:10px;letter-spacing:.28em;color:#9a9a9a;text-transform:uppercase;margin-bottom:8px}',
  '.cos-muted{color:#666;font-size:11px;line-height:1.45}',
  '.cos-stage{position:relative}',
  '.cos-hub{position:absolute;left:50%;top:46%;transform:translate(-50%,-50%);text-align:center}',
  '.cos-ring{width:210px;height:210px;border-radius:50%;border:1px dashed #2a2a2a;margin:0 auto;display:flex;align-items:center;justify-content:center}',
  '.cos-core{width:70px;height:70px;border-radius:50%;background:#f0f0f0}',
  '.cos-core.busy{box-shadow:0 0 28px rgba(125,255,154,.45)}',
  '.cos-hubname{margin-top:10px;letter-spacing:.32em;font-size:12px}',
  '.cos-sat{position:absolute;font-size:10px;letter-spacing:.22em;color:#9a9a9a;text-transform:uppercase}',
  '.cos-sat.top{left:50%;top:8%;transform:translateX(-50%)}',
  '.cos-sat.bot{left:50%;bottom:10%;transform:translateX(-50%)}',
  '.cos-sat.left{left:8%;top:48%}',
  '.cos-lane{border:1px solid #1c1c1c;padding:14px;margin-bottom:10px}',
  '.cos-bottom{display:grid;grid-template-columns:1fr 1.4fr 1fr;gap:16px;padding:0 36px 20px;align-items:end}',
  '.cos-prompt{border:1px solid #2a2a2a;border-radius:28px;padding:12px 16px;display:flex;justify-content:space-between;align-items:center;color:#777;font-size:13px}',
  '.cos-stat{display:flex;justify-content:space-between;font-size:11px;color:#888;margin:4px 0;letter-spacing:.12em}'
].join('\n')

function str(v) {
  if (v == null || v === '') return '—'
  if (typeof v === 'string') return v
  if (typeof v === 'object') {
    if (typeof v.connected === 'boolean') return v.connected ? 'connected' : 'offline'
    if (v.name) return String(v.name)
    if (v.id) return String(v.id)
  }
  return String(v)
}

function clock() {
  try {
    return new Date().toLocaleTimeString('en-GB', { hour12: false })
  } catch {
    return '—'
  }
}

function Hud() {
  const busy = useValue(host.state.busy)
  const model = useValue(host.state.model)
  const profile = useValue(host.state.profile)
  const gateway = useValue(host.state.gateway)
  const cwd = useValue(host.state.cwd)

  return jsxs('div', {
    className: 'cos',
    children: [
      jsx('style', { children: CSS }),
      jsxs('div', {
        className: 'cos-top',
        children: [
          jsxs('div', {
            children: [
              jsx('div', { className: 'cos-brand', children: 'zer0' }),
              jsx('div', { className: 'cos-sub', children: 'company os' }),
              jsxs('div', {
                className: 'cos-status',
                children: [
                  jsx('span', { className: 'cos-dot' }),
                  busy ? 'busy' : 'idle'
                ]
              })
            ]
          }),
          jsxs('div', {
            className: 'cos-clock',
            children: [
              jsx('div', { children: clock() }),
              jsx('div', { className: 'cos-sub', children: str(profile) })
            ]
          }),
          jsxs('div', {
            className: 'cos-meta',
            children: [
              jsx('div', { children: str(model) }),
              jsx('div', { className: 'cos-sub', children: 'gateway ' + str(gateway) })
            ]
          })
        ]
      }),
      jsxs('div', {
        className: 'cos-body',
        children: [
          jsxs('div', {
            className: 'cos-rail',
            children: [
              jsxs('div', {
                className: 'box',
                children: [
                  jsx('div', { className: 'cos-k', children: 'voice' }),
                  jsx('div', { children: 'intake gateway' }),
                  jsx('div', { className: 'cos-muted', children: 'raw · verbatim · never executable' })
                ]
              }),
              jsxs('div', {
                className: 'box',
                children: [
                  jsx('div', { className: 'cos-k', children: 'first mate' }),
                  jsx('div', { children: 'chief of staff' }),
                  jsx('div', { className: 'cos-muted', children: 'one Linear brief · no canary claim' })
                ]
              }),
              jsxs('div', {
                className: 'box',
                children: [
                  jsx('div', { className: 'cos-k', children: 'hitl' }),
                  jsx('div', { children: 'Kevin' }),
                  jsx('div', { className: 'cos-muted', children: 'PER-n YES/NO · voice brief Backlog→Todo' })
                ]
              })
            ]
          }),
          jsxs('div', {
            className: 'cos-stage',
            children: [
              jsx('div', { className: 'cos-sat top', children: 'hitl' }),
              jsx('div', { className: 'cos-sat left', children: 'mcp' }),
              jsxs('div', {
                className: 'cos-hub',
                children: [
                  jsx('div', {
                    className: 'cos-ring',
                    children: jsx('div', { className: busy ? 'cos-core busy' : 'cos-core' })
                  }),
                  jsx('div', { className: 'cos-hubname', children: 'LINEAR' }),
                  jsx('div', { className: 'cos-muted', children: 'company mind' })
                ]
              }),
              jsx('div', { className: 'cos-sat bot', children: 'kanban' })
            ]
          }),
          jsxs('div', {
            children: [
              jsxs('div', {
                className: 'cos-lane',
                children: [
                  jsx('div', { className: 'cos-k', children: 'product' }),
                  jsx('div', { children: 'third mate' }),
                  jsx('div', { className: 'cos-muted', children: 'one owner per product' })
                ]
              }),
              jsxs('div', {
                className: 'cos-lane',
                children: [
                  jsx('div', { className: 'cos-k', children: 'oss lane' }),
                  jsx('div', { children: 'frontier harnesses' }),
                  jsx('div', { className: 'cos-muted', children: 'omp · o8 · hermes · pi · codex' })
                ]
              }),
              jsxs('div', {
                className: 'cos-lane',
                children: [
                  jsx('div', { className: 'cos-k', children: 'host' }),
                  jsx('div', { children: 'second mate' }),
                  jsx('div', { className: 'cos-muted', children: 'local Kanban on this machine' })
                ]
              })
            ]
          })
        ]
      }),
      jsxs('div', {
        className: 'cos-bottom',
        children: [
          jsxs('div', {
            children: [
              jsx('div', { className: 'cos-k', children: 'cwd' }),
              jsx('div', { className: 'cos-muted', children: str(cwd) })
            ]
          }),
          jsxs('div', {
            className: 'cos-prompt',
            children: [
              jsx('span', { children: 'ask your company anything…' }),
              jsx('span', { children: '↑' })
            ]
          }),
          jsxs('div', {
            children: [
              jsxs('div', {
                className: 'cos-stat',
                children: ['profile', jsx('span', { children: str(profile) })]
              }),
              jsxs('div', {
                className: 'cos-stat',
                children: ['model', jsx('span', { children: str(model) })]
              }),
              jsxs('div', {
                className: 'cos-stat',
                children: ['gateway', jsx('span', { children: str(gateway) })]
              })
            ]
          })
        ]
      })
    ]
  })
}

export default {
  id: ID,
  name: 'Company OS',
  defaultEnabled: true,
  register(ctx) {
    ctx.register({
      id: 'page',
      area: ROUTES_AREA,
      data: { path: '/company-os' },
      render: function () {
        return jsx(Hud, {})
      }
    })
    ctx.register({
      id: 'nav',
      area: SIDEBAR_NAV_AREA,
      order: 58,
      data: { path: '/company-os', label: 'Company OS', codicon: 'dashboard' }
    })
    ctx.register({
      id: 'open',
      area: PALETTE_AREA,
      data: {
        id: 'company-os.open',
        label: 'Open Company OS',
        run: function () {
          host.navigate('/company-os')
        }
      }
    })
  }
}
