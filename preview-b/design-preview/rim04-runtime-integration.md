# Runtime rim geometry integration

Candidate: `rim04-runtime.blend` (derived from untouched full `rim04-asymmetric.blend`).

Only transfer mesh data of **SVG broad sloped champagne wall** to the corresponding object in the final integrated scene. Preserve parent object, transform, material slots and custom metadata. Do not copy the full scene/dial/seconds attachment.

For existing **SVG champagne aperture rim** and **SVG lower champagne rim lip**, set `data.bevel_resolution = 2`; their original full XY polylines and bevel radii remain unchanged. Blender's evaluated mesh has 8 cross-section sides at this resolution, not 12.

Rim: 160,512 → 60,864 triangles. Each lip: 24,320 → 19,456 triangles. Total three objects: 209,152 → 99,776 triangles (52.3% reduction). Projected total face count from 265,310-triangle baseline: approximately 155,934 triangles; exporter may differ.

Adaptive depths: 9 levels for constant main wall sections, original 33 at endpoint geometry. Full 1,216 XY samples retained. Transition polygons explicitly include dense boundary vertices (no T-junctions); no decimation.

Verified: zero nonmanifold edges, zero nonadjacent triangle overlaps, zero static visible-source collisions, 169 source meshes unchanged. All three hands pass 72 samples each. Left angle 32.00408–32.00609°, right 65.76305–65.78041° (same endpoint range as full master). Master sampled front-to-runtime surface max difference 0.000001093 mm. Native master and separate seconds scene untouched.

Wire circle sagitta upper bound: 0.003425 mm upper lip, 0.001370 mm lower lip; actual change relative to previous faceted wire is smaller. At full-face scale this is comfortably subpixel, though high magnification can expose any polygonal section. The integrated web asset still requires a matched macro appearance check. Source master remains available for unlimited-closeup fidelity.

Files: `rim04-runtime-build.py`, `rim04-runtime-audit.json`, `rim04-runtime-hand-sweep.json`.
