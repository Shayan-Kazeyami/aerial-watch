# Attribution and changes

Original movement design: Association openmovement, La Chaux-de-Fonds, Switzerland. https://openmovement.org/

The supplied `OM10_Technical_Information_20210314.pdf` identifies the OM10 movement as Creative Commons Attribution-ShareAlike 3.0 Unported. https://creativecommons.org/licenses/by-sa/3.0/

The adapted OM10 geometry in `assets/`, its geometry metadata and the accompanying geometry/animation adaptations are made available under CC BY-SA 3.0. Changes: STEP tessellation to triangle meshes, per-mesh local origins with preserved source placement, source metadata extraction, metallic browser shading and illustrative animation transforms. No endorsement is implied.

The supplied STEP assemblies remain the authoritative exact geometry. Copies of the provided technical sheet and release notes are included unchanged in `docs/` with their original notices. Sources: manual A/B (2022-07-01 filenames), automatic beta (2023-05-22 filename), and technical sheet (2021-03-14).

Three.js 0.180.0: MIT, copyright its authors; full notice in `vendor/THREE-LICENSE.txt`. The optional KTX2 delivery dependencies have separate Basis Universal (Apache 2.0), KTX-Parse (MIT), and zstddec/Zstandard (MIT and BSD-3-Clause) notices; see `vendor/ktx2-NOTICES.md` and the complete licenses in `vendor/ktx2-licenses/`.

Conversion uses occt-import-js 0.0.23 and its Open CASCADE WebAssembly build. These are build-time dependencies and are not needed by the prepared browser application; their notices accompany the installed packages.

Revision 02 changes: original exterior mesh revisions, closed strap/lug shells, procedural pebbled leather and brushed-steel surface maps, source-instance presentation material overrides, studio environment and screen-space contact occlusion. Source CAD and source GLB geometry remain unchanged. Prepared complete exports include the material overrides; original material data remain available in the separate movement source GLBs.

Revision 03 changes: a separately authored native Blender exterior around the intact Manual A movement, rigid source-coordinate reorientation, local mesh origins, source metadata and clay presentation. The native package is `../Aerial-Rebuild-v3/`; its prepared browser copy is `rebuild/assembly.glb`. Source-derived geometry and its adaptation retain the CC BY-SA 3.0 attribution and share-alike notice above. The original 166 movement meshes remain present.

23 October 2026 inspection improvements add reversible browser exterior-material previews, an illustrative exterior-hand study, component inspection controls and portable verification/build tooling. The native clay checkpoint and original CAD geometry are preserved. Material previews and hand motion do not certify materials, physical attachment, movement operation or mechanical clearances.

The follow-up interior animation applies reversible rigid wheel/balance transforms to 12 original Manual A mesh instances using retained source hierarchy and shaft centres. Coordinate conventions are adapted for the native watch orientation, preserving wheel ratios and aligning the seconds wheel and hand directions. Geometry, metadata, original downloads and native exports remain unchanged; reset restores source poses exactly.

The subsequent studio revision animates 34 source components, indexes twelve gear contacts into complementary tooth phases, fits axes to native jewel bearings/circular hubs, adds phased escape-wheel/pallet motion and deforms a private hairspring geometry with its outer terminal fixed. One stationary crown wheel also receives a phase correction. Browser rest poses keep this corrected alignment; the motion helper can restore exact imported transforms and geometry. Proposed PBR finishes, procedural machining/leather grain, a local reflection environment, perspective cameras and a studio tour are browser adaptations. They do not modify original downloads or the native checkpoint, and are not a verified materials BOM or a contact/elastic dynamics solution.

31 October 2026 Left Crescent B presentation: a separately authored 76-mesh dial/marker/ring overlay is loaded from `premium-face/face-b.glb`. Three original front plate meshes (source IDs 0, 149 and 155) are hidden in this cutaway view. The underlying source geometry and placement are retained; the original appearance remains available in the viewer. The scene applies reversible neutral bearing and steel wheel-plate finishes for the selected visual direction. These are presentation adaptations, not structurally validated replacement plates or a manufacturing design. The source-derived movement and its adaptations retain the attribution and share-alike notice above. See `design-preview/APPROVED-B-README.md` for the authored overlay and static preservation checks.

## Photographed leather candidate (R09)

The optional `leather=photo` candidate uses adapted, charcoal-tinted and baked maps from **Brown Leather**, by **Rob Tuytel**, [Poly Haven](https://polyhaven.com/a/brown_leather), CC0. Source metadata and checksums are in `design-preview/material-reference/brown-leather-source.json`. No external texture requests occur at runtime. The fitted strap geometry is separately authored; this material does not change the OM10 geometry attribution.

## Fine leather and sewn strap candidate R10

The optional `leather=craft` candidate uses **Leather White**, a separate CC0 texture asset from [Poly Haven](https://polyhaven.com/a/leather_white), recolored to charcoal through the material pipeline. The source maps are retained at 4K for the native study; the runtime embeds reviewed 2K material maps. Source URLs and checksums are in `design-preview/material-reference/fine-leather-source.json`. It does not reuse the Brown Leather asset as its current surface. The padded bands, punctures, seam treatment and three-ply thread geometry are authored presentation work. No claim about a measured leather species, physical manufacturing tolerances or durability is made.

## Higher-resolution outer leather candidate R12

`leather=craft12` (also `craft12ktx`) uses the same CC0 **Leather White** source from Poly Haven, with a genuine 4096×4096 outer normal map and 2048×2048 color/roughness maps. The R11 lining and R10 sewn geometry are retained. The KTX2/UASTC texture encoding is lossy; chunk reassembly is byte-exact. GPU texture storage depends on device support and is not a measured VRAM claim. Geometry, UVs and the original movement are unchanged by this material-delivery revision. Basis Universal and related decoder notices are included under `vendor/ktx2-licenses/`.

## Rendering compatibility patch

The vendored Three.js r180 renderer has one documented local change allowing this viewer to initialize its transmission target without multisampling. The original four-sample behavior remains the default unless explicitly overridden by this viewer. See `vendor/THREE-TRANSMISSION-MSAA-PATCH.md` for the exact change, hashes and limitations. Official r180 SMAA pass/shaders retain their upstream license; the viewer uses SMAA at unchanged selected resolution. This is a rendering-method choice, not a claim of identical edge quality or measured phone performance.
