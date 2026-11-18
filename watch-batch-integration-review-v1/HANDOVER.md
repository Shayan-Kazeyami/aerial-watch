# Watch batch integration review, not a release

Base: main b84a51ec91b715aa70408e8bff6e988e29d93edb. Local branch codex/watch-batch-lifecycle-review. Public loader and sealed e79b release unchanged. `build_stage.py` creates a separate local review directory with exactly one changed application module. Its inherited deployment manifest is deliberately NOT a valid candidate release manifest; do not publish it.

Combined changes: active scene/render-state lifecycle guards plus source geometry revision invalidation. Changed attribute/index identity, array, version/layout, draw range, groups or any populated morph attributes fall back to authoritative meshes. Raw CPU writes without needsUpdate are outside the contract. No source geometry is edited, no 421-object acceptance is implied, and no particular reported user symptom has been attributed to these defects.

32 real-Three tests pass on the combined module. Independent reviewer additionally imports the actual staged module. Historical repository regression invocation gave 20 pass and 2 failures in unchanged tests: crown fixture imports a missing local module; loading-v3 asserts an outdated dca5 release ID. The complete log is preserved, not rewritten to appear green.

Browser/GPU acceptance is not complete. Playwright bundled Chromium absent; attempted download returned invalid/truncated archive. Installed system Chromium fails its process socket in the restricted execution environment. No actual WebGL images, performance, device interaction or complete application acceptance claimed. New immutable release generation and browser/device quality checks remain required before any deployment. Stable branch is untouched.

To restore: obtain repository at the pinned base, copy this review folder, run `python build_stage.py`. Candidate test and independent audit folders are included separately in the combined backup. The stage is reproducible from the base; no 95 MB duplicate stage is included.
