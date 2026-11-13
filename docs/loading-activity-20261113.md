# Continuous loading activity

A compositor-only CSS sweep keeps the progress bar visibly active through long preparation phases. It does not invent percentages or change estimated progress. Reduced-motion disables the sweep. Readiness stops it and fills to completion; errors hide it; iframe reload starts fresh. No watch renderer, geometry, controls or immutable release changes.

Acceptance run 43416322870 passed: real Chromium root loader fixture, stalled phase, milestone update, readiness, iframe reload, error and reduced-motion cases. Screenshot visually inspected. The fixture isolates loader behavior; it is not a hardware performance measurement.
