# Material-state mechanism batching

Baseline: main4193c7b, immutable b38ddef3. Read-only remote probe CI43408503827 confirmed:
- Finishes on:132 Smooth /275 Studio calls (438/887 unbatched).
- Finishes off:222 Smooth /668 Studio calls, no batching benefit.
- All166 source materials become one MeshStandardMaterial in finishes-off mode.

Candidate reuses the same geometry buffers and selects the largest opaque material cohort in each existing geometry batch. Exceptions stay on their original source meshes, with exact materials and transforms. Transparent/transmissive materials never join. No geometry, quality preset, visibility, animation or interaction changes. No phone FPS claim.

Unit tests cover finish swaps, minority material exceptions, transparent/transmissive bypass, material mutation, source restoration and disposal. Browser QA compares actual composed-frame counts and screenshots against the original per-mesh render path in Smooth/Studio, assembled/exploded, finishes on/off. Candidate must pass before publishing; public baseline remains unchanged until then.
