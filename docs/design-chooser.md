# Read-only CompanyOS design chooser

**Integrated delivery:** use [the complete launcher](integrated-chooser.md) for the production backend + ten-group adapter on 18747. The proxy-only invocation below remains supported; it does not update or restart its explicitly supplied upstream.

An isolated interactive chooser over the existing critical-path backend. It does not replace the plugin, install a profile, dispatch work, or change production layout. All three are custom dashboard views. Saving a default is a browser-local preference and an optional downloaded JSON file, not elimination of the other views. A later owner-authorized implementation/deployment is separate.

## Run

```bash
python scripts/design_chooser.py --port 18745 \
  --upstream http://127.0.0.1:18743 \
  --artifacts /workspace/zer0/data/operations/company-os-recovery/design-chooser
```

The source service must already expose `GET /api/plugins/company-os/snapshot` and `GET /api/plugins/company-os/health`. The server prints its actual loopback URL/PID, does not open a browser, and fails if the requested port is occupied. Omitting `--port` binds an OS-assigned port. SIGTERM/Ctrl-C shuts down only this server. Open `http://127.0.0.1:18745/design-chooser/` (not `localhost`, because the host guard is exact).

No second data authority is introduced. A fixed, same-origin GET-only proxy forwards the two allowlisted JSON routes to `127.0.0.1`. It does not recalculate source bytes, forward cookies/authentication, follow redirects, expose arbitrary paths, or use environment proxy settings. External origins, cross-site browser reads, API query strings, and mutations are rejected. Static fonts/styles are served from a fixed allowlist. The image gallery serves only six named captures, with byte hashes and capture times. This unauthenticated loopback design host is not a production server.

## Compare and inspect

- **Spatial cockpit:** source index rings, a service/provider rail, and a persistent inspection column. The center and each labeled node are actual group buttons; rings express neither progress nor topology.
- **Operations split:** service/supply on one side and workloads/process presence on the other, with a broad evidence area below.
- **Instrument desk:** source freshness ledger, parallel expandable instruments, and a detail rail. Expand/collapse all or use each native keyboard-operable disclosure.
- **Common hierarchy:** ten imported adapter groups with eight-child pages. Agents, Services, Resources, Capacity, Work & authority, Cognition, Evidence coverage, Evaluation, Economics, Sources & gaps. Resources exposes Kubernetes pods/nodes and separate host/session exports. Breadcrumbs and Back one level navigate source categories, not inferred task/authority relationships.
- **Inspection:** actual child fields, source provenance, source timestamps, freshness, bounded coverage and raw JSON. Null/absent values remain `unknown`, while measured `0` and `false` stay intact. Empty capacity/providers explain the missing observation rather than implying idle/offline.
- **Updates:** poll five seconds after the previous request completes, or Refresh snapshot. Pause updates for manual reading. Selection, native disclosures, scroll positions and disclosure focus survive updates. A failed read keeps an explicitly stale last-known snapshot; cold failure invents no rows. A successful GET does not make an upstream source fresh.
- **Keyboard:** Tab/Shift-Tab reach buttons/links, Enter or Space activates controls and disclosures; Left/Right/Home/End navigate design tabs. Return to selected row focuses and reopens its section when present.
- **Default view:** Save as default view saves layout/theme under `companyos.chooser.choice.v1`; current theme is `companyos.chooser.theme`. A visible marker and status show the choice. Download choice exports `companyos-design-choice.json` with `production_changed: false`. Storage denial falls back to session-only choice with an explicit warning. No choice is sent to a backend.
- **Images:** Compare images shows six actual browser captures, not live telemetry. Each image opens its corresponding live design/theme; Full PNG opens the captured file. Previewing an image is not choosing it. `?design=spatial|balanced|dense&theme=dark|light` allows direct preview.

## Visual lineage

The chooser imports the recovered `web/hud-v3.css` unchanged: local IBM Plex Sans/Mono, thin corner brackets, dotted rings, small circles/diamonds, restrained near-black and warm-white themes. Density varies with the actual content; no texture/noise or invented activity is added.

Style base: `7da554116d096cdfc7a7fb77658da5eca80bd6e4`. Existing diagnostic contract: critical-path head `19d19528df0900e206a74441f2dbc8265ad71adc`.

Issue #5's actual attached clip was retrieved and inspected, superseding the earlier style-preview report's missing-attachment observation:

- Issue: https://github.com/kvnloo/company-os/issues/5
- Exact clip: https://github.com/user-attachments/assets/18dc5eb2-e513-4486-a33b-5937f8d176ef
- Inspected frames: 0.0s, 7.5s, 14.5s. Early overview and middle dense hierarchy inform grouping and panes, not source numbers or claimed interactions. The clip creator is not established.
- Evidence: `reference-receipt.json`, original MP4, probe metadata, contact sheet and PNG frames under the artifact directory.

## Verify

Use the existing test environment (pytest and Playwright; Chromium at `/usr/bin/chromium`). Dependencies are already listed in `requirements-test.txt` and `requirements-style-preview-test.txt`.

```bash
CHOOSER_ARTIFACTS=/absolute/evidence/path \
  python -m pytest tests/test_design_chooser.py -q
node --check web/design-chooser/chooser.js
python -m py_compile scripts/design_chooser.py
```

The test command starts/stops its own ephemeral integrated chooser/backend server. Browser acceptance consumes the existing source services directly through the production consumer; it does not depend on the sibling 18743 server or substitute fixture telemetry. The proxy unit test uses an explicitly labeled protocol-only payload to prove byte passthrough/null/zero/false and no credential forwarding.

Coverage: three layouts and two themes; choice persistence and downloaded JSON; actual snapshot/source retrieval; hierarchy/child inspection; keyboard and disclosure continuity across polling; expanded provenance retention; controlled consumer-only outage/recovery; cold outage/storage denial; six-image gallery; six viewport sizes including 320px, 390px, 768px, 1024px, 1440px and 1536px; no horizontal overflow, no normal-path page/console errors, loaded local fonts, no simulated progress animation, and same-origin GET-only requests. Outage injection aborts only the test browser request and never stops a live service.

The suite captures 36 layout/theme/viewport combinations. The six 1536px PNGs are the gallery artifacts. JSON request logs, source snapshots, render matrix and outage/choice receipts accompany them. A whole-repository regression run can additionally use `STYLE_PREVIEW_ARTIFACTS=/another/path python -m pytest tests -q` and the existing Node UI tests.

## Boundaries and handoff

The chooser reads the existing backend as-is, including degraded/unavailable sources, unknown upstream observation timestamps, unqualified capacity, and missing task/economics/authority joins. It is not evidence that all services are healthy. The integrated launcher now imports the verified backend and standalone adapter from the separately owned live-wiring worktree. That worktree and all sibling servers remain unchanged.

Preserve artifacts locally: operational snapshots/captures are not committed or uploaded. Commit only chooser source/tests/docs. Do not push, merge, install, edit live profiles or auto-open native windows as part of this diagnostic.
