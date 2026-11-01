# Seconds attachment: local native candidate

## Diagnosis
The previous annulus is only 0.14 mm deep (Z 3.43–3.57). Two bridges exist, each 0.32 mm wide and 0.12 mm deep. In the reference's grazing view, those thin connections largely disappear. The ring therefore reads as a floating wafer rather than an intentionally supported subdial.

216 downward rays were sampled under the original annular footprint (72 azimuths, three radii). 160 hit visible original movement surfaces; those returned 1.38–5.33 mm clearance from the ring underside, median 3.96 mm. The remaining rays pass through open areas within the 20 mm trace distance. These are sampled vertical separations, not an exact global clearance or a fabrication tolerance.

## Candidate
`seconds-attachment-r02.blend` derives from `rim04-asymmetric.blend`, which is not changed.

- Original face remains at Z 3.57, inner/outer radii 3.1/4.1, original seconds pivot and hand fully preserved.
- Annular underside tapers down to Z 2.83: bottom inner radius 3.40, outer radius 3.86. The central opening remains unobstructed; no floor or central plate is added.
- Two existing connection lanes are reinforced with smoothly waisted bridges, width 0.52–0.86, depth 0.605 mm. Their roots merge into the annulus and dial. No posts contact moving gears.
- The ring is intentionally suspended from the dial. It is not claimed to rest on gears. Some air gap must remain; filling it arbitrarily would conceal movement and invent attachment points.

Revision 2 replaces the obsolete thin support mesh instead of retaining it inside the union, eliminating its faint top-face ridge. The original dial aperture outline is reused exactly; no rim changes are made.

## Verified
- All 169 original source meshes, topology and transforms identical to input scene.
- Corrected asymmetric rim mesh/topology/transforms identical.
- Unified dial/ring/bridge mesh: one connected component, zero nonmanifold edges.
- Static triangle-surface overlap versus visible original source meshes: zero.
- Original hour, minute and seconds hands: 72 samples each, 5-degree spacing, zero sampled surface intersections with authored face parts.

## Limits
Not manufacturability, strength, continuous motion or moving-gear certification. Surface-overlap testing does not establish all containment or tolerance conditions. This is a visual native-geometry candidate, not a production CAD design or published site change.

## Evidence
- `seconds-attachment-front.png`: face, preserved open center, two reinforced bridges.
- `seconds-attachment-oblique.png`: attached depth reading.
- `seconds-attachment-side.png`: grazing-angle attachment check of revision 1 (same depth/bridge proportions; final revision 2 removes inherited top ridges). Final front and oblique images are revision 2; a final revision 2 side render is not included.
- `seconds-attachment-baseline-oblique.png`: exact same view of previous geometry.
- `seconds-attachment-measure.json`, `seconds-attachment-audit.json`, `seconds-attachment-hand-sweep.json`: numerical checks.
