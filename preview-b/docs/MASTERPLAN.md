# Aerial Watch studio showcase masterplan

Updated 31 October 2026. Owner: Kazeyami. Status: active rebuild, not an accepted release.

## Purpose and decision

Rebuild Aerial into a premium interactive watch showcase that helps Kazeyami win design and development clients. The watch must look convincing before the interface or technical features ask for attention. This plan covers the model, materials, lighting, controls, animation, renderer evaluation, testing and final integration package.

The current public preview is a working reference, not the quality target. Its materials, crescent rim and interface have been rejected. Preserve the useful engineering beneath it, then replace the weak presentation rather than polishing the same design indefinitely.

Visual quality comes first. Start with representative close-ups of the actual watch, solve the geometry and material problems there, then extend the result across the entire experience. Generated concepts can guide decisions; they cannot prove implementation.

### Fixed requirements

- Preserve the broad left crescent B composition, charcoal dial, silver case, champagne trim, blue hands and dark leather. The added blue-jewel treatment remains rejected.
- Preserve the current uneven concave right-edge curve in 2D. Do not straighten or symmetrize it. Smooth only its top and bottom joints with a small curve radius.
- Keep the original OM10 gear coordinates, dimensions, axes, hand lengths and seconds pivot. Do not move the movement to fit a more convenient face.
- Retain the original geometry, attribution and CC BY-SA 3.0 notices. Separate authored presentation work from the openmovement source.
- Build a studio showcase, not a storefront or manufacturing-certified watch. Mechanical motion and exploded assembly are explanatory presentation, not a physical simulation.
- Rebuild the interface around a large viewer and understandable compact controls. No desktop scrolling, giant button wall or hidden essential dropdown choices.
- Continue routine design and implementation decisions without waiting for replies. Ask only when genuine access, scope or approval blocks progress.
- Shayan owns integration into the main Kazeyami site. Deliver a tested package; do not silently deploy to that site.

## Current checkpoint

These states describe the checkpoint before the new rebuild is validated. Local work must not inherit the earlier preview's test results.

| Area | State | What this means |
| --- | --- | --- |
| Original movement | Preservation verified at prior checkpoints | All 169 source movement and hand meshes retained geometry and world transforms. Recheck after every new export. |
| Broad B face | Direction selected | The composition is retained; the present rim, surface finish and attachment treatment are not accepted. |
| Crescent joins | Existing right profile locked and joins unresolved | Initial concepts A to D were rejected. Preserve the current uneven concave right curve and use small-radius endpoint joins. Later concepts do not authorize a straighter or symmetric outline. |
| Seconds ring | Implemented but visually unresolved | Two modeled supports exist. The apparent side-view gap and floating appearance still need redesign. |
| Materials and studio | Rebuild required | Leather, metals, dial, engravings, glass presentation, lighting and backdrop remain below the requested standard. |
| Interface | Working shell under test | The local atelier shell has runtime proxies and a fallback-browser check. Loaded GPU interaction remains unverified. The separate layout study is still a static prototype. |
| Crown motion | Logic implemented and smoothing in progress | A local presentation tween and three unit tests have been added. Browser behavior and broader animation integration remain unverified. |
| Exploded view | Local module not yet integrated | The local module has seven focused tests. It is not wired into the viewer, browser-verified or published; complete assembly behavior remains to be demonstrated. |
| WebGPU hardware trial | Environment blocked | The secure cloud browser exposes the API, but its high-performance adapter request returned null. No hardware comparison is available here. |
| Release evidence | Partial | Earlier tests and CI passed. Actual watch export delivery, full state restoration and real-device performance are still open. |

The earlier verification checkpoint recorded 69 tests, 88 JavaScript syntax checks and 180 manifest checks, plus passing CI. Those results predate the new local edits and are not visual acceptance. Cloud software rendering has displayed the watch; it is not evidence of phone or hardware-GPU performance.

## Watch geometry and visible construction

### Crescent walls and joins

The existing uneven concave right-edge curve is a design lock. Do not straighten, symmetrize or replace it with the outline from a generated concept. Smooth its top and bottom connections using a small curve radius, without broad rounding that erases the character of the edge.

