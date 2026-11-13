# Continuous crown input: one pose publication per streamed turn

The existing continuous hold path called cancel → turn → finish on every input tick. Cancel published the unchanged state, then finish published the committed state, running the full mechanism-pose calculation twice. While normal motion also ran, that became three pose calculations per tick.

The candidate adds an immediate option to crown turn input. It discards any unshown discrete target, commits the exact supplied delta once, and preserves winding/time callbacks and their order. The hotspot uses that path; discrete arrow/button strokes keep their existing easing. No geometry, materials, input rate, hold dead zone, clock ratio, pull distance or rendering-quality changes.

## Verification

- Current live behavior audit 43415964589 passed all touch/control checks and measured 3 pose calculations per held winding tick / 2 while setting.
- Candidate CDP touch run 43417497919 passed and measured 2 / 1 respectively. This is reduced redundant pose work, not a hardware FPS claim.
- Unit tests compare old/new exact state, winding deltas and setting deltas; pending-target discard; subsequent discrete easing; reversals; reduced motion; mode switches; zero/invalid input; overflow rejection without mutation; disposal.
- Exact immutable-release acceptance additionally compares all model matrices, position-buffer hashes, crown/winding states and setting time after matched winding/setting sequences. Publication waits for it to pass.
- Mobile acceptance includes stationary hold, center/reverse/release/cancel, tap pull without time change, held setting, seamless toolbar modes, internal Explode/Reset repetitions, immediate slider, and no document/canvas reset or repeated asset downloads.

All browser checks use Chromium software rendering. Physical-phone latency/FPS and hardware WebGPU parity remain unmeasured. Previous immutable release and runtime recovery are retained.

Exact immutable-release gate **43418557130** passed at QA commit `15354efa24407c566aeef28ef5f7bbcffd0e0753`. Across all **417 model meshes / 417 position buffers**, matched winding and setting sequences produced **zero matrix difference**, identical position-buffer hashes, identical crown/winding state and identical setting time. Real-touch pose counts remained 2 and 1; no JavaScript errors, navigation or canvas dimension writes. The tested release is `51e744f388b6989632e125d50090f119ce36bd8781a9cb16587ecb3f5a7d2aad`.
