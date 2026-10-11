# CompanyOS reference-motion study

**Scope:** offline measurement and a source-labeled reference prototype, not a live CompanyOS implementation and not completion of issue #5's product roadmap. The original replica worktree and its port 18748 remain unchanged. This branch extends that baseline in an owned worktree; its server uses port 18749.

- Preview: `http://127.0.0.1:18749/motion-reference`
- Full native fixture: `http://127.0.0.1:18749/video-replica?native=1`
- Evidence root: `/workspace/zer0/data/operations/company-os-recovery/motion-analysis/`
- Main source: user-supplied video [7], SHA-256 `84a29e4fafea04c7a4b945f7db4f6c5b09877ba8996572d244662996093063b5`.
- Source: 1496×1080, 60 fps; **909 decoded frames**, 304 analyzed samples including frame 908 at **15.133333 s**. This endpoint is the last frame's PTS, not an assertion that the container's total duration equals that PTS.

## Research and method selection

No single flow estimator is optimal for this clip. The useful order is **register first, measure residual change second, interpret last**.

1. **SIFT correspondences + robust similarity fitting:** frame-zero component regions, ratio-test matches, partial-affine RANSAC; retain original coordinates, mapped polygons, inlier counts and median/p95 residuals. A full homography is also estimated but retained as a diagnostic rather than selected automatically. OpenCV's feature/homography tutorial provides the matching/RANSAC approach [2]. The low-degree-of-freedom similarity model is a deliberate choice for a flat screen with scale/pan; it is not adequate for grid reflow.
2. **Independent anchors:** compare fixed wallpaper/header, common content and five component transforms. Fixed wallpaper can dominate global consensus while the content window zooms. Publication prefers agreement across independently fitted components and exposes a recording-transform toggle. Scroll versus recorder pan remains underdetermined when fixed anchors leave the crop.
3. **Actual sparse and dense flow:** run Lucas–Kanade forward/backward checks between sampled frames; run Farneback on registered component crops. These are diagnostics, not inferred CSS trajectories or physical velocities. Brightness/appearance changes and glow violate simple motion assumptions; the OpenCV optical-flow treatment motivates these limits [1].
4. **Residual segmentation:** native registered frame differences, threshold 14, small morphological opening and connected-component boxes; valid-pixel masks exclude offscreen areas. Thresholding is applied to isolate changed regions, not to classify their business meaning [3].
5. **Ring tracks:** sample ten measured radii at 0.5° angular spacing; subtract the temporal 35th-percentile brightness baseline; detect peaks; geometrically link same-ring candidates with a gated assignment. Split across gaps over 110 ms. Track IDs are not source item identities.
6. **Text and chart state:** run local Tesseract every 0.5 s, grayscale inversion/2× cubic scaling/PSM 11; save raw TSV and native word bounds/confidence. Scaling, contrast and segmentation choices follow Tesseract's quality guidance [5]. OCR remains candidates. Human-readable lane-summary samples are a separate source-labeled sample-and-hold track; no interpolated counter values. Colored sparkline centerlines are segmented before late reflow; later chart samples are intentionally not fabricated.
7. **Easing candidates:** SciPy robust bounded least squares [4] compares linear, smoothstep and power-in/out against observed scale. The replay uses measured samples, **not the best-fit curve as an assertion about original CSS easing**.

Synthetic transform/linking tests verify algorithms; they are not evidence about the video. All source measurements use decoded native BGR pixels. JPEG review images are separate hashed derivatives.

## What was measured

Raw results: `tracks.json`, `decoded-frame-manifest.json`, `ring-intensity.npz`, `flight-tracks.json`, `ocr-candidates.json`, `tooltip-track.json`. Published playback: `timeline.json` and `web/video-replica/motion-timeline.mjs`. Machine-readable distinctions: `events-and-confidence.json`, `analysis-summary.json`, `observed-states.json`.

| Component | Raw fitted samples / 304 | Median sample p95 reprojection residual |
|---|---:|---:|
| Rings | 254 | 1.150 px |
| Outcome | 292 | 0.974 px |
| Metric region | 304 | 0.929 px |
| Lanes | 259 | 1.150 px |
| Header | 204 | 0.505 px |

