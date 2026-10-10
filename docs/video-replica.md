# WOLFSUITE / North Star video replica

A separate **reference-fixture-only** visual study, not another CompanyOS design interpretation and not a live dashboard. Based on the exact initial frame of the user-supplied issue #5 attachment. The existing integrated dashboard and API are not imported or modified.

## Run / inspect

```sh
python scripts/video_replica.py --port 18748
# http://127.0.0.1:18748/video-replica
# Native, unscaled comparison: /video-replica?native=1 at 1496 × 1080, DPR 1.
```

The default route fits the locked composition above separate fixture/comparison controls. It does not rearrange or simplify the reference at smaller viewports. Native mode places the controls below the 1080-pixel frame. Side-by-side temporarily fits both images even when entered from native mode.

Controls: replica, original frame, opacity-adjustable overlay, side-by-side, measured-motion play/pause, reset, and the issue-defined binding map. P4's observed tooltip is exposed on hover or keyboard focus; Escape closes it. The recorded initial arrow is a crisp SVG fixture element, not the real pointer. It is not moved as a fabricated interaction.

## Source, media and scope

- Video: <https://github.com/user-attachments/assets/18dc5eb2-e513-4486-a33b-5937f8d176ef>
- SHA-256: `84a29e4fafea04c7a4b945f7db4f6c5b09877ba8996572d244662996093063b5`.
- Video stream: **1496 × 1080, 60/1 fps, 909 frames, 15.150000 seconds**. Container including AAC audio: 15.210667 seconds. The audio is not recreated.
- Initial frame: **frame 0, PTS 0.000000 s**, no crop, scale or interpolation. PNG SHA-256 `4be34d58734b58510f839fb1c2ae2afdd8b06899452e7b4626f11d3f7fc3a9a8`, matching the earlier media receipt.
- 37 exact native frames extracted: every half-second from 0 to 15 seconds, plus frame indices 1, 6, 12, 18, 24 and 908. Three labeled contact sheets cover the clip, with native/cropped inspection of the initial frame, metric close-up, P4 tooltip and lane close-up.
- Camera registration confirms 2× zoom on the metrics at 2.5–3.0 s, a return to the initial framing, then approximately 1.682× on the lanes at 7.0–7.5 s. The page does **not** implement this recorded camera motion as a UI gesture.
- The bottom three strips are clipped by the source window, so only their visible headings/subtitles are recreated; hidden content is not invented.

Everything inside the dashboard is HTML/CSS/SVG. The only raster within the reconstructed frame is an independently retrieved **Tahoe Day landscape photo**, used as the desktop wallpaper surrounding the window. No video frame or dashboard screenshot supplies the dashboard background. `original-frame.png` belongs only to the explicit comparison layer, outside `#replica-frame`.

Typography is locally served Inter, selected after actual browser comparisons against installed SF, Arial and Geist candidates. The original font cannot be conclusively identified from this compressed clip; Inter is a reconstruction choice, not a claimed source-font identification. No compression grain or video ringing was added.

### Motion evidence, not a new telemetry simulation

The source visibly contains circulating flight glows, transient expanding event rings, changing lane counters/tool mixes and an observed P4 tooltip. The implementation replays **six matched angular tracks from 0–1.5 seconds**, using measured native-frame positions, interpolated between observations. Other glows, counters and text stay at the first-frame fixture. Playback is paused initially, explicitly user-controlled, and pauses on a new reduced-motion preference. The 1.5-second replay boundary is a study loop, not a claimed source animation period.

Transient ripple choreography, all later counter changes, pointer movement and their exact event timing are **not reconstructed**. The screenshot target remains the initial frame. P4 tooltip content was directly readable: “P4 · Breadth census”, “68.6% done · 648 done · 296 open”, “12 in flight · 14 blocked”. No unobserved P0–P9 tooltips or operational actions were invented.

## Issue #5 binding seam

The current issue body was refreshed and saved with its comments response: `updated_at=2026-10-10T21:52:26Z`, zero declared/fetched comments. Its only attachment is the video. There are no data-flow image attachments in that version; its mockup is the text pipeline and the component tables.

`web/video-replica/bindings.mjs` and `bindings.d.mts` separate `reference-fixture` from explicit, provenance-bearing `source-bound` values. `acceptSourceBinding` is a **pure validation seam**, not an authority check or connected collector. It rejects fixture promotion, missing provenance and known percentages without a positive denominator; null, false and zero are preserved. There is no automatic mapping from reference finance/commercial labels to CompanyOS facts.

