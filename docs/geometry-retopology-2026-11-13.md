# Authored champagne wall and rim reconstruction

Date: 2026-11-13. Baseline runtime: 63600a544b71214dcbfceee96a3eac0dbfa48bca7d42d59425acd43bae131bfd.

## Scope and result
Only premium-face face-svg04 meshes 71 (champagne wall), 72 (aperture rim), 73 (lower rim lip). All other mesh accessor payloads, material assignments and transforms remain unchanged.

| Part | Before triangles | Candidate triangles |
|---|---:|---:|
| Champagne wall | 60,864 | 21,172 |
| Aperture rim | 19,456 | 6,080 |
| Lower rim lip | 19,456 | 5,888 |
| Combined | 99,776 | 33,140 |

66,636 fewer triangles (-66.8%). Meshopt transfer file 3,094,636 to 2,379,608 bytes (-23.1%). This is topology/transfer improvement, not a measured phone-FPS claim. Draw-call count is not reduced by these changes.

## Method
Reconstruct from authored swept profiles, not polygon-collapse decimation. Recover the wall's original 33-depth by 1,216-contour grid and retain all silhouette contour samples. Choose depth rows from positional and inherited-normal interpolation error; retain extra rows at curved transitions and cap/side normal discontinuities. Zip unequal adjacent row chains without T-junctions. Rim lips retain all eight cross-section samples while reallocating contour samples.

The wall has no UV channel; the lips' UV channels are preserved. Material and assembly identity stay unchanged.

## Evidence and limits
- Wall sample-to-surface maximum below 0.000281 mm in two directional sample sets. This is a sampled deviation, not a certified Hausdorff bound.
- Welded wall shell edges have two incident faces, with no candidate degenerate faces.
- Decoded packed raw arrays exactly match independent candidate POSITION/NORMAL/TEXCOORD/index arrays. Unrelated 170 accessor payloads preserved.
- Official existing meshopt pipeline verifies every decompressed buffer byte and non-storage metadata against input.
- Actual matched Chromium SwiftShader shaded and wireframe comparisons: QA run43462384945, including isolated part, macro and upper/lower transitions. Mean full-frame shading differences at tested cameras below0.023/255; not a proof for every view.
- Integrated release8da6179fe4cc360db298c64720b76933d2325d3a5c65b237aa7c83dc18178803 tested via raw and meshopt, portrait and landscape, actual loaded triangle counts, crown hold/reversal/release, no reload, movement layer focus/reassembly.
- Physical-device thermal, memory and FPS characterization remain separate work.

## Failed packaging candidates and safeguards
The initial packer keyed replacements by original accessor ID. Source lips shared an index accessor, so independent replacements collided. In-memory renders were correct, but packed GLB was not. Fixed by cloning primitive accessor ownership and pruning unused originals; decoded per-mesh equality and actual loaded counts now gate delivery.

A raw URL's version query bypassed an exact-path ownership override. Fixed matching against the normalized logical pathname while retaining query/fragment in resolution. Both raw fallback and compressed variant are shipped locally in the new immutable release; other owner routing is unchanged.

A raw-landscape interaction test initially captured the pre-gesture camera before residual settling. The rerun requires exact camera stability before input and retains exact during-gesture invariants. This does not change runtime quality or weaken movement checks.

Keep candidate validation distinct from public deployment. Verify the live loader, release identity and actual loaded geometry after promotion; retain previous immutable release for rollback.
