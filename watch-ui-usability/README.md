# Inspection usability source candidate

Three fixes against the immutable `e79b2236` viewer baseline:

- Full Reset clears Follow the power highlights and its optional controls before materials refresh.
- Explicit isolated-part framing uses current visible bounds and preserves view direction, instead of inheriting a whole-watch near plane or stale target depth.
- Original-part support text uses a Unicode escape rather than a garbled literal.

The existing release, root entry, models, materials, delivery guards and workflows are not changed. This folder is a **source-only candidate**, not a published viewer release. Do not overwrite an immutable release or a newer modified viewer with this complete module.

From the repository root, with Node available:

```sh
node --test watch-ui-usability/test.mjs
node --check watch-ui-usability/assembly-review.js
```

The tests require only Node built-ins and the repository's existing Three.js math classes. They use source-extracted callbacks, synchronous DOM/function doubles and fabricated thin/thick/offset bounds. They do not launch a browser, renderer, parser, server, installer or model. Source hashes enforce the exact three-change scope; they are not runtime authentication.

Checks cover Reset ordering, optional controls and repetition; fallback/attachment text and selection effects; stale near/target-depth histories, real repeated resulting camera poses, portrait/landscape and thick/tiny bounds; existing depth safety and unchanged whole-watch behavior.

Rendered behavior, asynchronous OrbitControls dynamics, camera restoration settling, performance and device coverage remain unverified. Very small parts still obey the existing inspection distance and surface-clearance limits. A future activated release needs its own exact closure/revision identities and browser checks.
