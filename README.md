# Company OS

Read-only operational projection for Hermes Desktop **and the Hermes browser dashboard**. Both use the existing dark HUD and the same bounded backend/presentation model. CompanyOS is not a control plane, scheduler, quota ledger, evidence producer, memory runtime, or independent verifier.

## Implemented critical-path prerequisite

- Exact process `comm` matching, including multiword names; presence is **not** governed work, session identity, task age or heartbeat.
- Source-isolated GET consumption of the existing local z0 service: health, dispatch readiness, providers, service metrics and aggregate outcome coverage.
- Kubernetes Ready conditions and restart counts, not inventory-count-as-health; names become opaque references.
- Optional `z0.capacity.snapshot.v1`, recursively typed/bounded and explicitly **unqualified** while its producer is not qualified.
- Disk/permission **metadata only**, preserving the existing disk-pressure/security checks without exporting filenames or reading config contents.
- Unknown economics stays JSON `null` / UI `unknown`. No receipt summation, fake savings, fabricated pipeline stages or inferred memory/shadow activation.
- Browser component registration using `window.__HERMES_PLUGINS__.register`, host React and authenticated `sdk.fetchJSON`.

### API and routes

```text
GET /api/plugins/company-os/snapshot
GET /api/plugins/company-os/health
Desktop page: /company-os
Browser page: /company-os-network
Browser bundle: /dashboard-plugins/company-os/dist/index.js
```

The UI polls every 5 seconds with overlapping calls suppressed and a 20-second request timeout. API failure retains visibly stale last-known data. UI buttons only reveal details; they cannot dispatch, infer, reserve quota, mutate evidence, or edit trackers.

The backend uses a fixed GET allowlist against `http://127.0.0.1:11501`:

```text
/healthz
/readyz
/v1/providers
/metrics
/v1/observe/outcome/coverage
```

No upstream authentication, credentials, cookies, redirects, proxies, refresh routes, POSTs or inference calls. It never reads raw receipt JSONL, credential configuration, quota ledgers, transcripts or AgentsView databases. Kubernetes uses only bounded-time `kubectl get` requests against the current context.

### Truth and privacy contract

Each source exposes `checked_at`, upstream `observed_at`, freshness, source-content SHA-256, producer revision (unknown if the API does not supply it), coverage and a fixed reason code. A response hash identifies bytes; it does **not** prove a loaded Git revision or qualified behavior. HTTP health is service-process health, not model availability or deployment acceptance.

Source failures are isolated. Unknown numeric values are not coerced to zero; explicit measured zero and false are preserved. Capacity input is limited to 512 KiB, 64 rows per kind and a closed recursive schema. IDs/labels are opaque aliases, enums are closed, arbitrary nested keys/text are discarded. Capacity generation time and filesystem mtime are not observation time. Old/reset quota values cannot masquerade as fresh availability. Sessions remain non-migratable.

Coverage is deliberately `local_partial`. Process projection is capped at 100 matches; the HUD shows 8 with visible counts. Kubernetes/capacity truncation is explicit. The hierarchy scrolls independently and is not a complete-system inventory.

## Known missing contracts / qualification holds

