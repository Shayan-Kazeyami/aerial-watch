# Premium face design study

This is a reversible Blender study using the actual repository assembly and R07 front presentation geometry. It is not an accepted final design, a live-WebGL screenshot or a manufacturing model.

Run `blender -b --python design-preview/render-premium-study.py` from the repository root. The script imports existing GLBs, preserves source geometry, creates a separate selective-aperture dial and renders it with CPU Cycles. Blender 4.3.2 was used here. Denoising is disabled because this installed build lacks OpenImageDenoise.

The materials are deliberately simplified study materials, not a faithful reproduction of every runtime shader. Crystal objects are hidden for this front-composition inspection. No mechanism motion or dynamic collision validation is claimed. The first round is too plain and its round openings need further art direction; it is retained as an experiment rather than promoted to the product.

Generated `.blend` and render files stay out of Git. The script and repository GLBs reproduce the study. Shayan received the R02 rendered image as a native attachment on 31 October 2026.
