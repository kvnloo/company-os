/**
 * Company OS — thin Hermes Desktop HUD.
 * Disk door: $HERMES_HOME/desktop-plugins/company-os/plugin.js
 * Plain ESM. No JSX tags. Only @hermes/plugin-sdk + react + react/jsx-runtime.
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
  '.cos{position:absolute;inset:0;background:#080808;color:#ececec;font-family:ui-sans-serif,system-ui,sans-serif;overflow:hidden}',
  '.cos *{box-sizing:border-box}',
  '.cos-top{display:flex;justify-content:space-between;padding:28px 36px 0;font-size:12px;letter-spacing:.16em;text-transform:lowercase;color:#8d8d8d}',
  '.cos-brand{font-family:ui-monospace,monospace;font-size:28px;letter-spacing:.12em;color:#ececec;text-transform:none}',
  '.cos-dot{display:inline-block;width:7px;height:7px;border-radius:50%;background:#7dff9a;margin-right:8px}',
  '.cos-grid{display:grid;grid-template-columns:180px 1fr 280px;gap:12px;padding:12px 36px;height:calc(100% - 88px)}',
  '.cos-card{border:1px solid #1f1f1f;padding:14px;font-size:12px}',
  '.cos-k{color:#8d8d8d;letter-spacing:.2em;font-size:10px;text-transform:uppercase;margin-bottom:8px}',
  '.cos-hub{display:flex;flex-direction:column;align-items:center;justify-content:center;position:relative}',
  '.cos-ring{width:220px;height:220px;border-radius:50%;border:1px dashed #2a2a2a;display:flex;align-items:center;justify-content:center}',
  '.cos-core{width:72px;height:72px;border-radius:50%;background:#f2f2f2}',
  '.cos-core.busy{box-shadow:0 0 24px #7dff9a}',
  '.cos-title{margin-top:12px;letter-spacing:.28em;font-size:12px}',
  '.cos-sub{color:#8d8d8d;font-size:11px;margin-top:4px}',
  '.cos-row{display:flex;justify-content:space-between;margin:6px 0;color:#ececec}',
  '.cos-muted{color:#8d8d8d}'
].join('\n')

function str(v) {
  if (v == null) return '—'
  if (typeof v === 'string') return v
  if (typeof v === 'object') {
    if (v.connected != null) return v.connected ? 'connected' : 'offline'
    if (v.name) return String(v.name)
    try {
      return JSON.stringify(v)
    } catch {
      return '—'
    }
  }
  return String(v)
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
              jsx('div', { children: 'company os' }),
              jsxs('div', {
                style: { marginTop: 10, color: '#7dff9a' },
                children: [
                  jsx('span', { className: 'cos-dot' }),
                  busy ? 'busy' : 'idle'
                ]
              })
            ]
          }),
          jsxs('div', {
            style: { textAlign: 'right' },
            children: [
              jsx('div', { children: str(profile) }),
              jsx('div', { children: str(model) })
            ]
          })
        ]
      }),
      jsxs('div', {
        className: 'cos-grid',
        children: [
          jsxs('div', {
            children: [
              jsxs('div', {
                className: 'cos-card',
                children: [
                  jsx('div', { className: 'cos-k', children: 'voice' }),
                  jsx('div', { className: 'cos-muted', children: 'intake is Linear Voice Gateway' }),
                  jsx('div', { className: 'cos-muted', children: 'this plugin does not capture voice' })
                ]
              }),
              jsxs('div', {
                className: 'cos-card',
                style: { marginTop: 12 },
                children: [
                  jsx('div', { className: 'cos-k', children: 'first mate' }),
                  jsx('div', { children: 'chief of staff' }),
                  jsx('div', { className: 'cos-muted', children: 'one Linear brief · no canary claim' })
                ]
              }),
              jsxs('div', {
                className: 'cos-card',
                style: { marginTop: 12 },
                children: [
                  jsx('div', { className: 'cos-k', children: 'cwd' }),
                  jsx('div', { className: 'cos-muted', children: str(cwd) })
                ]
              })
            ]
          }),
          jsxs('div', {
            className: 'cos-hub',
            children: [
              jsx('div', {
                className: 'cos-ring',
                children: jsx('div', { className: busy ? 'cos-core busy' : 'cos-core' })
              }),
              jsx('div', { className: 'cos-title', children: 'LINEAR' }),
              jsx('div', { className: 'cos-sub', children: 'company mind · human ledger' }),
              jsx('div', { className: 'cos-sub', children: 'Hermes Kanban executes underneath' }),
              jsx('div', {
                className: 'cos-sub',
                children: 'gateway ' + str(gateway)
              })
            ]
          }),
          jsxs('div', {
            children: [
              jsxs('div', {
                className: 'cos-card',
                children: [
                  jsx('div', { className: 'cos-k', children: 'product' }),
                  jsx('div', { children: 'third mate' }),
                  jsx('div', { className: 'cos-muted', children: 'one owner per product' })
                ]
              }),
              jsxs('div', {
                className: 'cos-card',
                style: { marginTop: 12 },
                children: [
                  jsx('div', { className: 'cos-k', children: 'oss lane' }),
                  jsx('div', { children: 'frontier harnesses' }),
                  jsx('div', { className: 'cos-muted', children: 'omp · o8 · hermes · pi · codex' })
                ]
              }),
              jsxs('div', {
                className: 'cos-card',
                style: { marginTop: 12 },
                children: [
                  jsx('div', { className: 'cos-k', children: 'host' }),
                  jsx('div', { children: 'second mate' }),
                  jsx('div', { className: 'cos-muted', children: 'local Kanban on this machine' })
                ]
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
