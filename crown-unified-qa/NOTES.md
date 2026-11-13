# Unified crown input candidate (not published)
Baseline: immutable 214740598c3327efb618f559ce587911d3893bd97a060a53172277877480a8b2.

Runtime changes: assembly-crown-hotspot.js and assembly-review.js only.
The existing hotspot now exposes beginPointer(event,captureTarget), movePointer,
endPointer(event,cancel=false), cancel(). Both dot and mesh paths use its same
offset/dead-zone/rate/RAF stream and immediate crown turn callback. It owns
capture on the originating element. Start/end callbacks temporarily disable
OrbitControls and restore the previous enabled state, clearing scene-selection
pointer state. Every accepted mesh event stops immediate propagation to avoid
OrbitControls and selection duplication. No automatic Time-panel event remains
in the mesh path. Tap toggles once; the old extra double-click toggle is removed.
Explicit Set time controls and focus action are unchanged.

Reset, reseat, scrub, view, Escape, explosion, blur, hidden document and disposal
cancel shared input. Lost capture/pointercancel are matching-pointer-only.
Source mesh start checks readiness, visible ancestors and nearest visible
mesh hit (one scene raycast per crown-hit start, none on moves). This prevents
interacting through a visible case from the rear.

8 CPU mock-DOM tests pass: dot/direct continuous stationary hold rate, reverse,
dead zone, tap once, duplicate/unrelated pointer, cancellation, capture cleanup,
availability, blur, visibility and disposal. Both source syntax checks pass.
These are not browser/render/physical-touch proof.

Browser gates:
- Project crown surface outside dot hitbox, confirm nearest visible hit is crown,
  send actual CDP touch. Hold displaced >=1sec with no pointermoves; verify ongoing
  immediate degrees/time updates, no tween tail, reverse/dead zone, release stop.
- Same trace on dot: equivalent rate; exact single tap toggle on both.
- No Time panel, camera change, canvas resize, navigation or model refetch.
- Rear/occluded crown does not start; hidden ancestors/readiness block.
- Reset/view/reseat during held gesture stop future turns and restore orbit;
  lost capture, pointercancel, blur, hidden and disposal do likewise.
- Existing Set time/keyboard/buttons and winding versus time-setting intact.
- Parent should verify model traversal includes crown and visible blockers in
  the actual assembled scene, including batched surfaces and transparent modes.

Follow-up: 11 tests now pass. Actual source-extracted ownership callbacks preserve
both initially enabled and initially disabled OrbitControls. A captured mesh
gesture continues if only the decorative dot anchor leaves the viewport; actual
scene unavailability still cancels. Dot-origin gestures retain anchor-loss
cancellation. Both cases tested. Synchronous initialization renderingQuality()
does not invoke view(); first initial view is inside async loading continuation,
after hotspot and pointer state initialization.
