# Aerial Watch — B face, revision 02

## What this is
An editable Blender 4.3.2 design study matching the user's approved broad Left Crescent + Small Seconds image. Not an AI image. Source OM10 movement and hand geometry are preserved. The scene contains the actual gears; no image plane substitutes for the mechanism.

Open `approved-b-face-r02.blend` in Blender. Numpad 0 selects the prepared camera; F12 renders the scene. Materials are procedural and embedded, with no external texture dependency. The compressed .blend is the self-contained deliverable.

## Implemented
- A broad full-height curved opening following the approved silhouette.
- Thin champagne metal perimeter around the opening.
- Fine procedural charcoal dial grain.
- Applied hour markers and AERIAL / KAZEYAMI STUDIO lettering.
- Open small-seconds chapter ring at the source seconds axis with 60 ticks and warm metal edges.
- Neutral bearing appearance retained; the user rejected the sapphire-blue accent preview.
- Original case, strap, crown, hand and movement positions retained.

## Verified
169 source movement/hand objects have identical local-vertex SHA256 values and world transforms compared with the original cutaway scene. The static ring/tick maximum Z is 3.62 mm; source seconds hand minimum Z is 3.900000095 mm, a separation of 0.280000095 mm. This proves that limited vertical relationship, not full-assembly mechanical clearance.

## Important limits
Three original front plates (source indices 0, 149, 155), original dial/chapter and crystals are hidden for presentation. This is a cutaway design study, not an engineered replacement bridge or manufacturing release. Ring mounting and full component interference still require validation. AI reference geometry is not substituted for actual gearing. Small visual differences remain because the actual geometry is fixed. Web-viewer integration, animation acceptance and device performance are not complete. This revision is not deployed.

To reproduce in the repository: run Blender with `design-preview/build-fixed-reference.py`, then `design-preview/render-approved-b-face.py`, then `design-preview/export-premium-face.py`. The build script creates the cutaway input directly from the tracked source GLB. That construction dependency is not needed to open or render the delivered final .blend. The preservation JSON documents the checked revision.

## Attribution
Movement source: Openmovement OM10, https://openmovement.org/ . Adapted geometry and related geometry adaptations are distributed under CC BY-SA 3.0 Unported, https://creativecommons.org/licenses/by-sa/3.0/ . No Openmovement endorsement is implied. This revision changes presentation materials and authors a new dial, aperture trim, markers and small-seconds chapter styling; it preserves original gear/hand mesh vertices and transforms. See the included project ATTRIBUTION.md for the existing adaptation history.