These residuals describe **inlier feature fits**, not whole-component pixel accuracy. The publisher rejects fits with fewer than eight inliers and rejects the late metric-region affine model. Missing fits are explicitly held-last-visible, not silently promoted to observations.

- **304 linked glow tracks, 6,634 accepted linked samples**; longest track 149 samples. Geometric associations may include collision/occlusion edges or expanding events. No claim of 304 distinct source objects.
- **220 pointer-positive samples**. Template identity and location do not prove click, hover or input causality.
- Common-window zoom threshold-positive intervals: **1.90–3.65 s** and **6.20–8.10 s**. These are detector-positive bounds, not true onset/offset measurements; blurred/failed matches obscure the start of the first zoom.
- Content-scale/reflow detections extend from **10.10 s to the last sample**. Native frames 630 and 660 visibly show browser-zoom popups **50%** and **67%**. This supports browser content reflow distinct from recorder-only magnification; exact input method is unseen.
- P4 tooltip positives: **4.05–4.10**, **4.95–5.05**, and **5.20 s**. Only six template positives; false negatives prevent a reliable complete hover duration. Visible text at frame 300: `P4 · Breadth census`, `68.6% done · 648 done · 296 open`, `12 in flight · 14 blocked`.
- Lane-summary observations and two readable lane orders are replayed. The summary is no longer frozen to frame zero: frame 660 reads **19 agents, 22 tool calls/min, 9,531 tokens/min, 0 files edited/min, 4 commits/h**. Changes are known only between readable observations. Ambiguous/blurred samples are omitted.

The 50 ms measurement grid is **not** an event-timing error guarantee. OCR's 500 ms spacing gives still less onset precision.

### Easing results and rejection limits

`selected-window-easing.json` records all tested models and residuals. Best candidates:

| Fitted scale window | Candidate | Scale RMSE | Max scale error |
|---|---|---:|---:|
| 1.85–2.35 s | power-out, exponent at upper bound ≈8 | 0.0656 | 0.2053 |
| 2.95–3.75 s | smoothstep | 0.1007 | 0.1864 |
| 6.15–6.90 s | power-out, exponent ≈2.985 | 0.0224 | 0.0605 |
| 7.60–8.20 s | power-out, exponent ≈1.752 | 0.0408 | 0.0930 |

The first fit hitting its bound and the large residuals are evidence **against identifying an exact source easing**. The later fit is a useful image-space approximation, not proof of a particular library or input sequence.

## Prototype behavior and remaining fidelity limits

Working: full-sequence play/pause/scrub, Home/End and 50 ms arrow-key scrub, non-looping endpoint, reduced-motion pause, exact initial reset, recording-transform on/off, original/overlay/side-by-side comparison with synchronized source-video seeking. The replica itself remains HTML/CSS/SVG; only the authorized wallpaper is a raster inside the replica root. Video is confined to explicitly selected comparison layers.

**Measured/replayed:** component/common transforms, accepted glow positions, selected chart centerlines, pointer/tooltip candidates, observed summary values and lane order changes.

**Approximated:** rendering glow shape/brightness, interpolation between measurements, grid sizing after browser zoom, lower-panel appearance, sample-and-hold text transitions and geometry held through missing fits. Static font substitution and first-frame baseline differences remain.

**Not fully reconstructed:** expanding event rings and all event-label lifetimes; every lane's tool mix/status/timer change; late sparkline data; complete lower live-feed text; exact browser-popup lifetimes and controls. Source-video comparison preserves the entire visible sequence for inspecting these gaps. This is not a claim of pixel-perfect or semantically complete reproduction.

**Unobservable:** actual backend data flow, event dispatch, polling cadence, hidden content, exact user input, original CSS easing and identities across occlusion. The source's visible “sampled every 3 s” text is just a displayed label, not independent proof of a poll interval.

## Verification and fidelity

`test-runs.json` records real commands, outputs and exit codes. The final verification gates passed **9 Python tests (including actual-source integration), 4 Node tests and 32 real-browser checks**; all six verification commands exited zero. The scoped suite includes actual-clip decode/publication integration, transform/linking/OCR regression tests, exact-sample/endpoint discrete state, timeline tests and HTTP range seeking. `browser/browser-tests.json` records real isolated Chromium tests, not parser-only or mocked browser evidence. No everyday browser or native Tern session was attached.

