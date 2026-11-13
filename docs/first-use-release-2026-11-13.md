# First-use touch hint release — 2026-11-13

Release: 7bff24707c244be0a28d8731300db86a183696552a1e76f3af53b99c74e76670
Source QA: 74f3a071c48fbe67e35620de336ee19c86d9a47c
QA run: https://github.com/Shayan-Kazeyami/aerial-watch/actions/runs/43393436311
Rollback: main 0372398e022bee1b902779748c588638dadfbcc2 and watch-home-memory-7455e960.js.

A single noninteractive "Drag to explore · Pinch to zoom" status cue appears after readiness on coarse-pointer first visits. Dismissed after intentional touch movement, multitouch or eight seconds; remembered locally. No focus capture, canvas resizing, new render loop, SVG hit-test overrides or renderer changes.

## Verified
- Actual rendered 390×844 portrait and return-visit 844×390 landscape PNGs inspected. Cue is compact, legible and does not overlap watch or action dock.
- Passive pointer listeners, pointer-events none, role status, no animation; focus stays on body.
- Readiness gating; one timer; movement threshold; multitouch; persistent dismissal; timeout; hidden/resume; panel pause; fine-pointer exclusion; blocked storage; disposal.
- Browser touch-emulation: cue dismissal then Explode and Reset, no replay after reset/reload, stable canvas bounds, zero paused additional frames, no JS errors.
- Deterministic release builder validates hashes and byte sizes across local/shared closure.

## Limits
Physical-phone FPS and assistive-technology speech were not measured. Existing landscape header/dock consume substantial space; not changed by this scoped cue release. This cue adds no persistent control.

## Negative finding retained
Zero-duration CDP drag can suppress next native click even in a minimal HTML fixture. Pacing input fixes the test. QA no longer injects pointer-events CSS; do not publish speculative SVG workaround from qa/touch-target-20261113.
