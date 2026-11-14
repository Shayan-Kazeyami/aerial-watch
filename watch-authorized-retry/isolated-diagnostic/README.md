# Isolated screenshot-timeout diagnostic, NOT release QA approval

No upload, remote execution, browser execution, or production change was made.
This directory contains a guarded derived harness, not a replacement for the
required original screenshot/UI gate. A diagnostic always leaves `passed=false`.
The original source remains SHA-256
`c52b78dfcb389eca2c570f02c66a908fc2eb227239277b33bb55950a9cf9373c`.

## Concrete findings from preserved exact 0116 artifacts

- All three failures are the same `capture()` CDP compositor command at source
  line 65, not a quality selection or interaction assertion. Its 180-second
  await times out. The final second screenshot attempt also times out.
- Mobile and landscape each saved initial, Efficient, Balanced, Detail, and
  Studio images, and completed those four native interaction/reset cycles.
  Both stopped at return-Efficient capture before its fifth interaction cycle.
- Desktop saved initial and Efficient images, completed the Efficient lifecycle,
  and stopped at Balanced capture. Higher modes were not exercised there.
- Failing canvas sizes: mobile 430x760, landscape 740x247, desktop 1920x819.
  Mobile/landscape are returning to their initial canvas sizes, so this is not
  explained by an unusually large final screenshot alone.
- Last snapshots have same canvas/document, ready/cameraReady, interactive,
  no loading/failure, no page error/context loss. Those are pre-capture state,
  not proof of continued paint, compositor response, or GPU health.
- Prior f0 reported the same mobile/landscape return-Efficient capture pattern.
  This does not support attributing the problem specifically to Reset's near
  change. It also does not prove the application free of a lifecycle issue.

## Prepared comparison arms, awaiting separate execution authorization

Build locally with `python watch-authorized-retry/isolated-diagnostic/build.py`.
The derived harness expects the existing exact 0116 staged server at port 8765;
it never builds or modifies the release. Keep RID/revision assertions intact.

1. `DIAG_MODE=behavior`: retains all five same-document selections and exact
   native drag/reassemble/Home actions. Explicitly records omitted visual checks.
   Only `behaviorSequenceCompleted` can become true, never original gate passed.
2. `DIAG_MODE=repeated-capture`: retains all original screenshot checks and
   interaction ordering. A screenshot failure remains a failure and stops it.
3. `DIAG_MODE=fresh-quality DIAG_QUALITY=balanced` (or each other quality): starts
   a new browser process for each invocation, retains initial desktop hover/orbit
   preamble, selects one quality, and captures it. No lifecycle coverage claimed.

For each arm use `QA_UI_KIND=mobile`, `landscape`, or `desktop`; preserve original
viewport/DPR/SwiftShader. Do not run all arms concurrently when comparing pressure.
These are proposed invocations, NOT evidence that they ran.

## Independent heartbeat and failure handling

`heartbeat.py` concurrently records a browser-process `Browser.getVersion`,
frame DOM query, and two-frame rAF probe every five seconds to JSONL. Each is
bounded independently to three seconds. Browser CDP is a separate session from
the screenshot session. Frame probes still share the renderer/Playwright
transport; timing impact and lack of a fully independent OS observer are limits.
No observer mutates viewer state. No second screenshot is queued on a stalled
compositor. Capture start/completion monotonic timestamps are preserved.

Interpretation: browser heartbeat alive plus DOM/rAF alive with capture stalled
narrows to screenshot/compositor path; DOM alive but rAF stalled implicates paint
scheduling more broadly; all probes stalled needs transport/process diagnostics.
None alone distinguishes driver/software-GPU from renderer bugs. Add external
Chromium GPU logs/process memory in a separately authorized execution environment.
Do not assert a leak from process memory growth alone.

## Acceptance and limits

Mock heartbeat unit tests and Python syntax compilation pass locally. They do
not test a browser, WebGL, actual screenshot recovery, or visual correctness.
Do not simply raise timeout, force redraw, lower quality, pause the renderer,
remove required screenshots, or relabel diagnostics as release approval.
Any eventual fix must pass original meaningful interaction and visual gates on
the exact final payload. Caseback macro ROI remains a separate evidence defect.
