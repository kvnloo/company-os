# Integrated v3 dashboard views (local, read-only)

All three layouts are retained as distinct custom dashboard views, not competing finalists. The view tabs switch perspectives; **Save as default view** sets a browser-local default without removing the other views. Existing chooser routes, filenames, query IDs, storage keys and JSON preference schema remain backward compatible.

Issue #5 was refreshed after the owner's update (2026-10-10T21:52:26Z; 0 declared/fetched comments). Compatible immediate semantics are explicit focus ownership, reversible inspection, persistent reading context, quiet presentation, last-good evidence, deliberate local preference and source-scoped unknowns. Conversational/voice-driven scenes, presenting/sharing, generative widgets and a view-recipe architecture remain proposed and outside this integration; no microphone, external publishing or model invocation is enabled. The parent's library research owns that next design decision.

This worktree intentionally starts at chooser `fa6c99de795695e67e88fab99374241c253e1b7b` and imports **only** the backend, dependency-free inspection adapter, and matching consumer tests/contracts from live-wiring `2b575c4a8000dcebe8a3d1373d209cd6adc80dec`. It does not cherry-pick the Desktop renderer or overwrite the recovered v3 styles. The three chooser arrangements, local IBM Plex fonts, theme tokens and local preference schema stay intact.

## Run the complete artifact

```bash
PYTHONDONTWRITEBYTECODE=1 \
COMPANY_OS_CLUSTER_URL=http://100.113.138.100:8787 \
/home/kvn/.hermes/hermes-agent/venv/bin/python scripts/integrated_chooser.py \
  --port 18747 \
  --artifacts /workspace/zer0/data/operations/company-os-recovery/integrated
```

The cluster override is optional; omit it to show `not_configured`, not zero. The existing consumer validates loopback or actual local IPv4 ownership. The z0 origin remains the existing loopback service `http://127.0.0.1:11501`, unless an explicit valid `COMPANY_OS_Z0_URL` is supplied. Neither source is started or restarted.

The launcher reserves an OS-assigned private loopback API socket and the requested public chooser port. It mounts the **actual production FastAPI router** from this worktree without starting Hermes, loading credential configuration, editing profiles or activating plugins. The existing fixed same-origin GET-only proxy preserves API JSON bytes and serves the existing chooser and exact adapter. A public-port collision fails before any collector starts. SIGTERM/Ctrl-C reaps only this process's private API thread/listener. There is no fallback to a sibling diagnostic and no dependence on ports 18743–18745.

Ready URL: `http://127.0.0.1:18747/design-chooser/`. The launch JSON names PID, both owned listeners, source root and artifact directory. Open it in an existing browser; the launcher never opens native windows.

## Functional contract

- Ten adapter groups: Agents, Services, Resources, Capacity, Work & authority, Cognition, Evidence coverage, Evaluation, Economics, Sources & gaps.
- Every group exposes its operational question, limits, actual projected child data and source provenance/coverage. Child pages contain at most eight rows. Navigation counts are not global work totals.
- Click, Enter, Space and Right arrow drill. Back, Left arrow and Escape return with child focus; breadcrumbs jump ancestors. Native section and child collapse controls remain functional.
- Paging, selected source identity, disclosure state, scrolling and keyboard focus survive ordinary five-second polls. Namespaced pod IDs remain distinct even when display names match.
- A disappearing selected row or failed selected source retains the **latest successful** detail and provenance, explicitly marked last-known/stale. Disappearance is never completion. Whole API failure retains all panes; cold failure invents nothing.
- Service health/readiness, providers, metrics, bridge capabilities, outcome-window denominators, randomized-evidence review gates and optional cluster aggregates remain distinct. No advertised inference endpoint is invoked. Process counters are not economics, process presence is not work, cluster counts are registry-only, and healthy transport is not upstream freshness or producer revision.
- Missing canonical Tokenomics, selected-work/authority and qualified memory remain explicit unknowns. Real zero/false/null are preserved. Empty HTTP overload cannot become zero metrics; a failed process source cannot produce a zero-count badge.
- The existing local storage keys and download schema are unchanged: `companyos.chooser.choice.v1`, `companyos.chooser.theme`, `companyos.design-choice.v1`, `scope=local-design-preference`, `production_changed=false`. Isolated test selections are not the user's choice.

## Verify

Verify an already-running exact artifact without restarting it:

```bash
python scripts/verify_integrated.py --url http://127.0.0.1:18747 \
  --artifacts /absolute/evidence/committed-server
```

This verifies served file hashes and backend implementation hash against this checkout, exercises six live view/theme combinations, local defaults/download, and explicitly labelled retained-detail/source-outage controls. It opens/reaps only its own isolated headless Chromium.


```bash
CHOOSER_ARTIFACTS=/absolute/evidence/directory \
STYLE_PREVIEW_ARTIFACTS=/absolute/separate/style/directory \
PYTHONDONTWRITEBYTECODE=1 python -m pytest tests -q
node --experimental-vm-modules --test tests/test_ui.mjs tests/test_inspection_adapter.mjs
node scripts/build-browser.mjs --check
node --check web/design-chooser/chooser.js
```

The Python suite starts/reaps its own integrated servers. Browser acceptance consumes real existing GET sources, not operational mocks. The explicit consumer-only replacement/removal/outage controls and closed-schema privacy/overload HTTP fixtures are separate tests. The six layout/theme interaction gate records every readiness attempt (maximum four); successful interaction is not a claim of uninterrupted source availability. The responsive matrix covers 36 unique layout/theme/viewport combinations. Screenshots remain local evidence, not checked-in telemetry.

`plugin/inspection-model.mjs` and `hermes-plugin/dashboard/plugin_api.py` are exact imports from the pinned live-wiring commit. The adapter was generated there from that lane's canonical model. This integrated chooser deliberately does **not** replace `plugin/plugin.js` or its generated Desktop/browser entry. Its existing `build-browser.mjs --check` continues to check the unchanged plugin entry, not regenerate the imported standalone adapter. Update the adapter intentionally from its source lane and rerun adapter plus chooser tests.

The older proxy-only launcher remains available for explicit external backend inspection, but integrated tests and this handoff use the complete launcher above. No push, merge, production deployment, profile activation, capacity exporter creation, provider call, credential read or service restart is implied.
