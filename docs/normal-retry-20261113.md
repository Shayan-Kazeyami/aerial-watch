# In-place full-detail recovery

Verified candidate entering publication; public verification is separate. Baseline main 89f648d5 and immutable release fad7fffe. Current candidate release 0c0dd309c80d8ce23e5743dac69555ffa3364e20664f2eb2474c1788e29f1d27. Earlier 54364969 is retained as the prior candidate.

## User-visible recovery

A transient background 4K leather-normal failure previously left a usable 2K watch but instructed a reload, losing the current configuration before image/video capture could resume. Capture now shows honest pending/failure status and an explicit Retry detail action. It performs one verified attempt per request, coalesces repeated clicks, leaves the existing texture/view in place and never schedules automatic retries. PNG/video remain blocked until the exact requested full normal is installed. Save/load configuration remains available; stopping an active recording is not blocked.

The controller retains the verified 4,389,472-byte initial payload after failure so retry can reuse it; it releases its reference on successful adoption or disposal. This is reference accounting, not a GC/GPU memory measurement. Late decoded resources and aborted loads retain existing cleanup behavior. Failure warnings are deduplicated and removed on successful recovery. Focus moves from Retry to the status while pending, then to Save PNG only if the user has not moved focus elsewhere.

## Evidence and limits

32 controller/capture-policy CPU tests passed. Actual browser tests inject two HTTP503 responses, then allow a gated third attempt. They verify low/full installed identity, button readiness, duplicate-click coalescing, exact camera/crown/explosion/quality/geometry identity and normal scales, no navigation/model refetch, and portrait/short-landscape Capture layout with 44 px targets. Actual PNG export includes verified full-detail provenance. Software-GPU tests are functional/still-view evidence, not phone FPS or new end-to-end video encoding coverage.

Run 43442880847 passed landscape but portrait failed exact stable-state equality without sufficient diagnostics. The cause is unresolved, not described as fixed. Diagnostic run 43443578163 passed both viewports with zero differences; final repeat additionally requires three exact settled snapshots before preservation checks and asserts recovery focus. No numeric tolerance or runtime change was introduced to make the gate pass. The initial run 43442743486 failed only because its viewport environment used names rather than dimensions; corrected in QA.

Final repeat, publication, public verification and recovery are recorded separately once completed. Do not claim deployment from these candidate notes.

Repeat run 43444392046 at 289546a7 passed both viewports with zero state differences, accessible focus recovery, and a real 477,814-byte PNG carrying verified full-detail identity. Actual UI screenshots inspected. A final presentation-only refinement removes duplicated success text from the Capture panel while preserving focus; release 0c0dd309 is receiving the same full gates.

Final exact-release run 43445375165 at 74d648d51fbcabdd8d511a96fbf5898db4533e8f passed both viewports for release 0c0dd309. All preservation comparisons were exactly equal. Portrait exported a 478,779-byte PNG with original 4K identity. Actual final UI image inspected; success confirmation is no longer duplicated. Entering publication; public verification and backup follow separately.
