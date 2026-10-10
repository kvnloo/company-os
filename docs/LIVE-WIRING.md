# Source-backed network inspector

> Imported source-lane contract from `2b575c4a8000dcebe8a3d1373d209cd6adc80dec`. The integrated chooser reuses the backend and standalone adapter, **not** this lane’s Desktop renderer or diagnostic scripts. See [integration boundaries and commands](integrated-chooser.md) for the runnable artifact in this worktree.

CompanyOS is a read-only projection, not a new scheduler, memory runtime, quota ledger or verifier. This slice extends the existing PR3 path. It does not activate the plugin in any live profile.

## Recovered purpose

- [CompanyOS #1](https://github.com/kvnloo/company-os/issues/1): compact state → structured claims → evidence, explicit stale/degraded behavior, shared source semantics rather than a per-harness memory engine.
- [CompanyOS #2](https://github.com/kvnloo/company-os/issues/2): inspect fleet, capacity, economics and the selected governed path; unknown is not zero; source failures must not blank the HUD.
- [z0 #47](https://github.com/kvnloo/z0intelligence/issues/47): the authority/trace/visibility join belongs to the existing producer and harness policy boundary. Read-only visibility acquires no dispatch authority.
- [z0 #54](https://github.com/kvnloo/z0intelligence/issues/54): implementation, deployment, model-visible delivery, use, independent outcome, freshness and coverage are separate dimensions. Receipt replay is not new work or new success.

The intended unified control snapshot is **not replaced** by this consumer. Until the source owner exposes and qualifies it, the page labels its independent input groups and the missing join. Existing source implementations are not described as nonexistent just because they are not integrated into the shared GET service.

## Purpose matrix

| Group | Operational question and observable state | Existing source | Detail / limitation / next action |
|---|---|---|---|
| Agents | Which matching local processes are present? How many nodes are in the separate cluster registry? | Exact process `comm` metadata; optional cluster status GET | PID, process age, checked/observed time; no argv. Process age is not task age. PID reuse and Python/node-hosted/remote omissions are explicit. Need owner process/session/task identity and heartbeat to qualify lifecycle. |
| Services | Is the shared process reachable and dispatch-ready? Which admission/dispatch counters did it report? | `/healthz`, `/readyz`, `/metrics`, `/v1/bridge/capabilities` | Boolean readiness, protocol/transport limits, typed counter/gauge values and units. HTTP availability is not a loaded model, successful task, or behavioral acceptance. Overload is unavailable, never a measured empty counter inventory. |
| Resources | Are storage or current-context Kubernetes workloads constrained or unready? Are source-owned hosts/sessions exported? | Disk/permission metadata; `kubectl get`; optional `z0.capacity.snapshot.v1` | Disk pressure, Ready conditions/restarts, separate kube nodes, host vectors, sticky sessions. No implied kube↔host↔session join. Exporter absence is unknown, not an empty global inventory. |
| Capacity | What admission headroom is reported, separately from dimensional quota? | `/v1/providers`; optional capacity offers/leases | Inflight/cap, availability reason, cooldown, typed quota/resources when exported. Inflight/cap is not token budget. Stale/reset remaining quota is withheld. Placement does not authorize execution. |
| Work & authority | What work states are genuinely observable? Is the selected governed path joined? | Optional `/api/v1/cluster/status`; explicit #47/#54 read-contract gap | Cluster pending/ready/running/completed/failed counts remain registry-only. Blocked/cancelled are unreported, not zero. Objective, AODL, placement, dispatch, admission, execution and verification are separately inspectable **unknown** stages, not invented episode nodes. |
| Cognition | What does the bridge advertise? Is consumer/model use qualified? | `/v1/bridge/capabilities`; memory qualification gap | Endpoint semantics are inspectable without invocation. Shadow endpoints can physically execute models. Advertised support is not invocation, model input, use, independent benefit or permission. |
| Evidence coverage | Which expected outcome windows are eligible, missing or incomplete? | `/v1/observe/outcome/coverage` | Registered-expectation scope, 1h/24h/7d denominators, complete/partial/missing, ratios and gate reasons. `as_of` is assessment time, not the latest evidence event. Coverage alone is not causal quality. |
| Evaluation | Is any registered experiment ready for human review? | `/v1/observe/outcome/randomized-evidence` | Opaque experiment IDs, arm unit counts, sample gates and review requirements. Review readiness is not causal proof, deployment acceptance or promotion permission. Free text, metric effects and treatment hashes are omitted. |
| Economics | What measured usage/cost/verified work can be credited? | Explicit canonical Tokenomics read-contract gap | Unknown fields remain unknown. No receipt summation, provider-counter accounting, fake avoided-token total or invented savings. Integrate the existing Tokenomics window/identity contract rather than a second ledger. |
| Sources & gaps | Which exact input is unavailable, stale, bounded or unqualified? | Every source envelope | Endpoint/metadata scope, observation/check/assessment time, response SHA-256, unknown producer revision, coverage and blocker. A response hash identifies bytes, not the loaded source revision. |

## Interaction contract

- Ten representative overview groups. Child pages show at most eight nodes, with explicit projected counts and source coverage. No global total is inferred from a bounded projection.
- Every node is a real button with meaningful source detail or an explicit unavailable explanation. Child count is navigation structure, not an activity metric.
- Click, Enter or Space selects/drills; Right arrow drills; Left arrow/Escape and Back return; breadcrumbs jump ancestors. Keyboard drill transfers focus into the new child list and Back restores the relevant group. Polling does not steal focus.
- Selected state, paging, child collapse, and detail survive ordinary polls. The selected node keeps its stable source key, not its array position.
- A removed selected node retains the **latest successful** detail/provenance, not merely click-time state. It is labelled last-known; disappearance does not prove completion. API outage retains the same visibly stale detail.
- Structured fields and source envelopes use expandable details, keeping the overview compact without hiding provenance. No buttons imply dispatch, deployment or mutation.

## Reusable adapter

```js
import {buildInspectionModel} from './plugin/inspection-model.mjs'
const {root, nodes} = buildInspectionModel(snapshot)
```

This generated module needs no React, SDK or network. It yields stable `id`, `parent`, `children`, `sources`, `meaning`, `limitation`, `observedCount`, `summary` and bounded `data`. Edges mean presentation grouping only. `plugin/plugin.js` is canonical; `scripts/build-browser.mjs` emits both the browser bundle and this adapter. `--check` rejects drift. The design chooser can reuse the same model/API without accepting this renderer's styling.

## Source-owner integration, not replacement backend

Discovery inspected the current shared source and archived exact-source HTTP implementations for master, #137 readiness, the integration/multiharness lanes and PR121/PR150. Their seven exposed operational GET paths are the ones consumed here. Dispatch authority, task checkpoints, receipts and memory contracts already exist elsewhere; their existence does not establish a bounded, current, qualified selected-work GET join.

- **Work/repair view:** #47/#54 own the current-intent/tracker → source/implementation → consumer → independent outcome join. Expose canonical IDs, revision/freshness, source coverage, blocker and next permitted action there; do not reconstruct it from arbitrary event/receipt files in CompanyOS.
- **Capacity:** [z0 #133 / PR134](https://github.com/kvnloo/z0intelligence/pull/134) and [Kerdoios PR57](https://github.com/kvnloo/kerdoios/pull/57) own exporters. Preserve explicit optional/unqualified state until configured and qualified. This consumer does not create or refresh those files.
- **Memory/reuse:** #22/#66/#137/#140 own source, sufficiency, binding and use. The dated #137 audit records native delivery but behavioral FAIL / DISCARD; availability and green implementation CI must not become active/qualified memory badges.
- **Receipts/economics:** PR149/PR150 are feature-branch receipt-integrity fixes, not deployed acceptance. Preserve negatives and unknown outcomes. Their source existence is not permission to start a duplicate summary store.
- **Evaluation:** existing registered outcome/review GETs are wired now. They are not a global work score, protected evaluation verdict or a new judge.
- **Hermes Cluster:** an existing separate live aggregate is useful when explicitly configured, but supplies neither process identity nor the governed/evidence join. Its `python-1.0.0` shape is checked. Origins must be loopback or verified IPv4 addresses on this machine; no credentials, arbitrary remote hosts, redirects, task-body or config reads.

## Verification and boundaries

`tests/test_service_details.py` executes real loopback HTTP fixtures against the production consumer. `tests/test_ui.mjs` executes the Desktop module, browser registration and standalone adapter. `scripts/test-inspector.py` runs the installed Hermes registry/loader/PluginPage/fetchJSON in an owned headless diagnostic and performs real clicks/keyboard input against the production API and bundle.

The browser gate records live GETs separately from labelled browser-only replacement/removal/outage controls and the disposable stale/privacy capacity fixture. It retries initial live readiness at most four times, preserving every attempt; a passing interaction gate is not uninterrupted upstream availability. The production collector does not retry or perform inference. A live overload was observed during this lane and is retained in its receipts.

The gate owns/reaps its temporary server and headless Chromium. It does not restart the shared z0 service, edit profiles, activate plugins, migrate databases, call provider/dispatch endpoints, change external trackers, or touch peer worktrees. No native browser or physical desktop is opened.

Evidence for this lane lives at `/workspace/zer0/data/operations/company-os-recovery/live-wiring/`: refreshed issue/PR threads, declared-comment count checks, exact-source GET inventories, red/green logs, live sanitized snapshot, browser screenshots/request receipt, mutation controls, and protected-tree verification. Local source implementation and isolated rendering are the acceptance scope; full native/profile deployment and source-owner golden governed traces remain separate work.
