# Asymmetric rim v4 — local geometry candidate

Native source: `rim-leather-r04.blend`. Candidate: `rim04-asymmetric.blend`.

## Established
- Right aperture retains original uneven four-cubic XY flow. Exact SVG commands preserved except tangent 0.20 mm top/bottom endpoint fillets. No straightening or symmetrization.
- Broad left wall: 0.80 mm radial width, 0.50 mm drop, 32.005° slope. Main right wall: 0.225 mm true normal offset, same 0.50 mm drop, 65.772° slope. No changing slope/twist along the right main curve. At the endpoints, only the 0.20 mm corner fillet blends these different surfaces. The left cone itself retains constant inclination all the way to the corner seam, with no ramp or flattening.
- Outer left radius 15.7 mm centered at origin; dial radius 16.4 mm. Native dial cut and rim use identical tessellated upper contour. SVG retains exact circular/cubic upper path; native tessellation uses 160 samples/cubic and 400 main left-arc samples.
- Solid continuous rim: 0 nonmanifold edges, 0 nonadjacent triangle self-overlap pairs. Native dial also manifold. See section audit for connected components.
- All 169 source meshes retained byte-identical vertex coordinates and transforms. Seconds pivot and original hand axes retained. Source gears never moved.
- Full-depth wall has 0 triangle-surface intersections with visible original movement meshes. All three hands pass 72 sampled poses each, 5° intervals, versus authored face parts.
- Seconds ring/support retains SVG03 geometry; separate attachment lane owns any redesign.

## Endpoint correction after latest clarification
The original two-loop loft was replaced with 33 depth slices. Every left surface slice is exactly R(z)=15.7−1.6×(3.47−z), including endpoint regions; every right slice uses the original curve normal offset of 0.225×depth_fraction. The circle/right-offset intersection is rounded only by the local 0.20 mm tangent fillet. Measured left conical vertex radial residual is <0.000000705 mm and all left facet inclinations are 32.00408–32.00642° (tessellation/float error). No extended left endpoint slope transition remains.

## Visual review
Actual `rim04-front.png`, `rim04-top-join.png`, and `rim04-bottom-join.png` inspected. Upper and lower endpoint turns remain small, smooth and connected. No flat end caps, broad spoon-bowl fillet, tip pinching or outline/cutout mismatch observed. Macro cameras are angled and top view is rotated relative to front. Existing materials reused; root owns material/light refinement.

## Honest limits
32-sample QA renders contain noise. Source hardware, dial material and seconds support are unchanged except the tiny dial-tip contour corrections required to match the rim. Static triangle-surface collision and 5° hand sweeps are not continuous swept-volume, containment, manufacturing tolerance or strength certification. Original cubic joins remain authoritative, including their tiny source tangent differences.

## Reproduction
`python design-preview/rim04-build-profile.py`
`blender -b --python design-preview/rim04-build-scene.py -- --skip-render`
`blender -b --python design-preview/rim04-render-qa.py`
`blender -b --python design-preview/rim04-verify.py`
`blender -b --python design-preview/check-svg-hand-sweep.py -- --scene rim04-asymmetric.blend --output rim04-hand-sweep.json`

Only new rim04-prefixed files plus `Aerial-Left-Crescent-Asymmetric-Rim-v4.svg` were authored in this lane. No runtime/source build scripts changed; no publish or commit.
