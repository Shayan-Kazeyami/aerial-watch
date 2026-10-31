# Aerial visual rebuild checkpoint

Recorded 31 October 2026 at 22:23 UTC. This is local work in progress, not a completed or fully tested public release.

## Geometry

- The original uneven 2D right-edge flow is retained. Both rim wall sections are constant through the tips; only a local 0.20 mm meeting fillet changes direction. Left wall is 0.8 mm wide with 0.5 mm drop; right is 0.225 mm wide with the same drop.
- Native rim master and reduced runtime geometry have separate audits. The runtime candidate preserves the underlying design, endpoint angles and source placement; it is not a manufacturing certification.
- The seconds ring has a deeper tapered body and substantial twin bridges. It is intentionally suspended clear of the gears, not supported on moving wheels. Ring face and original hand height/pivot remain unchanged.
- Original 169 movement/hand meshes were verified unchanged by the native geometry scripts. Hand checks sample 72 angles per hand, not continuous mechanics.
- Integrated native checkpoint: `design-preview/visual-master-r01.blend`. Exported face: `premium-face/face-svg04.glb`.

## Leather

- New fitted bands have 264 discrete punctures and 132 short three-ply stitches. Earlier continuous-cut seam variants were rejected as torn-looking.
- Runtime GLB is `quality-study/leather-craft-r10.glb`, 9,487,248 bytes and 184,256 triangles. High-detail bands/bevels are retained; thread tessellation is reduced. All maps are embedded.
- A glTF exporter sheen-weight mismatch was found and corrected. A native-compatible versus actual GLB roundtrip detail comparison passed visual review; the 2K normal is slightly softer at extreme crop. See the seam-study audits.
- Browser material/lighting integration still requires review. Counts and clean topology are not visual acceptance.

## Interface and interactions

- New local entry: `atelier-preview.html?face=svg04&leather=craft`.
- The static layout study is separate and explicitly labeled. The live entry uses the real canvas, with a compact task dock and contextual tools; legacy controls remain only as an internal compatibility bridge.
- Logical-group explosion is implemented and wired. A local software-WebGL test visibly separated layers at 69 percent. Module tests cover retargeting, fixed matrices, repeated reassembly, parent restoration and source preservation. Full interaction regression remains open.
- Crown presentation interpolation and direct drag/double-click hooks are implemented locally. Real browser gesture, pull/turn/reseat and cross-feature verification remain incomplete. Mechanical command state is still authoritative; no full physical simulation is claimed.
- Exploded amount is validated and preserved in view configuration. Existing capture/import/tour/inspection functions are retained through the new controls.

## Rendering

- Optional atelier materials add subtle crystal attenuation while retaining measured 0.35/0.30 mm thickness and IOR 1.76. Lighting/reflection cards and the background are under active review.
- The ordinary cloud browser exposes WebGPU but returns no adapter. No hardware speedup comparison can be made here.
- The isolated software-WebGL browser can render the project, but high-definition camera work has triggered GPU-process exits/context loss. Rendering-quality and hardware compatibility claims remain limited. No security settings were expanded to address this.
- Three.js r187 was downloaded from the official npm package with integrity verification into a separate vendor directory and experiment entry. The stable r180 renderer is retained. Matching transmission shader insertion points were checked; loaded-scene parity is not established yet.
- Postprocessing quality, grounding shadows, all-view lighting, exports, mobile hardware performance and final release acceptance are not complete.

## Verification and recovery

- Latest completed local aggregate checkpoint before subsequent integration edits: 83 Node tests, 93 JavaScript syntax checks and 187 manifest identities. Regenerate source identities and rerun against each final candidate.
- Actual-watch PNG/WebM delivery and JSON roundtrip must be verified; a small export fixture is not sufficient evidence.
- Native rebuild checkpoint is backed up in the authorized Codex Drive project folder. Public homepage and previous preview remain unchanged until a new tested review checkpoint is published.