The two crescent walls must both feel deep. Keep the left wall more angled; make the right wall more upright with a narrower bevel. Unevenness applies only to the 2D outline. Keep the right wall's cross-sectional angle, depth and width constant along the curve, with no slope twist or width drift outside the small-radius top and bottom endpoint blends. Blend those joins without bulges, pinching, hard seams or an abrupt change in highlight width.

- Build the section and end transitions as coherent geometry rather than disconnected trim pieces.
- Preserve the broad opening and the selected dial balance. Do not drift back to a narrow aperture.
- Compare front, both three-quarter views and low side views. Use a neutral diagnostic material before judging the polished finish.
- Check connected topology, normals, edge consistency, source preservation and sampled moving-part clearance. Report exactly what was sampled.

**Evidence required:** actual-model close-ups of both walls and both joins, a continuous highlight during orbit, and a geometry report. A manifold mesh alone does not prove a visually good join or manufacturing suitability.

### Seconds ring attachment

Preserve the original seconds pivot and hand length. Keep the ring readable and open in the center. Redesign the visible support path and depth so the ring reads as attached from front, oblique and gear-side views, rather than suspended above a gap.

- Inspect the existing two supports before replacing or thickening them. Solve the visual attachment, not merely the support count.
- Choose a restrained bridge or tab form that visibly meets the surrounding dial structure without obscuring the relevant movement.
- Check the ring, supports and ticks against the original hand sweep and visible neighboring parts.
- Retain a reversible authored layer; do not invent structural certification for the cutaway front plates.

**Evidence required:** side-view attachment close-up, clear front reading and repeatable clearance checks. The previous 0.280 mm static hand-to-tick separation is a limited measurement, not whole-assembly validation.

### Case and leather construction

Review the case, crown, lugs, strap and buckle as one object. Refine bevels and transitions so reflections reveal their construction at normal viewing distance as well as macro scale.

Replace the current leather treatment with a distinctly better fine-grain texture. Build convincing padding, burnished edges, recessed stitch holes, an inset seam channel and individual thread geometry. Stitching must sit in the leather rather than float above it; thread thickness and spacing must suit the watch scale.

Use appropriately licensed texture sources with local files, recorded attribution and repeatable mapping. Inspect both straps, their bends, lug attachments and buckle connection for stretched grain, obvious tiling and intersecting stitches. New texture studies are candidates until seen on the complete watch.

## Materials glass and studio presentation

### Distinct material families

Build a small, deliberate material library instead of applying one generic metallic finish everywhere.

- Brushed steel needs directionally consistent grain and broad controlled highlights. Polished bevels need a cleaner, sharper response.
- Champagne trim should read as restrained warm metal, not yellow paint or a luminous outline.
- The charcoal dial needs fine surface detail without noisy speckle. Markers, blue hands and engraving must remain legible.
- Crown, case, movement plates, screws and engravings need distinct finishing appropriate to their shapes. Do not alter source gear geometry to improve shading.
- Leather needs low-gloss fine grain, softer padded areas and separate edge and thread response. Avoid uniform plastic sheen.

