# Failed action investigation and isolated visible-UI proposal

Failed run43617161627 preserved at commitddad2cdf… and downloaded artifact14122109841, digestaa364edebe…. Original browser-driver.py/OUTGOING.json and evidence untouched. No retry/run/upload for this fix.

Exact pinned atelier-preview.html line30 places #animate,#animate-movement,#finish under `<div id="runtime-bridge" hidden inert>`. These are runtime state controls, not directly actionable user UI. Calling Playwright set_checked on #animate caused30s actionability timeout after registration succeeded; not evidence renderer hung or geometry failed.

Correct public route from exact atelier-preview.js: visible #motion proxies play-motion (line250); runtime play-motion handler (assembly-review.js733) toggles BOTH animation inputs off when either is on. Read #motion aria-pressed first; click only if true, else do not start motion, then read-only assert assemblyInspect animation and interiorAnimation false and aria false. Unknown state fails closed. No force/bridge event/direct state mutation.

Finished control is also hidden, so fix its upcoming analogous failure proactively: visible Studio tools `.atelier-more[data-mode="settings"]`→visible Engineering comparisons `#atelier-tools [data-mode="engineering"]`→actual visible proxy checkbox `#atelier-tools input[data-check="finish"]`. Shell change handler routes this to existing runtime change through public UI. Assert assemblyInspect.finish, close contextual tool and wait hidden before macros. Preserve existing shader/material behavior; never use hidden #finish directly.

New ui_actions.py and browser-driver-visible-ui.py are separate from failed frozen driver. Candidate/source/camera/picking/render/cleanup/visibility gates unchanged, only these visible controls and a fresh evidence directory differ. Four mock tests pass: running pause, already-paused no toggle, unknown state refusal and correct visible finish navigation. This is mocked action routing, not actual browser success. Independent review required before proposing one distinct corrected QA execution; no automatic rerun authorized here.
