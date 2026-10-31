# Atelier review checkpoint — 31 October 2026

## Published checkpoint

- Source: `068b20c943372e9bb96b9c4f376d19106b26c764`.
- Main preview subtree: `b3ccff10d4b3a8946d3e2f111418c9928c44eefb`.
- Source CI: https://github.com/Shayan-Kazeyami/aerial-watch/actions/runs/41250839930 — passed.
- Pages: https://github.com/Shayan-Kazeyami/aerial-watch/actions/runs/41250947963 — passed.
- Preview: https://shayan-kazeyami.github.io/aerial-watch/preview-b/atelier-preview.html?face=svg04&leather=craft

This is a review checkpoint, not launch acceptance. Main homepage remains unchanged.

## Observed locally

The live model was exercised in a dedicated software-WebGL browser. This proves functional compatibility in that environment, not performance on a client GPU.

- SVG04 constant-section crescent and R10 leather loaded; exported diagnostics identify both revisions.
- Crown pull/push and direct drag changed the time without orbiting the camera.
- Exploded assembly separated and reassembled.
- An exploded amount of 0.55 was saved, reset, restored and saved again. Camera, crown, clock, options, explosion, inspection state and setting offset compared exactly equal.
- PNG output decoded at 1180 × 503 with actual watch pixels; embedded source identity verified. Local capture adapter copied generated Blob bytes. Normal browser download delivery is a separate, unverified check.
- Eight-second video request generated a 32,186-byte VP9 WebM with only two decoded frames and about 4.01 seconds between packets. This is **unusable**, not a video-export pass. Local recorder validation now rejects such obviously sparse output; it does not turn the slow render into a smooth video.

## Fixes following inspection

- Successful JSON import synchronizes the task dock and exploded slider without changing restored model/camera state.
- Desktop removes duplicate status text inside tool panels; mobile feedback and the global accessible live region remain.
- Recorder reports requested settings separately from elapsed capture time and measured WebM packet timestamps. Unsupported layouts remain unverified. Structural inspection is not a video decoder or a guarantee of smooth playback.

## Renderer trial

Three.js r187 was tested separately from the published r180 build. Smooth and Sharp modes rendered the model; live diagnostics reported revision 187. Requesting Studio mode was followed by a software GPU-process exit. The r187 trial is **not promoted**. No WebGPU adapter was exposed in the cloud browser, so no WebGPU speed comparison is claimed.

## Still open

- Premium lighting/material acceptance, including sapphire at grazing angles and readable blued hands.
- Real-device mobile, touch and GPU performance testing.
- Studio-quality and r187 stability on hardware rendering.
- Normal download/file-picker delivery and a smooth full-length motion recording.
- Integrated mobile visual review, repeated interrupted interaction paths, and final site embedding acceptance.

Geometry clearance audits are visual/static/sampled evidence, not manufacturing or full physical certification. Existing source attribution and license remain applicable.
