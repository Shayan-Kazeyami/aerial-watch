# Aerial Watch studio showcase masterplan

Updated 31 October 2026. Owner: Kazeyami. Status: active design and implementation plan, not a completed release.

## Purpose

Aerial is a portfolio centerpiece for the main Kazeyami website. It must impress prospective clients through original product design, precise 3D craft, convincing materials, understandable mechanical motion and a polished interactive presentation. It is not a watch storefront, a manufacturing release or a general-purpose engineering dashboard.

The client's first impression should be of a premium watch. Its technical depth should reward exploration rather than dominate the face.

## Confirmed direction from Shayan

- Showcase the studio's technical and design capabilities while looking visually impressive.
- A premium face that reveals internal working without resembling a cheap skeleton watch.
- One understandable control section, potentially integrated into the 3D viewer rather than a separate sidebar.
- Avoid scrolling and hidden dropdowns for viewer options.
- Shayan will integrate the finished experience into the main Kazeyami site.
- Work directly in dot's cloud workspace; do not launch quota-blocked Codex tasks for this work.

These requirements supersede the previous emphasis on a technical review interface. The mechanical source and licensing constraints remain in force.

## Design proposal

### Premium face

Start with the dial composition, not decorative effects. Establish a continuous time-reading perimeter, strong hand contrast, disciplined typography and visible depth between dial, markers and hands. Reveal a small number of mechanically meaningful areas. Openings must follow a coherent design language rather than arbitrary cutouts or complete removal of the dial.

Working palette: dark graphite, restrained warm metal accents, brushed and polished steel, deep-blue hands and charcoal leather. This is a proposed direction, not a user-mandated palette. Test it against the actual model before locking it.

Keep the balance and selected connected gear movement visible where the existing geometry permits. Do not invent nonfunctional gears, change tooth counts for decoration or imply a physical simulation. A separate interior view can expose much more without compromising the primary face.

### Craft

Refine bevels, surface transitions, crown proportions, lug attachment, crystal edges, strap thickness, stitching and buckle details. Avoid uniform mirror finishes, flat gray plates, oversized exposed screws and busy ornamental gears. Surface roughness and lighting should explain shape, not hide defects.

Evaluate the result at whole-watch scale, normal dial-reading scale and macro scale. A beautiful close-up alone does not compensate for an unbalanced overall silhouette.

### Unified studio controls

The viewer is one visual composition. Place clearly labeled controls at its perimeter, leaving the dial unobstructed. Use visible button groups instead of dropdowns and avoid an independently scrolling sidebar.

Control inventory to reconcile before deleting or hiding anything:

1. Views: face, studio, interior, reverse, profile and useful detail views.
2. Motion: play/pause, slow motion, pose reset and timeline inspection.
3. Crown: focus, wind left/right, pull/push and reset.
4. Appearance: crystals, original versus authored face, finishes, original movement and render quality.
5. Inspection: component search/group, select, isolate, clear and restore complete watch.
6. Tour: start/stop and previous/next shot.
7. Output: PNG, video, view-settings save/load and reset studio.
8. Technical evidence: measurements, diagnostic output and source attribution.

Consolidate duplicated commands. Separate diagnostic information from product interactions, but do not silently remove useful functions. All public-facing control choices should be directly discoverable. Large component-result sets are content rather than a justification for an enormous permanent button wall.

Desktop acceptance target: at 1440 by 900, visible viewer controls without page or nested-panel scrolling, legible labels and no dial occlusion. Verify at 1280 by 800 and at 200 percent zoom too. On narrow screens, readability and accessible targets take precedence over an impossible promise to display every control and result without any scrolling. Resolve the mobile arrangement explicitly and show it for review.

## Roadmap and evidence gates

### Phase 1 Establish the baseline and art direction

- Preserve existing source geometry, licences and working behaviors.
- Inventory the actual runtime, entry points, assets and incomplete tests.
- Capture baseline face, three-quarter, interior and UI views with exact source revision.
- Produce a reversible dial composition candidate based on the supplied movement.
- Compare normal-size readability, visible mechanical interest and restrained finishing.

Gate: a reviewable actual-model candidate and clear design rationale. No generated illustration is evidence that the runtime model was changed.

