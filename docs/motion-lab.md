# CompanyOS motion lab

Local design candidate, based on replica `9478d88ba76a51c2f1f03c43c31bfac0f26fe9bf`. No production layout, profile, source collector, authority, or library stack is changed.

```sh
python scripts/motion_lab.py --port 18750
# http://127.0.0.1:18750/motion-lab
```

The launcher binds only loopback; an occupied port fails rather than replacing its owner. It serves the unchanged replica at `/video-replica` for same-origin side-by-side viewing. The original 18748 and integrated 18747 listeners are not controlled by this launcher. The default fixed upstream is `http://127.0.0.1:18747`; only snapshot and health GETs pass through. Upstream cookies/auth and redirects are not forwarded. Source access denial is preserved as 401/403 so browser-held facts can be cleared.

## Four choices, not four claims of implementation

- **00 / observed reference:** unchanged faithful video replica; reference-fixture numbers, not network data. Its measured flights are observed in the clip. Its original creator remains unverified.
- **01 / evidence trace:** source ring → actually bound card → evidence/provenance. One finite reveal teaches a reading path. It is not causal telemetry or agent execution.
- **02 / context lens:** selected track separates while the other nine remain context; related card, row and evidence retain the same canonical source ID. This is presentation focus, not data enrichment.
- **03 / time & hypothesis:** explicitly capture A in this tab, refresh B through GET, compare exact matched scalars. A dashed ghost separates held context from latest data. The source-withheld branch removes evidence only; it makes no prediction. No historical A is generated.

All three proposals retain ten colored rings, six compact cards and fourteen dense rows from the visual motif. **The rows are source bindings, not active worker lanes.** Ring arc lengths are fixed design geometry, never progress percentages. Colors identify categories, not success.

## Operator-purpose / source matrix

| Question | Bound source | Actual read | Missing-source behavior |
| --- | --- | --- | --- |
| Why trust this summary? | `sources[id]` plus checked-in source scalar paths | status, freshness, observation/check/assessment timestamps, scope, digest, producer revision | unknown stays unknown; no percent/quality inference |
| Is dispatch readiness the same as authority? | `z0_readiness` | `z0_service.readiness.*` allowlisted booleans/numbers | unavailable/denied fields remain unknown; no action route |
| Is there outcome evidence? | `z0_outcomes`, `z0_evaluation` | registered expectations/observations, returned experiments, existing explicit gates | zero is distinct from unknown; no company-wide outcome claim |
| What does the Hermes count mean? | `hermes_cluster` | exact registry counts only | no process/task/authority join invented |
| What changed since I pinned the view? | explicitly captured normalized A and current B | same IDs, exact same scalar paths and snapshot times | absent A = not captured; no upstream history synthesized |
| What if this evidence were withheld? | selected source's existing binding | local hypothetical omission | every branch value says withheld/hypothesis; no forecast |

`model.mjs` is the closed data/selection seam. Unknown paths, missing source provenance, denied fields and unsupported snapshot schemas fail closed. Only scalar numeric/boolean fields are projected; private payload fields and raw prompts are not rendered or retained. The canonical capacity plane is not replaced by the legacy `capacity` provider alias.

## Local interaction lifecycle

- All interactive ring/card/row identities mount once. Refresh updates text without replacing controls or stealing focus.
- Three variants are deterministic manually selected recipes. This is **not** a generative OpenUI/voice adapter or an implementation of the whole issue #5 backlog.
- Enter question lens captures presentation state. Back restores the previous stable selection. Restore/Discard recover the prior selection, variant, disclosure, scroll and entry control. They do not rewind live data or re-authorize denied data.
- Pin stores only `{schema, variant, selected}` under `companyos.motion-lab.pin.v1`. Recall opens another private lens. Snapshot A remains memory-only and is erased on restore/discard/page exit or source access denial. Forget removes only this lab's pin.
- No microphone, sharing, presenter, mutation, arbitrary text request, remote model or generated code path exists. The page states **Not listening / not sharing**.
- Play/Pause and native range scrub control a finite reveal. Reduced-motion begins off, updates pause active motion, and an explicit Motion off keeps all information/controls usable. Escape restores an ephemeral lens. Enter/Space activate all controls; arrows move between SVG rings or scrub the native slider.
- Normal reads are manual GET only. A successful GET is not treated as a fresh observation. Warm outages mark last-received facts NOT current; cold outages show unknown. 401/403 clear both current and held facts; a per-source denial clears any held comparison.

## Verification

No install required for the artifact itself: Python stdlib server and native HTML/CSS/SVG/JS. Browser proof uses an already available Playwright environment with system Chromium; it never attaches to Zen.

```sh
node --test tests/motion-lab.test.mjs tests/video-replica-bindings.test.mjs tests/test_inspection_adapter.mjs
python tests/test_motion_lab.py
# Use an environment already containing playwright:
python scripts/verify_motion_lab.py
# or verify the owned running handoff server:
python scripts/verify_motion_lab.py --base http://127.0.0.1:18750
# Actual CDP screencast frames → local VP9 WebM, ffmpeg required:
python scripts/capture_motion_lab.py --base http://127.0.0.1:18750
```

The browser verifier normally owns a port-0 server and cleans up only that instance. It writes actual captures, a four-image gallery, a viewport/variant matrix and a counted receipt. Normal captures use real source GETs; privacy, denial, outage and storage-failure injections are isolated **test fixtures**, never demonstration data. The screencast is made from real Chromium frames with recorded timestamps/hashes; it has no microphone/audio track.

Evidence defaults to `/workspace/zer0/data/operations/company-os-recovery/motion-prototypes/`. Generated operational data/media/receipts are not committed. `REPORT.md` there records verified outcomes, exact process/commit and source gaps.

## Unresolved contracts and promotion boundary

No source here establishes objective denominators, causal PR dependencies, independently accepted delivery, RevOps/CRM/BI windows, historical time series, task-owner authority, or a governed worker lane join. Existing available source counts are not substitutes. No new source, collector or fabricated agent is added to fill the design.

The issue's typed conversational binding, meeting/speaker revision context, preview/present sharing, generation validator, TTL/expiry, reusable widget promotion/dormancy, 100-cycle disposal/performance gates and A/B/C decision-outcome benchmarks remain future work. User visual preference in this lab is not evidence of better decisions or production readiness. The equal-information static table is a selectable control, not a completed benchmark.

## Reusable implementation lessons

Bind the highlighted category card dynamically to the selected source rather than highlighting a related but differently sourced value. Treat snapshot transport denial as a revocation, not an ordinary last-known outage. Drop older comparison anchors on source-level denial. Preserve the original control nodes on rebind and test actual focused elements. In CSP-constrained headless tests, use bounded host-side polling instead of Playwright string-eval wait predicates; do not weaken the page CSP for the test. Keep absent comparison context visibly absent, including its ghost geometry.
