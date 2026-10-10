# v3 style preview

This is a **static visual recovery**, not a second dashboard or an alternative telemetry source. The existing plugin, backend, generated browser bundle and historical `web/index.html` remain unchanged. No preview code is imported into the live route.

## Run

```sh
python scripts/style_preview.py                 # OS-assigned loopback port
python scripts/style_preview.py --port 18744    # explicit port; collision fails
```

The server prints a JSON receipt with the actual URL, port and PID, then stays in the foreground. Open its `/style-preview/` URL manually. It never auto-opens a GUI, starts Hermes, changes profiles or calls an upstream API. Ctrl-C/SIGTERM stops it. Only the exact preview asset allowlist is served; filesystem browsing and mutation methods are rejected. CSP disallows all network connections (`connect-src 'none'`). External reference links are ordinary user-initiated navigation.

## Test

Use Python with `requirements-style-preview-test.txt` and an installed `/usr/bin/chromium`:

```sh
STYLE_PREVIEW_ARTIFACTS=/absolute/evidence/directory \
  python -m pytest tests/test_style_preview.py -q
node --check web/style-preview/preview.js
```

The single pytest command owns its test server/browser and cleans them up. It does not attach to the manual preview or the live diagnostic. Real Chromium covers dark/light, persistent and unavailable localStorage, native keyboard disclosures, anchor navigation, loaded local fonts, no off-host/API requests, HTTP errors, six viewport sizes from 320 to 1536 px, no overflow/animation/progressbar, text-token contrast and actual corner-bracket pixels. The separate server CLI test verifies loopback bind, allowlist, mutation rejection and occupied-port refusal. Screenshots are review evidence, not a claim of automated pixel-identical fidelity.

## Visual lineage

- `3f3fea2ce766e2ab85ce93e82da8610835c0aad6:web/index.html` / `docs/architecture/hud-theme-v3.png`: sparse composition, #0a0a0a surface, IBM Plex type, 220 px left rail, concentric dot rings, light center, bracket corners, diamond/circle nodes and three role rows.
- `3d0f6eb3e2495bb46f232f4994a0902541fd0d5a:web/index.html`: historical ownership names and non-authority boundaries, not a current runtime inventory.
- `docs/inspo/hud-dark-cockpit.jpg` / `hud-light.jpg`: fine vector icon/connector language and warm light inversion. No JPEG grain, raster overlays or noise.
- [CompanyOS #5](https://github.com/kvnloo/company-os/issues/5): the new north-star issue. At recovery time its body explicitly says the original conversation-upload clip has no public video attachment/link. No frame inspection or video-derived styling is claimed. A real URL/upload is required before borrowing anything from it.

Truthful deviations from the historical still are intentional: no fake clock, “everything calm”, listening waveform, activity bars, progress percentages or working composer. Header, center and footer explicitly identify static historical architecture. Dashes mean not observed; no counts are inferred. The lower rounded control is a working source-notes link, not a pretend chat input.

## Reusable boundary

`web/hud-v3.css` contains namespaced `--hud-*` dark/light tokens, typography, brackets, panel/rail, dotted-ring SVG treatment, node symbols, role disclosure, compact metric labels and responsive layout. The root `data-hud-theme` selects appearance; `preview.js` only persists that visual preference. Fonts are locally hosted with upstream licenses.

Later integration should adopt these presentation primitives around the existing bounded projection model—not import the static role labels as current state, replace the authority graph, coerce unknowns or create a new backend. Map the font URLs into the host's sanctioned asset route during integration. Source freshness, unknown/stale/degraded semantics and read-only boundaries must remain with the existing dynamic components. This style-only phase makes no deployment/activation claim.
