# Unexecuted isolated hub GPU fixture
Prepared only, no browser or remote execution/upload. See sibling hub-render-validation-plan/PLAN.md for hypothesis and acceptance limits. Source/candidate files are copied with exactly one import rebase, never edited upstream. Exact e79 manifest/source/vendor hashes verified by prepare.py; actual candidate pin8b7034… unchanged.

Preparation: python watch-qa-infrastructure/hub-render-validation/prepare.py
Static unit contracts: python watch-qa-infrastructure/hub-render-validation/test_preparation.py
Syntax: node --check watch-qa-infrastructure/hub-render-validation/fixture.js; python -m py_compile watch-qa-infrastructure/hub-render-validation/run.py

Browser entry point run.py is intentionally NOT invoked. It requires a separately authorized browser-capable QA environment and HTTP server rooted at fixture/ on127.0.0.1:8765. No local sandbox bypass. Independent review before any remote packaging/execution. The prepared workflow is read-only, single-run,15min QA-only; no installation or upload has been executed during preparation. At most one reviewed300s browser arm, with30s operations,60s screenshots, normalclose30s. Ten ROI pairs/30 PNGs; exact direct pixel checks, no page/GL errors, actual renderer/backing dimensions,20 disposal cycles with source redraw. Reports acceptance field means isolated fixture only, not release acceptance; manual zoomed image approval still required. Screenshot timeout or close failure remain failure, no suppression/retry.

No actual browser/visual/GPU results yet. Static contract tests do not prove projected ROI threshold passes on a browser. Published vendor recorded here does not establish live viewer registration. Hardware/mobile/full-viewer/picking/UI/quality/release gates remain held; no FPS/triangle/GPUbyte improvement claim.
