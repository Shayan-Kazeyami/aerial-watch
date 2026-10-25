# Attribution and changes

Original movement design: Association openmovement, La Chaux-de-Fonds, Switzerland. https://openmovement.org/

The supplied `OM10_Technical_Information_20210314.pdf` identifies the OM10 movement as Creative Commons Attribution-ShareAlike 3.0 Unported. https://creativecommons.org/licenses/by-sa/3.0/

The adapted OM10 geometry in `dist/assets/`, its geometry metadata and the accompanying geometry/animation adaptations are made available under CC BY-SA 3.0. Changes: STEP tessellation to triangle meshes, per-mesh local origins with preserved source placement, source metadata extraction, metallic browser shading and illustrative animation transforms. No endorsement is implied.

The supplied STEP assemblies remain the authoritative exact geometry. Copies of the provided technical sheet and release notes are included unchanged in `dist/docs/` with their original notices. Sources: manual A/B (2022-07-01 filenames), automatic beta (2023-05-22 filename), and technical sheet (2021-03-14).

Three.js 0.180.0: MIT, copyright its authors; full notice in `dist/vendor/THREE-LICENSE.txt`.

Conversion uses occt-import-js 0.0.23 and its Open CASCADE WebAssembly build. These are build-time dependencies and are not needed by the prepared browser application; their notices accompany the installed packages.

Revision 02 changes: original exterior mesh revisions, closed strap/lug shells, procedural pebbled leather and brushed-steel surface maps, source-instance presentation material overrides, studio environment and screen-space contact occlusion. Source CAD and source GLB geometry remain unchanged. Prepared complete exports include the material overrides; original material data remain available in the separate movement source GLBs.

Revision 03 changes: a separately authored native Blender exterior around the intact Manual A movement, rigid source-coordinate reorientation, local mesh origins, source metadata and clay presentation. The native package is `../Aerial-Rebuild-v3/`; its prepared browser copy is `dist/rebuild/assembly.glb`. Source-derived geometry and its adaptation retain the CC BY-SA 3.0 attribution and share-alike notice above. The original 166 movement meshes remain present.

23 October 2026 inspection improvements add reversible browser exterior-material previews, an illustrative exterior-hand study, component inspection controls and portable verification/build tooling. The native clay checkpoint and original CAD geometry are preserved. Material previews and hand motion do not certify materials, physical attachment, movement operation or mechanical clearances.

The follow-up interior animation applies reversible rigid wheel/balance transforms to 12 original Manual A mesh instances using retained source hierarchy and shaft centres. Coordinate conventions are adapted for the native watch orientation, preserving wheel ratios and aligning the seconds wheel and hand directions. Geometry, metadata, original downloads and native exports remain unchanged; reset restores source poses exactly.

The subsequent studio revision animates 34 source components, indexes twelve gear contacts into complementary tooth phases, fits axes to native jewel bearings/circular hubs, adds phased escape-wheel/pallet motion and deforms a private hairspring geometry with its outer terminal fixed. One stationary crown wheel also receives a phase correction. Browser rest poses keep this corrected alignment; the motion helper can restore exact imported transforms and geometry. Proposed PBR finishes, procedural machining/leather grain, a local reflection environment, perspective cameras and a studio tour are browser adaptations. They do not modify original downloads or the native checkpoint, and are not a verified materials BOM or a contact/elastic dynamics solution.
