# Aerial Watch — visual design study

This is an independent, interactive visual study of an original complete-watch concept built around the Openmovement OM10 mechanical movement. It preserves the supplied movement geometry as a design reference and adds a separately authored exterior, presentation materials, camera views, and illustrative browser animation. It is not a manufacturing release or an endorsed Openmovement product.

The adapted OM10 geometry and related geometry/animation adaptations are attributed to Openmovement and distributed under **Creative Commons Attribution-ShareAlike 3.0 Unported (CC BY-SA 3.0)**, as identified by the supplied OM10 technical information. The original source is [Openmovement](https://openmovement.org/); the license is [CC BY-SA 3.0](https://creativecommons.org/licenses/by-sa/3.0/). Changes include STEP tessellation, local mesh origins with preserved source placement, source metadata, browser presentation materials, and illustrative animation transforms. No endorsement is implied.

Third-party notices are retained with the prepared application. Three.js 0.180.0 is MIT licensed; see [THREE-LICENSE.txt](vendor/THREE-LICENSE.txt). The included original technical sheets and release notes retain their supplied notices in [docs/](docs/). The complete project attribution and adaptation history are in the [showcase attribution](ATTRIBUTION.md).

Open the [interactive watch](./), or visit the [material review](material-review.html), [interior and assembly review](assembly-review.html), or [historical movement study](movement.html). The browser application uses local static assets and requires a modern browser with WebGL.

## Local preview and compatibility

Serve the repository over HTTP, for example `python -m http.server 8765`, then
open `http://localhost:8765/`. The main studio uses JavaScript modules/import maps,
WebGL, Fetch and AbortController; opening the HTML directly as a local file is not
a supported preview. No build or package installation is required.

The main studio offers keyboard camera controls, a component explorer, static
images when interactive rendering fails, reduced-motion behavior and a clock that
pauses in the background. WebM recording is optional and checked at runtime;
unsupported recording does not establish that the 3D viewer is unsupported.
Actual browser/device coverage, mobile rendering performance, screen-reader
behavior and touch interactions remain unverified by the cloud syntax tests.

The main studio loads local static assets. Application source contains no added
analytics endpoint or automatic upload; view/image/video exports are browser
downloads, and imported view files are parsed locally. External attribution links
remain external. These source observations are not a runtime network audit.
Historical study pages are separate entry points and have not received the same
loading-deadline regression coverage as the main studio.

Run the dependency-free checks with `node --test tests/*.test.mjs`.
Verify JavaScript syntax and deployment file identities with `node scripts/validate.mjs`.
