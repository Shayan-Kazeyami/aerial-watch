# Bounded same-runner WebGL control / exact viewer A/B

Diagnostic, not a viewer fix or release approval. One job per viewport, no retries.
Each runner performs two sequential fresh-browser arms using identical Chromium,
SwiftShader flags, viewport, device scale, mobile/touch settings, and CDP PNG
method: (A) tiny independent animated WebGL2 triangle; (B) exact frozen0116 viewer
loaded through its real root. A changes canvas density1→1.5; B captures Efficient
then selects Balanced using real UI and captures again. Both preserve meaningful
nonblank-pixel assertions and require actual saved images. There is no periodic
renderer heartbeat or route interception. Original release gates stay unchanged.

Action JSONL distinguishes clip preflight, exact capture dispatch, completion,
failure, cancellation and outer deadline. Process observer every15s records no
matching process as data and continues. Arm failure and browser-cleanup failure
are separate report fields, so cleanup cannot overwrite capture failure.
Failure-only browser-process/host-DOM probes are bounded and never redraw.

Budgets: simple control300s, viewer900s, screenshot180s, cleanup30s each.
No failure automatically retries. A failure does not prevent one independent B
attempt, but all failures remain visible. Diagnostic passed remainsfalse always.

Interpretation: if A also fails, the environment/control path is implicated but
watch readiness is still unproven. If A succeeds and B fails, trivial WebGL and
capture work on that runner, but this does NOT prove an app bug: software-GPU
load, app complexity, resource pressure and renderer lifecycle remain confounded.
Fresh browser per arm prevents shared app state; fixed A→B order and independent
low-load control are limitations. This is not physical GPU/FPS/leak evidence.

Local validation: syntax compilation and eight mocked/static tests only. No
local browser run claimed. Same-runner CI captures must be downloaded, their ZIP
hashes verified, and actual PNGs inspected before findings are reported.
