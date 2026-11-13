# Optional mechanical-layer inspection

2026-11-13. Immutable release `214740598c3327efb618f559ce587911d3893bd97a060a53172277877480a8b2`.

The existing exploded view already translates the movement into six construction layers. Its full-watch overview makes their overlapping interiors hard to inspect. The Explode sheet now provides a single optional layer selector and Overview return. Selecting a layer temporarily hides other model meshes and frames its existing geometry in the region not covered by the sheet. This is presentation isolation, not a new physical disassembly simulation. The existing slider, Full and Assemble controls remain.

Preserved: all 166 original source memberships, all 417 registered mesh local poses/geometry, mechanical offsets, selected quality, accepted dial and bevel design. Hidden authored variants are not revealed. Repeated selection keeps one original overview snapshot. Same-size Overview restores its exact camera and visibility; after rotation, the overview refits the complete exploded envelope. Leaving Explode restores the overview before other tools, including Capture. Focus is deliberately temporary and is not encoded as an additional saved-view format.

Focused depth constraints use actual selected member bounds. Full-detail texture adoption reapplies the focus mask after all material and tick-batch updates. No geometry loads are repeated. Scalar state checks avoid enumerating membership in the interaction frame loop.

## Evidence

- 21 CPU tests pass, including hidden parents/variants, exact restore, invalid inputs, asymmetric safe rectangles with thick bounds, material-refresh mask reapplication and lifecycle cleanup.
- Final browser run [43453321497](https://github.com/Shayan-Kazeyami/aerial-watch/actions/runs/43453321497), exact stage commit `f49618da29c57bca5e2021d34af98d75685afd99`, passes both 430×932 and 740×360 with zero page errors.
- All six layer projected bounds remain inside the measured overlay-free rectangle. Projected area grows 3.74–38.69× in portrait and 5.35–34.91× in short landscape relative to their overview projections. These are geometric readability measurements, not FPS.
- Every interaction target is at least 44 CSS pixels. The compact sheet is 158 CSS pixels, previously 102; the added row is the explicit layer selector and Overview return. Canvas size remains unchanged.
- Exact same-size camera return, unchanged mesh poses/geometry and surface semantics, rotation, reassembly, no model refetch, and delayed 2K→verified4K adoption while focused all pass. Material UUIDs remain unchanged through focus switching. Across intentional detail material refresh, the existing Dial carrier may receive an equivalent material instance, so surface semantics rather than UUID identity are checked for that boundary.
- Actual portrait, short-landscape and rotated train/balance renders were inspected. Artifacts: portrait `14053906117`, landscape `14051913344`.

## Failed candidates retained

Run 43449346730 failed before browser startup due to a CPU vendor symlink; corrected to the shared manifest owner. Run 43449710025 passed the initial gates but did not test delayed adoption or exclude the panel rectangle explicitly. Run 43451386618 caught two nonmember visibility flags reset after the initial mask call; enforcement moved after tick-batch updates. Run 43452383965 then passed adoption visibility/camera but its post-adoption UUID assertion was overbroad. Run 43452962726 retained that same old assertion. Final acceptance additionally checks material surface semantics and retains strict UUID identity within focus switching.

## Limits and rollback

Chromium SwiftShader with touch emulation is not physical-phone FPS or hardware WebGPU parity. Selected quality is never silently changed. Existing source geometry and physical-accuracy limitations remain. Restore the root loader/index from main `7bb49e675f408ffa0c82e3b8a8669521947b3819` to roll back to release 0c0dd309. Public deployment verification and a fresh runtime recovery archive follow promotion.
