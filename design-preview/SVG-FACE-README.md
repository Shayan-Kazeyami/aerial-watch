# Left Crescent: SVG-driven geometry

The approved generated image is an art-direction reference, not authoritative CAD. This revision regularizes the face in millimetres while retaining the source movement.

## Files
- `Aerial-Left-Crescent-B-dimensioned.svg`: editable, dimensioned face overlay; SVG X right/Y down.
- `Aerial-Left-Crescent-B-dimensioned.png`: raster preview only; pale areas are openings.
- `build-svg-face.py`: reproducible construction and 2D checks.
- `build-face-from-svg.py`: reads the SVG to create the Blender face candidate.
- `svg-face-r01.blend`: candidate scene, original movement retained, font packed.
- `svg-face-r01-preview.png`: actual Cycles render, not generated concept art.
- `svg-face-audit.json`, `svg-face-3d-audit.json`, `svg-hand-sweep.json`: scoped checks.
- `check-svg-hand-sweep.py`: 5-degree sampled original-hand/face overlap check.
- `svg-lettering-bounds.json`: Inkscape text bounds converted from CSS pixels to millimetres; used to match the SVG lettering bounds in 3D.

## Construction
Dial radius 16.4 mm. Seven visible hour batons use exact 30-degree spacing; each is 2.2 × 0.4 mm. The remaining hour locations lie in the intentional aperture and are not filled with invented floating markers.

Small-seconds pivot is the actual source coordinate (-7.998827934, -0.016291369) mm in Blender. Its hand is unchanged. Chapter radii are 3.1/4.1 mm with 60 ticks at exact 6-degree intervals. Two shallow tabs actually connect the chapter ring to the dial. Blender unions these into one manifold connected solid rather than leaving a floating ring.

The crescent is a cleaned cubic outline, not a blind trace. The sampled minimum outer web is approximately 0.684 mm. This is a geometric measurement, not a structural strength approval.

## Evidence boundary
169 source movement/hand meshes retain vertex values and world transforms. The three original hidden front plates remain a presentation cutaway. The unified new dial has one connected component and zero non-manifold edges in the recorded check. The small-seconds hand has a 0.280 mm static vertical gap above the tick tops.

The sampled sweep checks triangle-surface overlap at 5-degree increments. It is not continuous collision detection, tolerance analysis, bearing validation, spring/contact dynamics or manufacturing certification. Read the current JSON results rather than treating this document as a blanket pass.

The original OM10 attribution and share-alike notice in `../ATTRIBUTION.md` remain applicable. Packed DejaVu font copyright and terms are included in `DEJAVU-FONT-NOTICE.txt`.

## Status
A local visual candidate. Do not claim it is the published viewer asset until the authored GLB has been exported, inspected and deliberately promoted. UI and export polishing are paused while reference matching is prioritized.
