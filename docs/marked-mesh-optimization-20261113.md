# Marked strap-end and lug density optimization — 2026-11-13

Scope: the user-marked rolled leather end and adjacent case lug tips, mirrored to the opposite end. Based on release `832a0ce0005cffdf950455dcb578c805724bf92d29a81f9ca209ab59efdead51`; preserves that release's landscape/mobile UI.

| Mesh/primitive | Before triangles | After triangles |
|---|---:|---:|
| Case with integrated lugs | 350,230 | 287,622 |
| Upper leather outer | 107,920 | 102,816 |
| Upper edge paint | 13,239 | 11,527 |
| Upper lining | 22,933 | 20,173 |
| Lower leather outer | 68,380 | 63,588 |
| Lower lining | 21,542 | 18,732 |
| Lower edge paint | 13,217 | 11,561 |
| **Affected mesh total** | **597,461** | **516,019** |

81,442 fewer unique triangles (13.63% of affected meshes). This is not the full watch count and does not imply a draw-call decrease. The 438-call assembled QA comparison kept draw calls unchanged; rendered triangle accounting includes multiple passes.

Leather geometry.bin shrinks 8,579,970 → 8,084,280 bytes; compressed case shrinks 4,017,662 → 3,446,952 bytes, saving 1,066,400 bytes combined. No texture changes.

## Protection and evidence
- Only strap vertices with source y > −5 mm and case vertices with |z| > 19 mm were eligible. Springbar bores/contact area within 1 mm of axes (y=−0.95, z=±22.4) were additionally locked.
- Unrelated surfaces and original sewing geometry retained. Material/identity labels updated together; actual loaded geometry bytes are verified, not just a version label.
- Attribute-aware simplification weights normals strongly (4,4,4) and UVs (0.1,0.1), preserves seams, borders and folds. Iterative neighborhood locks prevent new degenerate/flipped-normal triangles and new welded boundary/non-manifold edges.
- An earlier aggressive-normal candidate was rejected because actual macro renders showed tip highlight faceting. The accepted candidate preserves smooth tip shading.
- Independent bidirectional deterministic sampled surface-distance checks: case maximum sampled error 0.01132 mm, leather maximum 0.00989 mm. These are sampled bounds, not exact Hausdorff or manufacturing tolerances.
- Chromium SwiftShader 430×932 DPR3 Smooth: matched cameras and paused animation, assembled/close-up/upper/lower lug comparisons, explosion/reset and motion checks. These prove rendered consistency and functionality, **not real-device FPS**.

Reproduction scripts are under `marked-mesh-qa`. QA evidence is in the GitHub Actions artifact for the final marked-mesh run. Source geometry adaptation retains the repository's Openmovement attribution and CC BY-SA 3.0 terms. No manufacturing or full-contact certification is claimed.