### Phase 2 Refine the watch

- Implement selective dial openings and a coherent marker/hand hierarchy.
- Review the case, crystal, crown, lugs, strap and buckle as one design.
- Keep original movement geometry and authored presentation modifications identifiable.
- Verify static separation and sample moving-part sweeps where geometry permits.
- Label visual-only modifications and unvalidated mechanical claims accurately.

Gate: clean front, three-quarter and macro renders without obvious clipping, floating parts or unreadable time display. Physical manufacture and complete dynamic clearance certification are outside this showcase's scope.

### Phase 3 Build the integrated interface

- Replace the long sidebar with a unified studio layout.
- Expose normal control choices using plain-language button groups.
- Preserve keyboard focus, pressed state, disabled state and existing export/import behavior.
- Avoid duplicate controls and hidden essential choices.
- Review desktop and narrow-screen layouts with real screenshots, including loading and failure states.

Gate: controls understandable without instructions, watch unobstructed, no overflow at the desktop target, and no inaccessible controls at zoom or narrow widths.

### Phase 4 Create the presentation

- Compose an opening camera and lighting setup that reads immediately as premium.
- Provide an optional short tour of the whole watch, dial, motion and material craft.
- Keep supporting copy brief and client-facing.
- Replace outdated gallery evidence with real captures of the accepted candidate.
- Distinguish historical reference renders from the current experience.

Gate: an attractive first impression and a coherent short demonstration of Kazeyami's capabilities without overstating authorship of OM10.

### Phase 5 Validate reliability and performance

- Test cold load, slow or failed assets, optional-asset failure and retry.
- Test repeated camera, appearance, crown and motion interactions.
- Test background/resume, context loss, navigation away and resource cleanup.
- Verify PNG output, view-settings round trip and valid playable video where supported.
- Test unsupported recording independently of WebGL support.
- Check keyboard, touch, reduced motion and readable status announcements.
- Record actual browser/device and viewport; do not convert a desktop result into a mobile claim.

Gate: no known critical failure in supported journeys, automated checks pass, and manual/browser evidence accompanies any compatibility claim. Actual frame-rate targets must be tied to a named device and quality setting.

### Phase 6 Package for the main Kazeyami site

- Relative asset URLs and subpath testing.
- Document the simplest isolated integration route, initially an iframe if appropriate. A true component integration requires additional lifecycle and CSS isolation work.
- Avoid global host-site style leakage and unsolicited analytics or uploads.
- Preserve attribution, CC BY-SA obligations and third-party notices.
- Supply a versioned release candidate, test record, integration guide and rollback reference.
- Do not deploy to the main Kazeyami site. Shayan owns that integration step.

Gate: the documented installation path is actually tested and the handoff identifies any remaining constraints.

## Definition of finished

The watch and viewer meet the accepted visual direction; essential interactions and exports work; representative desktop and mobile evidence exists; no critical known defects remain; documentation and licences are accurate; the integration package is reproducible. A green unit suite alone is not completion. A single impressive static render alone is not completion either.

## Verified checkpoint

- Existing readiness branch base inspected: b0f290d1ac84b8bf575e5da80ceb63777fe88814.
- Direct recording-finalization recovery is in draft PR 2, final remote commit 2532192fde35807ca8e5e13346b1aeb744904002. It is stacked on the readiness branch, not main.
- 41 Node regression tests, 72 JavaScript syntax checks and 161 manifest identities passed. GitHub CI for that commit passed.
- The recording watchdog was regression-tested with a deliberately missing browser stop event. Real-device recording is not yet accepted.
- Cloud browser preview now reaches the local site through a persistent desktop-hosted HTTP server. Chromium reports that its WebGL context is disabled. The observed watch image is a fallback poster, not successful live 3D rendering.
- Premium dial redesign and unified controls are not implemented at this checkpoint.

## Working discipline

One bounded visible deliverable at a time. Reuse checkpoints and test scripts; do not create extra coordination layers. Keep modifications reversible and on review branches. Update this checkpoint with evidence as work progresses. Do not claim final visual quality without inspecting actual model output, and do not trigger publication merely to obtain a preview.