Browser checks cover the full endpoint, 13 nonzero scrub positions, controls, summary/order changes, focus, reduced-motion preference changes, camera separation, no invented loop, exact reset raster, synchronized source video, composition raster restriction, and no operational/external requests. A retained Chromium paint-layer issue was isolated with identical DOM geometry but stale clip/SVG pixels; reset now reattaches the same layer after one layout flush, preserving nodes/listeners and producing **zero changed pixels**. Comparison video required proper HTTP byte ranges; the owned server now supplies them.

Native RGB comparison uses exact source frame indices, DPR 1, no image registration/resampling. `fidelity.json` includes 14 captures and regional SSIM/MAE; `browser/full-sequence-comparison.jpg` shows source and replica side by side. The control is the **preserved static first-frame replica**, not a claim to benchmark its old 1.5 s motion loop.

Representative dashboard SSIM: 2.5 s **0.799 vs 0.521**, 7 s **0.793 vs 0.504**, 11 s **0.744 vs 0.577**, endpoint **0.712 vs 0.549** (motion replay vs static control). Frame zero is unchanged at **0.829**. Dark areas inflate SSIM; this is a regression metric, not perceptual acceptance or complete motion correctness. Late reflow and dynamic lane details remain the largest visible gaps.

## Issue #5 boundary and credit

The full issue body and comments were retrieved read-only into `issue5.json`/`issue5.md` [6]. This study preserves its requirements: fixture/reference values are not CompanyOS facts; no new authority, live backend, scheduler, ledger, provider calls, or operational mutations; existing owner/adapter labels remain unconnected. It does not claim completion of conversational meeting composition, six host-data fixtures, two production scenes, 100 lifecycle cycles, live Tern proof, p95 interaction benchmarks, or decision-quality A/B/C experiments.

The clip is user-provided WOLFSUITE inspiration. Its original designer remains unknown; no guessed attribution. CompanyOS owns future shell/widget presentation; existing canonical systems retain data/voice/intent/execution authority as specified in the issue. No remote issue/PR writes or changes to the original/sibling servers were made.

## Reproduce locally

Prerequisites: Python, uv, FFmpeg/ffprobe, Tesseract, Node and `/usr/bin/chromium`. Exact Python dependencies are in `scripts/motion-requirements.txt`.

```bash
cd /mnt/zer0models/z0-wt/company-os-motion-reference
OUT=/workspace/zer0/data/operations/company-os-recovery/motion-analysis
uv venv "$OUT/.venv"
uv pip install --python "$OUT/.venv/bin/python" -r scripts/motion-requirements.txt
# reference.mp4 is preserved in OUT and web/video-replica/assets/reference.mp4.
"$OUT/.venv/bin/python" scripts/motion_analysis.py \
  --source "$OUT/reference.mp4" --out "$OUT" --stride 3 --max-frames 1000
"$OUT/.venv/bin/python" scripts/run_motion_verification.py --out "$OUT"
"$OUT/.venv/bin/python" scripts/reference_motion.py --port 18749
```

The analyzer is source-region-specific, not a general video understanding service. `measure_motion_fidelity.py` uses the preserved original `video-replica/browser-native.png` as its static control. Server health and ownership are recorded in the external `RUN-RECEIPT.json`; stop only that recorded owned PID/process.

## Sources

- [1] OpenCV, Optical Flow: https://docs.opencv.org/4.x/d4/dee/tutorial_optical_flow.html
- [2] OpenCV, Feature Matching + Homography: https://docs.opencv.org/4.x/d1/de0/tutorial_py_feature_homography.html
- [3] OpenCV, Image Thresholding: https://docs.opencv.org/4.x/d7/d4d/tutorial_py_thresholding.html
- [4] SciPy, `least_squares`: https://docs.scipy.org/doc/scipy/reference/generated/scipy.optimize.least_squares.html
- [5] Tesseract, Improving the quality of output: https://tesseract-ocr.github.io/tessdoc/ImproveQuality.html
- [6] CompanyOS issue #5: https://github.com/kvnloo/company-os/issues/5
- [7] User-supplied attachment: https://github.com/user-attachments/assets/18dc5eb2-e513-4486-a33b-5937f8d176ef
