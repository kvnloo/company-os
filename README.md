# Company OS

Thin **Hermes** HUD. Not a company operating system, not a second Kanban, not Linear.

It is a cockpit that **reads** live Hermes state and draws the Company OS map (voice → first mate → Linear/human mind as a label → local Kanban as Hermes execution). Hermes remains the runtime. You remain the approver.

## What it is

- Hermes Desktop plugin (`plugin/plugin.js`) — full page at `/company-os`
- Optional static `web/index.html` for the same look without Desktop (demo numbers only)

## What it is not

- A control plane, issue tracker, or worker dispatcher
- A Linear client (no Linear tokens)
- A place for secrets, health data, or credentials

## Install (Desktop)

```bash
curl -fsSL https://raw.githubusercontent.com/kvnloo/company-os/main/scripts/install.sh | bash
```

Or from a clone:

```bash
./scripts/install.sh
```

Then in Hermes Desktop: **⌘K → Reload desktop plugins** → sidebar **Company OS**.

`HERMES_HOME` defaults to `~/.hermes`. Named profiles use that profile's home.

## How it connects

The plugin only uses the documented Desktop SDK:

- `host.state` — `busy`, `model`, `profile`, `gateway`, `cwd`, focused session
- `host.request('session.list')` when available — session count, never task bodies
- `host.navigate`, `host.notify`

If an RPC is missing, the HUD still paints from `host.state`. It never writes Kanban or Linear.

## License

MIT