| Video region / issue motif | Issue-defined widget and meaning | Existing owner / future binding | Source lines |
|---|---|---|---|
| Rings | ObjectiveRing / ReadinessBand; objectives/workstreams, declared vs independently verified outcomes, missing coverage | Candidate `objectives[]`; z0intelligence State Packet #22/#137 and outcome lineage #54, through existing CompanyOS #2 / PR #3 snapshot | 43, 164, 178, 191–192 |
| Headline, trends, cards | OutcomeDelta / MetricStrip; exact-window outcome deltas, blockers/approvals/coverage/active lanes/measured economics | Existing snapshot/source IDs; Tokenomics owns cost. The issue does not assign one real source to each of the six video cards | 44, 165–166, 211 |
| Lane matrix | FactoryLaneMatrix; task/owner, last useful event, wait reason, supported ETA and verifier state | Candidate `workstreams[]`; Hermes/OMP, Linear/GitHub and z0intelligence #47 | 45, 167, 180, 193–195 |
| Compact rails (not added to this frame) | WhatChanged / AttentionQueue; consequential deltas and human decisions | Candidate `attention_items[]`; existing AODL/Hermes/Linear authority path | 46, 179–181, 196–199 |
| Relationship displays (absent here) | DependencyLens / RevOpsFunnel; source-scoped PR dependency or cohort comparison | Existing canonical dependencies; RevOps remains unconnected, not assumed available | 47, 51, 55–65 |
| Hidden detail | EvidenceDrawer / ResolutionLens; known/unknown/conflict/next probe | State Packet → evidence lineage → original canonical source; reference P4 tooltip is not evidence | 48, 88, 169 |
| Meeting scratch (absent here) | CompareBranch / ImpactPath; reversible hypothesis with preview/Back/restore | Pinned existing snapshot/intent/source IDs; AODL remains authority | 49, 35–37, 93–114 |

The issue's original pipeline is preserved in the artifact below the composition: z0live/host voice → Ripple clarification → AODL scope/authority → z0intelligence State Packet → CompanyOS allowed snapshots/source IDs → OpenUI catalog proposal → host validator → existing CompanyOS renderer → preview/verify/present-or-discard → z0evals/Evolution Lab.

No live mode is claimed. This visual study does not fulfill the issue's future live architecture backlog. It creates no new backend authority and never requests the snapshot API.

## Executed verification

```sh
node --test tests/video-replica-bindings.test.mjs
python tests/test_video_replica.py
# Python environment with playwright and pillow:
python scripts/verify_video_replica.py --artifacts /path/to/receipts
```

The browser verifier owns a port-0 loopback server and an isolated headless Chromium profile, asserts real HTTP/browser behavior, writes screenshots/JSON, and shuts down only its own test server. It never attaches to Zen. 28 browser/HTTP assertions passed, including exact original-frame pixels, native geometry, both full images in side-by-side, opacity keyboard input, tooltip hover/focus/Escape, play/pause/reset/reduced motion, no external/API network requests, and no console/page errors.

RED→GREEN receipts include the missing initial server, the missing binding module, the side-by-side clipping bug at native size, and the known-percent-without-denominator rejection. A remote browser helper rejected loopback navigation, so real local Playwright/Chromium produced the evidence instead. Jev returned `no_key`; no model-selected GUI result is claimed.

### Quantitative visual result — not pixel-perfect

Unregistered native RGB comparison, no alignment/rescaling to improve scores; H.264-decoded source vs clean-vector browser output:

| Region | SSIM | MAE (0–255) |
|---|---:|---:|
| Full 1496 × 1080 frame | 0.809573 | 7.89755 |
| Dashboard only | 0.829166 | 5.94243 |
| Rings | 0.860269 | 9.64448 |
| Headline + metrics | 0.772832 | 6.79407 |
| Lanes | 0.818531 | 6.07538 |
| Header | 0.825369 | 6.58308 |

The first rendered component pass scored 0.777897 dashboard SSIM. Successive native render iterations, overlays/crops and measured circle/text diagnostics improved it to 0.829166. Large flat dark areas influence this metric; it is not a “percent pixel-perfect” claim.

**Residuals:** exact font identity/metrics and subpixel text rasterization; some card/pill padding and tiny labels; exact bloom, orbit-tail intensity and satellite/ripple state; compressed hairline edges; peripheral wallpaper water/rock details and source-frame registration. These remain visible in the comparison controls. Full event/ticker playback is intentionally incomplete as described above.

## Evidence home and ownership

`/workspace/zer0/data/operations/company-os-recovery/video-replica/` contains the source video, ffprobe/extraction hashes, all 37 native frames, three contact sheets, full issue body/comments, ring/color/flight/camera measurements, actual browser captures, iterative overlay/difference/crop metrics, test JSON and final report.

Owned worktree: `/mnt/zer0models/z0-wt/company-os-video-replica`, branch `design/company-os-video-replica`, based on `248126ebc5004e6430d3ebe1cc4c9340770d8dfe`. Existing integrated worktree/server on port 18747 is untouched. No push, merge, production/profile edits, or model-serving inference was performed. The parent may open the verified route in Zen; this verifier did not take over the user's desktop.