Calibrate texture scale, roughness and normal intensity on actual watch close-ups before extending presets. Correct texture color spaces and output conversion before compensating with exposure. See the official [Three.js color management guide](https://threejs.org/manual/pages/color-management.html).

### Clear glass with visible optical depth

The existing glass is not thickness-free: the current treatment already uses transmission 1, IOR 1.76, approximately 0.35 mm front and 0.30 mm rear measured thickness, and specular intensity 0.28. It has no absorption treatment. The problem is the final appearance and integration, not a missing transmission checkbox.

Refine the actual crystal edge, thickness, refraction and reflections together. Add only subtle absorption if it improves depth without tinting or clouding the dial. Compare glass on and off at identical camera and exposure settings. Avoid using heavy roughness, bloom or ambient occlusion to disguise refraction errors.

Use the existing physical-material controls deliberately; transmission, thickness, attenuation and anisotropy are documented capabilities, not all new r187 features. Their cost and visual benefit must be measured. See [MeshPhysicalMaterial](https://threejs.org/docs/pages/MeshPhysicalMaterial.html).

### Product studio lighting

Use a controlled key, strip reflections and negative fill to reveal case curvature and separate polished from brushed areas. Reflections must explain the model through a useful orbit, not only from one hero camera.

Create a seamless charcoal gradient backdrop with a grounded, soft contact shadow. Keep the watch separated from the background without a visible platform, horizon seam or artificial glow unless an intentional composition requires it.

Set tone mapping and exposure first. Add antialiasing, contact occlusion and restrained bloom only where they improve the image. Watch for dark AO halos, clipped highlights, grain shimmer, glass haze and lost blue-hand contrast. Keep the ordinary product view sharp; cinematic effects must not impair inspection.

**Evidence required:** matched actual-watch images at whole-watch, dial and macro scale; front, three-quarter, side and reverse views; and a short orbit. Inspect in motion as well as stills. The same scene settings must produce coherent materials across those angles.

## Interface and interactive behavior

### Rebuild the layout around the watch

Replace the old control structure rather than reskinning its buttons. A large unobstructed viewer and a compact task toolbar should be the primary composition. The static atelier layout study remains a design proposal. A separate local working shell now has runtime proxies and fallback-browser testing, but loaded GPU interaction has not been verified.

- Use plain labels and a visible active state. Keep the essential actions directly discoverable.
- Select parts directly in the scene and offer a searchable parts route for precision and keyboard access.
- Show context tools for the selected part or current task. Do not make every possible operation a permanent large button.
- Support crown dragging, with visible pull, push and winding alternatives that do not require a pointer gesture.
- Place diagnostics and detailed evidence outside the primary product experience without deleting access to them.
- Make the loaded experience work at 1440 by 900 and 1280 by 800 without page or nested-toolbar scrolling or dial occlusion.

At 200 percent zoom and on mobile, prioritize readable text, reachable controls and a useful viewer. Do not shrink controls to claim an impossible all-options-on-one-small-screen layout. Mobile can use an explicit task panel or sheet, with essential actions still visible and no trapped scrolling.

### Preserve every useful capability

Maintain a command inventory while replacing the UI. Each old action needs a working destination and a regression test where practical.

- Views and navigation: face, studio, interior, reverse, profile, detail cameras, orbit and reset.
- Movement: play, pause, slow motion, timeline or pose inspection and exact reset behavior.
- Crown: focus, wind both ways, pull, push, drag and reset.
- Appearance: crystal visibility, original and authored face, finishes, movement-only and quality choices.
- Inspection: search, group, select, isolate, clear and restore the complete watch.
- Presentation: start or stop the tour, previous and next shot, and safe manual interruption.
- Output: watch PNG, playable WebM where supported, view-state JSON save and load, and studio reset.
- Evidence: source attribution, measurements and diagnostic information.

### Smooth crown and presentation animation

Separate command state from displayed motion. The existing crown commands update mechanical state immediately; the new local presentation tween does not yet establish complete animation acceptance.

Integrate crown rotation, pull and push with hand-setting response, movement timing, camera transitions and tour behavior. Handle repeated input, direction reversal, pause, reset and background resume without jumps or stale animations. Reduced-motion mode should retain the same useful actions without unnecessary movement.

### Continuous exploded assembly

Integrate the local exploded-view module into a continuously adjustable slider with smooth separation and reassembly. Its seven focused tests are not browser acceptance. Use meaningful assembly groups rather than scattering every mesh independently. A proposed grouping is crystal, face and hands, movement, case, crown and strap assemblies; confirm it against the actual hierarchy during integration.

Store immutable assembled transforms and derive every exploded pose from them. Do not accumulate offsets. Preserve the exact assembled source pose at zero. Define how explosion interacts with selection, isolation, camera framing, playback, crown controls and saved view state; disable incompatible actions visibly rather than letting states conflict.

**Evidence required:** end-to-end real-watch interaction recording, keyboard path, repeated crown operations, slider scrubbing and exact reassembly comparison. An exploded view explains assembly order; it does not certify physical disassembly.

## Renderer evaluation without a speculative rewrite

The current application uses Three.js r180 with custom `onBeforeCompile` finishes and refraction, plus `EffectComposer` SSAO and custom refraction occlusion. A version update and a renderer migration are separate decisions.

Three.js r187 was released on 30 October 2026. Its PMREM changes and EON rough-diffuse shading are worth testing for this material study, but a newer version alone does not produce better leather or glass. Pin the evaluated version and review the intervening migration changes. See the official [r187 release](https://github.com/mrdoob/three.js/releases/tag/r187).

### Bounded comparison

1. Capture the improved actual-model baseline with one fixed camera set, lighting rig, exposure, pixel ratio and quality settings.
2. Test r187 with the existing WebGL approach separately from the WebGPU experiment. Keep the working baseline available.
3. Build one representative WebGPU trial containing the actual crescent, brushed and polished metal, leather, glass and a difficult reflective angle. Do not begin by porting the entire UI.
4. Port the required shader work to node materials and TSL, and replace the relevant post-processing chain. `onBeforeCompile` hooks and `EffectComposer` cannot simply be reused with `WebGPURenderer`. See the official [migration overview](https://threejs.org/manual/pages/webgpurenderer) and [post-processing guide](https://threejs.org/manual/pages/webgpu-postprocessing.html).
5. Compare visible quality, startup, frame times, memory, export behavior and fallback at matched settings. Record the actual active backend; a `WebGPURenderer` instance can be running WebGL 2.

**Go:** adopt the new path only if the representative scene preserves or improves the desired quality, supports the needed features and has credible performance evidence on a named device.

**No go:** retain the best verified WebGL path if the port degrades the image, breaks required features or lacks a demonstrable benefit. If hardware access is unavailable, mark hardware comparison unverified and continue the visual rebuild; do not claim a speedup from cloud software rendering.

The current secure cloud-browser diagnostic found `navigator.gpu` exposed but a null high-performance adapter response, without changing security flags. This blocks actual WebGPU hardware measurement in that environment. It says nothing about support or performance on Shayan's devices. Test and report fallback separately; an exposed API is not a usable adapter.

## Roadmap and evidence gates

The order below follows dependencies, not invented dates. Interface prototyping and test preparation can proceed beside visual work, but cannot substitute for the actual-model quality gate.

### Phase 1 Freeze the reference and inventory

- Record the preview, source revision, local changes, original geometry hashes, licensing and current capabilities.
- Capture the required camera set and log the specific visible defects. Establish reproducible materials and light settings.
- Reconcile missing, rejected, in-progress and unverified items against this plan.

**Outcome and gate:** a reproducible baseline with an intact rollback and no uncertainty about which results belong to which revision.

### Phase 2 Solve form and attachment

- Refine the deep asymmetric wall sections while preserving the uneven right-edge outline; add only small-radius endpoint joins.
- Correct the seconds ring's visible support and depth.
- Refine leather construction, case transitions, crown, lugs and buckle without altering the fixed movement.

**Outcome and gate:** clean neutral-material and shaded actual-model views, preserved source hashes and documented geometry checks. Iterate here if the construction still looks wrong.

### Phase 3 Prove the material and lighting treatment

- Build distinct material families, improved fine-grain leather, clear glass and a coherent studio rig.
- Validate the charcoal backdrop and grounded shadow through all required cameras.
- Use close-up comparisons to select the best treatment, then apply it consistently across the watch.

**Outcome and gate:** convincing whole-watch and macro imagery with no obvious floating attachment, plastic leather, uniform metal, cloudy dial or broken reflection transitions.

### Phase 4 Make the renderer decision

- Run the bounded r187 and WebGPU comparisons against the Phase 3 baseline.
- Record the active backend, matched settings, feature gaps and measured results.
- Adopt a proven improvement or explicitly retain WebGL. Do not leave a half-migrated default renderer.

**Outcome and gate:** a documented go or no-go decision and one supported main rendering path. The optional experiment is not allowed to block unrelated completion work.

### Phase 5 Integrate the rebuilt controls and animation

- Replace the old UI, preserve the full command inventory and wire direct selection and crown dragging.
- Complete smooth crown, camera and tour behavior.
- Implement the exploded slider, group logic, exact reassembly and saved-state behavior.

**Outcome and gate:** every required action works on the loaded watch; desktop layout, mobile behavior and keyboard access are demonstrated rather than inferred from a static mockup.

### Phase 6 Validate the complete experience

- Run automated geometry, logic, syntax and asset-manifest checks against the new candidate.
- Complete real-watch exports, restoration, accessibility, failure recovery and resource-lifecycle tests.
- Measure performance on named available devices and record remaining coverage gaps honestly.

**Outcome and gate:** no known critical failures in the supported journeys, with browser evidence attached to the exact candidate revision. A green unit suite alone cannot pass this phase.

### Phase 7 Prepare the release and integration package

- Capture the final tour and replace outdated presentation evidence with actual candidate images.
- Test relative paths, subpath hosting and the documented integration route.
- Package source, native scene, assets, licenses, test record, release notes and rollback; verify the new backup contains the final work.

**Outcome and gate:** a reproducible handoff that Shayan can integrate into the main Kazeyami site without guessing dependencies or losing the prior version.

## Release checks and definition of finished

### Visual review

- Review full-watch, face, both three-quarter, profile, reverse, crown, leather, rim-join and seconds-support captures from the actual runtime.
- Verify time readability, finish distinction, clean silhouettes and coherent glass at ordinary scale and macro scale.
- Inspect a slow orbit and moving hands for flicker, shimmer, clipping and transient artifacts.
- Keep rejected and historical images clearly labeled. Do not present an attractive concept image as the shipped watch.

### Functional and accessible behavior

- Test repeated and interrupted camera, tour, crown, appearance, isolation and explosion actions in mixed sequences.
- Complete the keyboard route with visible focus, understandable labels, selected and disabled states, and readable status announcements.
- Test touch targets, mobile orientation, zoom and reduced motion on the loaded experience.
- Confirm reset and JSON restoration return the documented appearance, camera, motion, crown and exploded state without stale UI.

### Exports and resilience

- Download an actual-watch PNG and inspect the file. A download request or test-fixture image is insufficient.
- Record an actual-watch WebM, download it and play it back. Verify unsupported-recording messaging independently of WebGL support.
- Save view JSON, change the scene, reload the file and compare the restored state. Test malformed input without losing the working scene.
- Test cold load, missing or slow assets, retry, context loss, background resume and removal or remounting of the viewer.
- Check disposal of render targets, textures, event listeners and animation loops. DOM removal alone does not prove resource cleanup.

### Performance evidence

Record browser version, device and GPU, active backend, viewport, pixel ratio, quality, cold-load behavior and frame-time measurements for a repeatable interaction sequence. Define any performance budget for that named setup, then verify it. Do not claim mobile support or a WebGPU advantage from a desktop software-rendering pass. If a device is inaccessible, record the coverage gap and the specific test still required.

### Handoff and ownership

Provide a versioned release candidate, editable native scene, source assets, exact dependency versions, license notices, integration guide and a tested rollback. An iframe is the initial integration proposal; a component integration needs explicit lifecycle and style isolation work. Test the chosen route rather than promising both.

The latest recorded Drive backup, `1Q0MUqsdkqABtzMHSAxpzHlpZ1BWm48CL`, contains earlier r05 and r06 native work. It does not establish protection of these new edits. Create and verify an updated authorized backup before handoff.

The experience is finished only when the visual defects above are resolved, required interactions and exports work, supported-device evidence is recorded, no critical known defects remain, and the source and integration package can reproduce the result. Report gaps as gaps. Do not label the current rejected preview accepted, and do not equate passing tests with a finished watch.

## Working record

- Published review route: [Aerial preview with SVG face and photographed leather](https://shayan-kazeyami.github.io/aerial-watch/preview-b/integrated-preview.html?face=svg03&leather=photo).
- Recorded preview source: `4800e5c3664824531b9e331cdcbdd17156754617`.
- Recorded main revision: `4004351e274bf6c788897f89f467d10a1fe225b0`.
- Detailed historical evidence: [implementation checkpoint](IMPLEMENTATION-STATUS.md), [live QA](LIVE-QA-2026-10-31.md), [integration handoff](INTEGRATION-HANDOFF.md), [source attribution](../ATTRIBUTION.md).

Maintain one clear status for each requirement and tie completion to a revision and evidence. Share useful visible results as they become available. If blocked, state the exact reason, affected work and action needed, then continue independent authorized work. Routine aesthetic and engineering choices remain owned by the implementation work, not returned to Shayan as a stream of direction requests.
