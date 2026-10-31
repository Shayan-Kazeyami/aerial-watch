# Leather material research

Current candidate uses **Brown Leather** by **Rob Tuytel**, from [Poly Haven](https://polyhaven.com/a/brown_leather), identified there as CC0. Source download URLs, sizes and MD5 hashes are retained in `brown-leather-source.json`; downloaded image bytes are unchanged.

The native study applies a charcoal material tint, remapped roughness and a deliberately art-directed 30 mm triplanar repeat. It uses the photographed height map for bump rather than treating incomplete inherited UVs as a finished unwrap. This is an appearance adaptation, not a measured material specification.

The first procedural cell-pattern study and the first UV-mapped normal-map study were rejected as insufficiently realistic. White/red leather previews are research alternatives, not selected production assets. No runtime calls to the Poly Haven API are planned; any chosen maps should be bundled with their source/credit record.

## UV repair checkpoint (2026-10-31)

R08 replaces the inherited strap UV layout. The upper band had 20,661 collapsed UV triangles out of 27,322; the lower had 15,623 out of 20,634. The replacement unwrap has zero collapsed triangles in either mesh, with vertex coordinates unchanged. See `../leather-uv-audit.json`. R08 uses the scan's tangent-space normal map and a narrower charcoal/roughness range. R09 tests a finer fourfold texture repeat and a less pronounced dial bump. Both remain local appearance candidates, not approved production finishes. Smart projection fixes degeneracy but does not establish seam-free mapping or uniform texel density.
