# Company OS

Live, read-only cockpit for the local **z0 network** inside Hermes Desktop.

It keeps the existing dark HUD design, but the values now come from a sanitized local projection of:

- z0intelligence receipts/control state
- active agent/harness processes
- Kubernetes nodes and pods
- Kerdoios provider/quota state
- Tokenomics-style usage/cost fields from canonical receipts
- AgentsView database/runtime health
- local disk pressure

CompanyOS is still **not** the control plane. AODL/z0/Kerdoios/harnesses remain authoritative; CompanyOS only projects what they report.

## Install

```bash
./scripts/install.sh
```

This links:

```text
~/.hermes/desktop-plugins/company-os -> plugin/
~/.hermes/plugins/company-os         -> hermes-plugin/
```

Then restart `hermes dashboard` once if the backend API is new, and in Hermes Desktop use **Reload desktop plugins**.

The projection API is namespaced by Hermes:

```text
GET /api/plugins/company-os/snapshot
GET /api/plugins/company-os/health
```

The Desktop UI polls the snapshot every 2 seconds.

## Truth rules

- Missing data renders as missing/unknown, never zero.
- AgentsView is degraded when its runtime root is a symlink even if the DB itself is readable.
- The browser never receives raw prompts, transcript bodies, credentials, environment secrets, or memory excerpts.
- CompanyOS does not write Linear, Kanban, Kubernetes, z0, Kerdoios, or provider state.
- Calls that cannot be joined to governed receipts should remain visibly ungoverned/unknown rather than receiving z0 savings credit.

## Local overrides

Optional environment variables for unusual layouts:

```text
Z0INT_HOME
HERMES_HOME
AGENTSVIEW_DATA_DIR
COMPANY_OS_AGENTSVIEW_DB
COMPANY_OS_KERDOIOS_LEDGER
COMPANY_OS_Z0_SNAPSHOT
COMPANY_OS_RECEIPTS
```

## Current integration target

See CompanyOS #2 and z0intelligence #47.

The immediate acceptance test is a live trace appearing as:

```text
AODL -> placement -> lease -> execute -> verify
```

alongside the active harness, provider/model, resource capacity, tokens/cost, memory health, and Kubernetes state.

## License

MIT


### AgentsView offload

AgentsView officially supports `AGENTSVIEW_DATA_DIR`. If `~/.agentsview` is a symlink to a large offloaded corpus, do not move the corpus back to `$HOME`. Point AgentsView at the real directory instead:

```bash
export AGENTSVIEW_DATA_DIR=/mnt/zer0models/sft-svlm/data/agentsview
agentsview daemon status
```

CompanyOS uses the same variable, so the memory panel and AgentsView itself agree on the effective data root.


## Security metadata checks

`scripts/doctor.sh` and the projection backend inspect only file **metadata** under `~/.config/environment.d`. They never read configuration contents.

Any group- or world-writable `*.conf` file is treated as critical because variables from that directory can be inherited by the systemd user manager and its units.

For a file that may contain credentials, prefer mode `600`; otherwise `644` is normally sufficient when contents are non-sensitive.

## AgentsView cold start

On this workstation the offloaded archive currently contains thousands of sessions. A cold AgentsView start may spend roughly 100 seconds building/indexing before readiness. A readiness timeout during that window is not sufficient evidence of daemon failure; check daemon/log progress and retry status before classifying the memory plane as down.
