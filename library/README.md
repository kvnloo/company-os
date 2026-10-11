# CompanyOS component + dashboard library (catalog v1)

**Status:** source-grounded, machine-readable **design/contract scaffold**, **not** a new renderer or a claim that 22 widgets / nine views have been implemented. Parent: [CompanyOS #5](https://github.com/kvnloo/company-os/issues/5). The source-of-truth for business, task, model, quota, worker, approval, outcome and memory state stays in its existing owner.

- [components.v1.json](components.v1.json): 22 typed **candidate widget definitions**, questions, allowed presentation interactions, evidence guards, data bindings and rollout phase.
- [dashboards.v1.json](dashboards.v1.json): nine **composition recipes**, first two based on CompanyOS PR #3's optional read-only projection.
- [validate_catalog.py](validate_catalog.py): dependency-free schema/reference lint; does **not** verify pixels, actual data, or runtime integration.

## Reviewed visual corpus — all 10 checked-in images + North Star video

| Artifact | Specific reusable visual insight | Caution |
| --- | --- | --- |
| [Dark cockpit](../docs/inspo/hud-dark-cockpit.jpg) | Black canvas; fine dotted/line topology; voice, left small cards, center hub, right lane; lower prompt | Its ENG / RESEARCH / OPS and counts are **illustrative**, not architecture or real telemetry |
| [Light cockpit](../docs/inspo/hud-light.jpg) | Low-contrast alternative; spacious intent-driven navigation | Must still meet legibility/contrast without giving up provenance |
| [Talk to company](../docs/inspo/landing-talk-to-company.jpg) | Voice -> bridge -> agent/tools/memory progression | Landing/aspiration, not proof that voice tools execute |
| [Grok voice / Tail MCP bridge](../docs/inspo/grok-voice-tailscale.jpg) | Phone voice entry, explicit trust/transport boundary, CoS agent hierarchy | Conceptual architecture; don't assume a live encrypted service exists |
| [HUD canonical v3](../docs/architecture/hud-canonical-v3.png) | Vertical truthful ownership chain from human/voice/intake to workers | The diagram is a governance map, not executable graph or performance score |
| [HUD real nodes](../docs/architecture/hud-real-nodes.png) | v3 center dotted hub; Voice / First Mate / HITL left, Product / OSS / Host right | Keep the **canonical semantics**, not arbitrary labels or hallucinated metrics |
| [HUD theme v3](../docs/architecture/hud-theme-v3.png) | Locked sparse visual grammar: void paper, rings, tracked type | Favor stable focus/selection, limit animation |
| [v1 three runtimes](../docs/architecture/map-v1-three-runtimes.jpg) | Historical separation of company mind and execution harnesses | Superseded ownership; do **not** copy v1's old roles |
| [v3 canonical graph](../docs/architecture/map-v3-canonical.jpg) | Voice intake -> First Mate -> Linear -> Product/OSS -> Third Mate -> Second Mate/Kanban -> workers; human approval on top | No fourth ledger; keep executable authority with source owners |
| [v2 mates/intake/Kanban map](../docs/architecture/map-v3-mates-intake-kanban.jpg) | Prior approval/host-vs-product owner feedback and provenance | Historical v2 image filename includes v3; canonical latest is v3 |
| [North Star reference video](https://github.com/kvnloo/company-os/issues/5) | Concentric outcome rings, dense "lanes now" grid, metric tile/sparklines, compact lower status deck, restrained motion | Video's numeric values are **not z0 data**; its original creator is not verified; preserve attribution uncertainty |

### Design invariants

1. **Visuals are evidence views**, not truth sources. Every nontrivial number needs exact numerator/denominator/window/source/status; missing is not zero. A ring with no qualified objective renders *unknown*, not a made-up percentage.
2. **Glance → focus → evidence.** Small quiet labels at rest; show proof, conflicts and next diagnostic probes on selection. Any ephemeral scene can dismiss/Back without losing the persistent cockpit.
3. **Motion encodes transitions** (blocked, resumed, verified, stale) and observes a reduced-motion setting. No continuous ornament/no focus theft.
4. **Human control stays human.** Any action beyond selecting/inspecting/rearranging a view must go through the existing AODL and native Hermes/other harness permission path; the catalog has no mutation authority.
5. **The source/event owner is not the viewer.** CompanyOS remains a private, sanitized projection. Never publish raw private events, prompts, transcripts, provider credentials or secret filesystem contents in this repo.

## Backend status / migration map (observed October 10, 2026)

| Upstream | Actual seam | First CompanyOS use | Hold / proof required |
| --- | --- | --- | --- |
| [CompanyOS draft PR #3](https://github.com/kvnloo/company-os/pull/3) | `GET /api/plugins/company-os/snapshot` and `/health`, `company_os.snapshot.v1`, 2s UI poll | fleet, sources, K8s, memory metadata, disks, security, capacity and **provisional** economics | PR is draft/unmerged. Inspect Hermes's current **local** dashboard tree before implementing anything anew. Probe endpoint with doctor + sanitized response; never infer installed runtime from repo code |
| [z0 control #47](https://github.com/kvnloo/z0intelligence/issues/47) | optional read-only control snapshot | execution/decision trace | distinguish governed/ungoverned/unknown and consent; no trace-prefix authority guessing |
| [z0 capacity PR #134](https://github.com/kvnloo/z0intelligence/pull/134) / [Kerdoios #57](https://github.com/kvnloo/kerdoios/pull/57) | `z0.capacity.snapshot.v1` hosts/sessions/offers/leases, optional file | provider/device offer chart | draft, host-installed state unverified; unknown remains null, Tern sessions sticky |
| [z0 receipt #54, PR #149](https://github.com/kvnloo/z0intelligence/pull/149) / [PR #150](https://github.com/kvnloo/z0intelligence/pull/150) | canonical trace-based outcome + usage revision join | verified results and Tokenomics economics tiles | **P0 correctness barrier:** PR #3 raw receipt aggregations can double-count append-only revisions and old positive statuses. Before using as KPI, reconcile canonical/bridge negatives, latest rev and per-trace idempotence. These repair PRs are still drafts |
| [z0 local shadow #20](https://github.com/kvnloo/z0intelligence/issues/20) | versioned shadow model observations/timeouts on feature branches | local-cognition comparison card | independent race/budget tests are branch-only; shadow != selected/deployed outcome |
| [z0 latency #139 + draft #141](https://github.com/kvnloo/z0intelligence/pull/141) / [#148](https://github.com/kvnloo/z0intelligence/pull/148) | hook RTT and neutral per-call diagnostics | latency waterfall / provider fallbacks | enabled specialization still has a synchronous hook; #148's report has incomplete/mixed strata and product smoke not green. Don't claim end-to-end speed or savings |
| [z0 memory #22](https://github.com/kvnloo/z0intelligence/issues/22), [reuse #137](https://github.com/kvnloo/z0intelligence/issues/137) / [draft #140](https://github.com/kvnloo/z0intelligence/pull/140) | State Packet, context/reuse readiness | history+reuse lens | construction, retrieval, model-visible delivery and used/verified are distinct; reuse is a draft **contract**, not an enforced code-edit gate |
| [z0 #144 ctx coverage finding](https://github.com/kvnloo/z0intelligence/issues/144) | coverage/health receipts | coverage-gap panel | OMP sessions not indexed in observed ctx host configuration; do not render "memory healthy" from AgentsView DB readability alone |
| [continuation PR #132](https://github.com/kvnloo/z0intelligence/pull/132) | restart-safe checkpoint contract | paused/sticky/recoverable state | native Hermes/OMP/Tern resume not proven; no automatic session migration |
| [Hermes OpenUI #456](https://github.com/kvnloo/hermes-agent/pull/456) / [#457](https://github.com/kvnloo/hermes-agent/pull/457) | small OpenUI Lang adapter and preview candidate | catalog-driven **view composition** only, later | draft experiments; no verified live Tern pixels or CompanyOS mounting. No arbitrary generated JS or Luau at runtime |

**Specific red flag in published PR #3:** `plugin_api.py:_economics()` iterates raw receipt rows; `_event()` uses an optimistic trace-prefix heuristic to mark some events governed. Do not show its positive aggregates as independently verified success or savings until #54's canonical reconciliation semantics are integrated and tested. The UI should label missing canonical evidence as partial/unknown.

## Integration order — smallest useful slices

1. **Freeze what's already built.** Collect the current Hermes-local CompanyOS screen/pane tree, the exact running plugin revision, `scripts/doctor.sh`, JSON keys from `/health` and a redacted snapshot. Compare against draft PR #3. No duplicate implementation.
2. **Truth bridge first.** Add a read-only canonical receipt summary adapter with exact trace IDs, revision provenance, verifier class, source freshness and measured-vs-estimated economics. Tests include replay, negative override, missing source and cross-version evidence.
3. **Ship two composed screens.** Render `factory-glance` and `fleet-economics` using existing snapshot fields, independent from OpenUI. Six P0 widgets; a missing data source shows an explicit gap. Compare to current UI screenshots.
4. **Then enable dynamic composition.** Catalog selector produces bounded approved widget/scene IDs and data refs; host checks schema, query scope and revisions before preview. Render → inspect → show; never let arbitrary LLM code run in the browser.
5. **Only after operator evidence:** voice-directed rearrangement, saved useful recipes, offline eval against static views, explain/discard/pin. Keep the stable shell and approval location.

### Tests / acceptance

- `python3 library/validate_catalog.py` passes. **This is only static reference integrity.**
- Real Hermes installed plugin loads exact selected revision; approved P0 source adapters have observed telemetry and freshness, and missing data degrades locally rather than fabricating data.
- 6 P0 widgets + 2 P0 scenes function on both narrow and desktop layouts, keyboard/reduced motion; 100 replace/update/dismiss cycles preserve focus and previous good view.
- Negative controls: stale snapshot; partial quota; shadow timeout; an old positive receipt followed by a newer negative; duplicate/cross-harness receipt; missing evidence; enabled-specialization latency; wrong-context/ambiguous voice reference. Each must stay truthful.
- Frozen operator tasks compare current dashboard versus this catalog-driven version. **Win only if time to correct decision, evidence retrieval, and interruption burden improve.**

## Provenance

Design directions: user-supplied original reference video (creator unverified) and repo images authored before this catalog; attribution retained by path. Implementation/diagnoses credited to the respective original Hermes, z0intelligence, OpenUI/Thesys, Stencil/Tern, Kerdoios, Tokenomics and GEV contributors per linked PR/issue authorship. These files make no claim those people endorsed this catalog.