There is no proven live source-owned unified control/episode read contract in the inspected z0 service. `control.available=false`, `flow=[]`, and the six governed stages stay unknown. **Feature B is held**, not recreated from raw events. Its existing owners are [z0 #47](https://github.com/kvnloo/z0intelligence/issues/47) / [#54](https://github.com/kvnloo/z0intelligence/issues/54). Tokenomics canonical accounting, host/session/trace/task joins, heartbeat/death transitions, remote hosts and qualified archive runtime remain gaps.

The HUD's expandable **dated audit context** is not a live producer:

- 2026-10-10: #137 source `6770954cf42615ab5bdb2699115acb809580594d` implements memory/harness bindings absent from the audited live runtime. Native packet delivery occurred, but behavioral qualification was **FAIL / DISCARD**, not success.
- #149 / #150 are stacked receipt-integrity feature branches, not master or deployed acceptance. Passing implementation tests/CI does not establish independent quality.
- Audited runtime was dirty `4de1aa962cf4c9a19b18a6120ea27309b908da65`; the GET contract does not certify its currently loaded revision.
- Capacity producers remain z0 PR134 / Kerdoios PR57. CompanyOS does not duplicate them. Memory, reuse, shadow activation and golden-canary acceptance require their own source/consumer/outcome proof.

## Build and regression tests

No JS dependency installation is needed for the plugin or its unit tests:

```bash
node scripts/build-browser.mjs
node scripts/build-browser.mjs --check
node --experimental-vm-modules --test tests/test_ui.mjs
python -m pytest tests -q
node --check plugin/plugin.js
python -m py_compile hermes-plugin/dashboard/plugin_api.py
bash -n scripts/install.sh
bash -n scripts/doctor.sh
```

Python unit-test dependencies are in `requirements-test.txt`. Tests import production modules, use real loopback HTTP fixtures, exercise routes and reject mutation methods. The Node VM tests execute the actual Desktop module and shipped browser bundle. `scripts/mutation_checks.py` checks regression sensitivity using isolated copies, never modifying the source under test.

## Static v3 style preview (separate from live diagnostic)

`python scripts/style_preview.py --port 18744` serves `/style-preview/` on loopback and prints its actual URL/PID without opening a browser. This recovers the historical dark v3 visual foundation with an explicit light switch, crisp SVG, reusable `web/hud-v3.css` tokens and self-hosted IBM Plex fonts. It is clearly labeled **static historical architecture / not live telemetry** and cannot poll, dispatch or approve anything. The live plugin and old `web/index.html` remain unchanged.

Browser-test dependencies are in `requirements-style-preview-test.txt`; run `STYLE_PREVIEW_ARTIFACTS=/absolute/evidence/path python -m pytest tests/test_style_preview.py -q` for the owned server/browser gate and both-theme responsive screenshots. See [visual lineage, blocked video reference and future integration boundary](docs/style-preview.md).

## Interactive v3 design chooser (local preference only)

`python scripts/design_chooser.py --port 18745` serves `/design-chooser/` on loopback, using a fixed same-origin GET proxy to the existing critical-path diagnostic on `127.0.0.1:18743`. It offers three functional pane designs, light/dark themes, compressed groups and keyboard drilldown, source evidence inspection, real captured-image comparison, and local choice persistence/download. It neither changes production layout nor installs a profile. No native browser is opened automatically.

Run `python -m pytest tests/test_design_chooser.py -q` with the real backend available for browser acceptance and six-theme/layout captures. See [operation, hierarchy, visual reference and verification](docs/design-chooser.md). This newer chooser retrieved the actual issue #5 attachment and supersedes the historical missing-attachment note in the static preview report.

## Isolated live browser/API diagnostic

This does **not** start the full Hermes server, change profiles, link/install the plugin, refresh credentials, open a native browser, or restart a service. It bundles the installed Hermes **loader, registry, PluginPage and fetchJSON** into a minimal owned loopback host, mounts the production router, and consumes existing live GET sources.

Prerequisites: installed Hermes source with its existing Node dependencies (`esbuild`, React etc.); Python with FastAPI/uvicorn and, for headless proof, Playwright plus Chromium. No automatic installs are performed.

```bash
HERMES_ROOT=/home/kvn/.hermes/hermes-agent
PY="$HERMES_ROOT/venv/bin/python"
ARTIFACTS=/workspace/zer0/data/operations/company-os-recovery/implementation/manual-browser
node scripts/build-browser.mjs --check
"$PY" scripts/diagnostic.py --hermes-root "$HERMES_ROOT" --artifacts "$ARTIFACTS" --test-browser
```

The command binds an OS-assigned loopback port, exercises both production API routes, saves sanitized snapshots, verifies the actual host registration/polling/detail/outage path, captures screenshots and request/error receipts, then stops its owned server/browser. `--chromium /path/to/chromium` overrides the browser binary. The controlled outage intercepts only the test browser's request; no live service is stopped.

For manual inspection, omit `--test-browser` and optionally specify `--port 18743`. The command prints the exact URL, stays in the foreground and **does not auto-open** it. Ctrl-C stops it. An occupied explicit port fails rather than attaching to or killing its owner. This unauthenticated diagnostic is loopback-only and not a production deployment.

## Real Hermes integration (owner deployment step)

The source-owned plugin manifest declares browser `/company-os-network`, entry `dist/index.js`, API `plugin_api.py`. Desktop remains `/company-os`. The generated browser adapter reuses the host's authenticated API helper; it never reads a session token itself.

Choose the intended `HERMES_HOME` deliberately. Only under separate deployment authorization, link `plugin/` to that home's `desktop-plugins/company-os` and `hermes-plugin/` to `plugins/company-os`, preserve existing `plugins.enabled` entries when enabling `company-os`, and perform the owner's approved server reload/restart. Verify manifest, API and bundle through **that same selected profile**. `scripts/install.sh` is an existing deployment helper, not part of the diagnostic/test path; it changes links and requests a live rescan. Do not run it just to validate this implementation.

No live profile activation or Zen/native-browser deployment is claimed by the isolated test. Rollback of this local implementation requires no live action; stop the diagnostic process. If later deployed, the owner should restore the recorded previous plugin links/settings without deleting either checkout.

## Backend overrides

```text
COMPANY_OS_Z0_URL                 # exact http://127.0.0.1:PORT origin only
COMPANY_OS_Z0_CAPACITY_SNAPSHOT   # optional local regular file, no symlink
Z0INT_HOME                       # default capacity source root (~/.z0int)
COMPANY_OS_DATA_ROOT              # metadata-only disk mount (default /mnt/zer0models)
HERMES_HOME                      # server-profile provenance (opaque in browser)
```

Old receipt/quota/AgentsView overrides are intentionally not consumed without qualified source-owned read contracts.

## Operational notes retained from PR3

AgentsView officially supports `AGENTSVIEW_DATA_DIR`. If its archive is offloaded via a symlink, do not move the corpus back to `$HOME` to satisfy a dashboard check; use the real directory for AgentsView itself. The archive may require a long cold start. File existence or a readiness timeout alone is not proof of usable or failed memory. This backend intentionally reports that runtime as unqualified rather than opening its database.

`scripts/doctor.sh` retains the existing environment-directory permission checks. Group/world-writable `*.conf` metadata is critical because the user service manager can inherit those variables. The projection never reads their contents or exports filenames. For a credential-bearing file, mode `600` is normally appropriate; otherwise `644` may suffice. No permissions are changed by CompanyOS.

## License

MIT
