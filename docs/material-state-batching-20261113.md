# Material-state-aware mechanism batching,2026-11-13

Baseline main `4193c7b`, release `b38ddef3`. New immutable release `3e9e591cbf61eaabb0b8dc9909c157514c9d14144b0dabdaa8543c368d0f4466`.

## Verified problem and change

The mechanism's three render batches held the original finish material identity. Turning Finishes off switched all 166 source meshes to a shared clay material, bypassing the batches entirely. The candidate chooses the largest compatible opaque material cohort within each existing batch, reusing all geometry buffers. Exceptions retain original meshes/materials; transparent/transmissive material states bypass batching. Source meshes remain authoritative for picking, motion and exploded transforms; hidden render sources are restored in finally. No geometry or visual-quality setting changes.

## Evidence

Current baseline probe 43408503827 and candidate A/B43409122657:

| State | Baseline calls | Candidate calls | Triangles before/after |
|---|---:|---:|---:|
| Smooth, Finishes off |222|69|1,590,762|
| Studio, Finishes off |668|209|4,756,947|
| Smooth, Finishes on |132|132|3,172,191|
| Studio, Finishes on |275|275|6,344,392|

Counts cover the entire composed frame, including repeated render passes, not unique source polygons. Existing batch buffers remain 19,044,930 bytes; no additional geometry buffers were introduced. Default-view performance is not claimed improved.

Unit tests cover repeated swaps, minority material exceptions, glass/transparency, material mutation, source restoration and disposal. Six browser A/B states cover Smooth/Studio, assembled/exploded and finish changes. Largest mean screenshot difference 0.04172/255; at most 0.0851% of pixels differ by more than 8/255, localized raster/shadow differences. Actual source/clay screenshots visually inspected. Triangles unchanged in every paired test. Tests use Chromium SwiftShader; they do not establish hardware-phone FPS, battery life or WebGPU parity.

Exact immutable release is validated separately before switching production. Previous release and recovery backup are retained.

Exact immutable-release gate 43411711104 passed at commit `0ca50dd78a9e46f2bf6b773f5b702ac4e93a4c18`. Final renderer-only screenshots excluded only the independently pulsing DOM crown affordance (not geometry); maximum mean pixel difference was 0.00232/255 and at most 0.01163% of pixels differed by more than 8/255. An earlier comparison correctly failed because it included different phases of that overlay; the threshold was not relaxed. Both finished and clay renderings were inspected.

A separate conservative broad-leather density study found the center faces already sparse, with most vertices concentrated in shoulder/bevel strips. Normal/UV-aware simplification preserving seams, silhouette, stitching and bevel boundaries removed only two triangles at 0.008 mm. That candidate was rejected; further savings need authored retopology rather than blanket decimation.
