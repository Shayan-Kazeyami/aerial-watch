# Hand clearance: scope and corrected native display variant

## Previous audit gap
Earlier rim/face audits preserved the source hands and checked each hand against authored face geometry at 5° intervals. They did **not** test hand-to-hand or hand-to-seconds-staff interference. Native and actual runtime hands had identical poses and depth bounds; neither was buried in the new dial. Nevertheless, the baseline hour blade and seconds assembly overlapped in depth.

Using actual `rebuild/assembly.glb`, coupled hour/seconds periods (43,200/60 seconds) produced a hand/hand intersection at elapsed 37,230 s and an hour/staff intersection at 38,370 s. These were inherited baseline-stack defects, not SVG04 dial penetration. This distinction matters when interpreting prior clean face-sweep reports.

## Minimal derived correction
The premium display layer rigidly translates a private clone of the **original seconds hand** by −0.32 mm in glTF local Y / native Z. No hand outline, length, XY pivot, axis or material is replaced. The private seconds-staff clone keeps geometry at/below 2.94 mm fixed, and compresses only the upper interval to end at 3.68 mm. This retains its original lower movement seat and original sleeve/hub engagement after the hand translation. All gears and source geometry remain authoritative and unchanged.

`visual-master-r02.blend` derives from r01. Original seconds and staff objects/data are retained hidden; clearly labelled display clones supply corrected visible geometry. Initial poses, materials and every other component are unchanged. Audit hashes include 170 original movement/hand/staff objects (the extra staff is included explicitly). Native corrected positions are compared against actual runtime GLB positions after applying the module's Float32 correction.

## Verification and margins
- 1,440 coupled poses across the complete 12-hour cycle, 30 s intervals: no tested hand/hand or hand/staff intersections.
- Each of 3 hands tested at 72 angles against the actual 75-part SVG04 face: clear.
- Continuous conservative depth/radial bounds: hour/seconds ≥0.03 mm; hour/staff ≥0.18 mm; minute/seconds ≥0.19 mm.
- Seconds blade/highest face feature ≥0.02 mm. Highest hand/front-crystal underside ≥0.13 mm.
- Raw runtime assets are untouched. Native originals retain geometry hashes, transforms and datablocks. Display clone materials are identical to source slots.

## Proof image
`hand-clearance-stack-proof.png` is a small labelled orthographic geometry inspection at the former collision-example pose, t=37,230 s. Gold denotes the unchanged hour, blue the corrected original-shaped seconds hand, grey the relieved staff. Glass, face and unrelated components are temporarily hidden only for this unsaved proof render. Proof-only contrasting materials and labels are not stored in the native master. It is not a beauty render or production material approval.

## Remaining limits
The hour/minute nested-hub check is sampled, not a continuous swept-solid certificate. These margins establish a visual noninterference correction, not manufacturability, tolerance stack-up, strength, dynamics or complete movement certification. Browser QA verifies actual premium enable/disable, visibility, selection, isolation and explosion integration; these notes do not substitute for that UI check.
