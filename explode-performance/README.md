# Exploded-view CPU work reduction (2026-11-12)

Status: implemented and unit/invariant verified; NOT deployed; browser visual acceptance remains pending.

## Identity / coordination
- Public main index read through GitHub on this turn still selects immutable release `1b013b90cdd2d448fbe5c88bc90e28786ba3424600fb43d35ddabed0707d9158`.
- Baseline `assembly-explode.js` SHA-256 `8ebcd02fa1f7f7b7ae17365df206937eb09266db6b14c5ff20e54a193abd4240` matches that release's manifest exactly.
- Candidate SHA-256 `4feb893027cb9520e9c17ce47e5bdf70de9c8e0316ed92aca44e351203ed8f3a`.
- Changes only this module. No geometry, materials, loader, branch, deployment or approval changes made.
- Separate geometry worker has a pending GitHub blob approval. This work does not retry or bypass it.

## Change
Reuse parent-axis calculations in a WeakMap, invalidated by exact parent-world-matrix or root-axis changes. Reuse the scratch inverse matrix. Avoid writing unchanged wrapper transforms. Per-frame parent world transform updates remain, so nested/animated/scaled parents still work. New/removed parents are not pinned by the weak cache. No meshes, material settings, animation duration, layers, raycasting identities, or authored matrices change.

## Verification
`node --test explode-performance/tests/*.test.mjs`

Nine tests pass:
- Seven existing real Three.js r187 explosion tests (all 166 parts, exact local matrices/geometry, child order, tween reversal, repeated scrubbing, late arrivals, disposal, parent/root motion).
- Differential baseline/candidate test: 240 steps, 166 parts then late-added dial; root translation/rotation/nonuniform scale, 8 moving parents, a singular parent scale and recovery, scrubbing, resets and disposal. World positions agree within 1e-10 and authored matrices agree exactly.
- Operation test: 600 settled frames, 166 parts and 8 shared parents. Baseline 4,800 Matrix4 inversions + 99,600 wrapper matrix writes; candidate zero + zero after warm-up. This measures removed CPU operations, NOT phone FPS or GPU time.

## Remaining release gate
`browser-check.mjs` prepares a matched baseline/candidate public-release render test with route-local candidate injection; assembled/exploded/37%/reassembled states, mobile 430x932/DPR1/Smooth. It uses the existing installed Playwright package. Chromium failed before navigating because this executor rejects socket() with Operation not permitted, including the approved outside-sandbox attempt. No visual pass claimed. `browser.log` captures this.

Run this test on an execution environment where Chromium can launch, inspect screenshots and compare states/errors. Then seal the changed module with manifest/revision receipts against the latest main; rebase onto pending geometry if merged first. Do not mutate the existing immutable release. Verify exact candidate CI, release and live public bytes before claiming shipped.

Additional hotspot noted but not changed: assembly-review calls registerExplosionParts() (full model traversal + mesh array allocation) on every active exploded frame to catch late additions. Removing that requires explicit topology invalidation across asynchronous replacement paths, so it should be a separate measured change.
