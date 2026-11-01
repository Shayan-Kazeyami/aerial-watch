# Premium display hand clearance

`createHandClearance(exterior)` from `assembly-hand-clearance.js` takes the actual baseline exterior array, containing exactly one `SECONDS` and `SECONDS-STAFF` mesh. Create once after baseline import. Register `dispose()` with the resource lifecycle. Call `setEnabled(premiumActive())` when front-detail visibility changes. Default is disabled.

The module does **not** enable the older custom quality hands. Original seconds shape/length/normals and all pivots/poses are preserved. A private seconds geometry clone is translated −0.32 mm along glTF local Y. A private staff clone compresses only the section above depth 2.94 mm to end at 3.68 mm, retaining its lower movement seat. Hour/minute and all movement geometry are untouched. Raw `assembly.glb` and other assets are never rewritten.

Mesh transforms, live clock quaternions, parent/sibling order, explosion wrappers, materials and visibility are not modified. Disabling restores original geometry; disposal frees only the two private clones and does not restore stale poses. Competing geometry ownership is rejected on enable rather than silently overwritten. Source geometry remains available for original/nonpremium inspection.

## Evidence
- `node --test tests/hand-clearance.test.mjs`: 4/4 pass, including actual assembly.glb buffer data and repeated lifecycle/explosion-parent tests.
- `blender -b -t 2 --python design-preview/hand-clearance-verify.py`: actual baseline and SVG04 GLBs, no renders or scene saves.
- `hand-clearance-audit.json`: 1,440 coupled poses over 12 hours (30 s step), all 5 tested hand/staff pairs clear; 72 poses/hand against premium face clear.
- Continuous z/radial bounds: hour/seconds ≥0.03 mm, hour/staff ≥0.18 mm, minute/seconds ≥0.19 mm. Seconds hand's full swept XY envelope never enters the main hub radius.
- Seconds blade/highest dial tick ≥0.02 mm; highest hand/crystal underside ≥0.13 mm. The minimum sampled seconds-vertex/face distance is 0.06923 mm; do not confuse that sample with the conservative 0.02 mm plane bound.
- Staff top 3.68 retains original sleeve/seconds-hub axial engagement after −0.32 translation; lowering staff to 3.59 would unnecessarily shorten that fit.

## Limits
Hour/minute nested hubs have a sampled coupled-cycle check, not a continuous swept-solid certificate. This is an interference-free visual display correction, not manufacturing tolerance, dynamics, or full movement certification. The 0.02 mm face-plane margin is positive but not a production tolerance recommendation. Actual browser appearance and control/selection/isolation/explosion QA are separate integration acceptance checks.
