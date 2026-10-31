# Native sewn-leather study — R05

Local visual candidate only. Nothing committed, published, uploaded, or changed in the runtime viewer.

## Deliverables
- `seam-study-r05.blend` — packed Blender scene; original fitted replacements and stitches retained hidden.
- `seam-study-r05-macro.png` — 1100 square, 128 samples, prescribed macro camera.
- `seam-study-r05-front.png` — full-watch front view.
- `seam-study-r05-seam-detail.png` — tighter seam inspection.
- `seam-study-build-r05.py` — build from untouched `rim-leather-r05.blend`.
- `seam-study-r05-audit.json`, `seam-study-r05-validation.json` — numerical checks.

## Changes
- Poly Haven CC0 Leather White 4K diffuse, OpenGL normal and roughness maps. Source bytes unchanged; charcoal recoloring entirely in Blender shader nodes.
- Each of 253 upper / 365 lower original UV islands individually rescaled by world/UV area to a 100 mm texture tile. Initial 300 mm tile looked too coarse/soft and was rejected.
- 264 discrete small puncture seats (0.08 mm lateral radius), 132 separated diagonal three-ply waxed-thread stitches (approximately 1 mm spans, 0.098 mm envelope diameter). Ends descend below the leather surface. Smooth finished leather remains between stitches.
- Removed the continuous channel cutter entirely: the R04 channel was visually torn/trenchlike, not premium sewing.
- Existing padded-band silhouette, rolled lug wraps and fit retained. Satin edge-paint material and 0.012 mm cut-edge bevel; no original movement geometry edited.
- Welded duplicate/split vertices ONLY on the new replacement copies, then rebuilt consistent normals before cutting. Both new bands are closed manifold meshes.
- Boolean cut-face UVs explicitly reprojected at physical scale. Normal-map strength 0.25; subtle charcoal albedo interval 0.011–0.016 linear; roughness interval 0.45–0.56.

## Checks
- 169 original source mesh vertex/transform hashes unchanged.
- 2,444 upper and 2,683 lower lug-region vertices (z > -5 mm) lie exactly on the original strap surface: maximum distance 0.0 mm before evaluated cut-edge bevel.
- Zero nonmanifold edges in either new band.
- Zero collapsed nondegenerate UV triangles, including new cut faces.
- Zero new-thread surface intersections with source movement, case, springbars, buckle and crown meshes. Sampled minimum separation 1.19192 mm; sampled static check, not certified minimum clearance.

## Honest limitations
- Thread is idealized and uniform rather than irregular hand sewing. This is visual sewing anatomy, not a manufacturing-ready process or dynamic/strength certification.
- Original rolled lug-wrap silhouette remains relatively full; this pass preserves fit rather than redesigning that construction.
- Fine grain is a normal texture, not pore-scale mesh displacement. The material remains deliberately subtle; no guarantee of matching a particular physical leather tannage.
- R01 is a rejected Boolean failure (empty bands); R02/R03 are rejected large-grain/cordlike-seam studies; R04 rejected for torn-looking channel. Use R05, not earlier scenes.

## Satin comparison
`seam-study-r06-macro.png` / `.blend` test roughness 0.36–0.48, normal strength 0.32, specular level 0.30 and sheen 0.13. All 397 mesh geometry/transform hashes match R05 (`seam-study-r06-audit.json`). Visual review favors R05: stronger R06 grazing sheen accentuates relief on the rolled end and risks a coated/rubbery read. R06 is a comparison, not the recommended candidate.

R05 macro, front and tight seam images have all finished rendering and been inspected. The channel tearing showstopper is resolved; final integrated appearance still requires review.

## Final runtime candidate — R10

Use **`seam-study-leather-r10-runtime.glb`**, not the ~42 MB high-detail export.

- 9,487,248 bytes; 4 authored object nodes, 8 material primitives; 184,256 triangles / 122,724 exported vertices.
- Exact high-detail two-segment band/bevel geometry preserved. Thread tubes reduced from 41 rings × 8 sides to 21 × 5, retaining all 132 three-ply stitches and all 264 punctures. No band decimation.
- 2K color and roughness (JPEG95); 2K strength-baked normal (lossless PNG). Maximum PNG compression saved ~0.9 MB with **zero decoded-pixel difference**. Original 4K scans/native master unchanged.
- No normal or UV quantization; no Draco or external decoder dependency. Float32 normals and UVs retained. Runtime derives tangent basis from UV derivatives.
- `QUALITY-STRAP` / `QUALITY-STITCH`, `leatherPbrRevision: R10`, appropriate `replacesAssemblyId`, no `sourceIndex`. Four material roles: leather, lining, edge paint, thread.
- Zero collapsed UV triangles on nondegenerate faces in final exported GLB. Normals are finite/unit length within float32 tolerance.

### Important exporter correction
Blender exported every enabled sheen as white `[1,1,1]`, dropping the authored weights. The actual GLB roundtrip exposed excessive brightness and puncture highlights. `seam-study-fix-sheen-export.py` corrects `KHR_materials_sheen.sheenColorFactor` to leather 0.10, lining 0.04, thread 0.25. Geometry and image binary payload are unchanged by this fix. Do not re-export and omit this correction.

### Human-visible comparison
Open `seam-study-r10-comparison.html`, or compare:
1. `seam-study-r05-seam-detail.png` — native unbaked reference.
2. `seam-study-r10-compatible-reference-detail.png` — high-detail export-compatible materials.
3. **`seam-study-r10-runtime-roundtrip-final-detail.png`** — final actual optimized GLB imported back into Blender.

All use the same 800 × 800 seam camera and 96 samples. Final visual review passes candidate equivalence: the earlier brightness/torn-puncture artifacts are gone, silhouette and discrete seated stitches match. The 2K normal grain is slightly softer at this extreme crop; no visible blocking. This is not final acceptance of the overall leather finish.

Rejected runtime evidence is retained for audit: `runtime-roundtrip-detail.png` had the sheen export bug; `runtime-roundtrip-fixed-detail.png` still had an overly simplified one-segment bevel. Neither is the final candidate.

### Native append
`seam-study-append-manifest.json` contains exact native R05 object names, including the two band names' trailing spaces. Append only those four objects to the latest watch scene; exclude hidden original replacements, recess cutters, and all source/movement meshes.

All work remains local. No commits, uploads, publication, or edits to `assembly-photo-leather.js`.

### Remaining numerical caveat
Roundtrip corner-normal sampling matched every sampled position. The 99th-percentile angular difference is ≤0.028°. Eleven sampled band corners exceed 1° (maximum 87.14°); the detailed normal audit retains these outliers rather than claiming bit-identical shading normals. They did not produce a visible defect in the inspected final macro. No additional cosmetic changes were made to hide them.
