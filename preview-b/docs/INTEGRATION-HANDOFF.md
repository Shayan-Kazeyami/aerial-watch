# Kazeyami integration handoff

## Recommended initial integration
Host the complete static repository at a subdirectory or dedicated subdomain and embed `integrated-preview.html` using an iframe. This isolates the existing viewer CSS, imports, canvas and lifecycle from the Kazeyami site's framework. Do not copy global viewer styles into the parent site.

Example (replace the path with the actual hosted location):

```html
<iframe
  src="/showcases/aerial/integrated-preview.html"
  title="Aerial — interactive mechanical watch by Kazeyami"
  loading="lazy"
  allow="fullscreen"
  style="display:block;width:100%;height:920px;border:0"
></iframe>
```

Serve over HTTP(S). Do not open the HTML as a file. All imported modules and model paths are relative to the viewer folder. No build step is required. Preserve vendor files, source attribution and asset paths. Do not impose a restrictive iframe sandbox without checking image/video/view-settings downloads and file import.

For a full-page case study, link to the same entry directly. Below 1050 CSS pixels the control section stacks for legibility; do not promise zero scrolling on phones. The parent can set a larger iframe height for smaller viewports. Avoid nesting parent and viewer scroll areas unnecessarily.

## Before launch
- Verify the actual GPU/WebGL render and reversible Original/Left Crescent switching.
- Verify face/interior/gears/crown/caseback views, component search, isolation and Show all.
- Verify imported view settings synchronize visible choice buttons.
- Verify PNG/WebM/settings downloads and unsupported MediaRecorder recovery.
- Test reload, context loss, background/resume and iframe removal.
- Test keyboard and touch, including small-screen sizing and focus visibility.
- Measure on representative phones, not only a desktop or software renderer.
- Retain Openmovement OM10 CC BY-SA attribution and visual-study disclaimer.

Current candidate is not launch-accepted: this cloud browser cannot create a WebGL context. Unit and layout checks pass but do not close this requirement.
