# Independent-runner normal-unload attribution diagnostic

Narrow purpose: test whether normal page navigation through the existing
pagehide lifecycle changes the previously observed browser shutdown failure.
This is NOT another release-approval attempt or reliable performance benchmark.

Exactly two independent Ubuntu jobs, one published-e79 and one frozen0116.
Desktop1280x800/DPR1 only. No mobile claim. Each job builds/verifies the same
sources, launches one fresh browser, requires original source/revision/full-detail
and state/dimension identities, captures Efficient then Balanced through real
quality UI with the same180s CDP image and nonblank gates. One attempt per release;
no auto retry, alternate renderer, forced redraw, paused motion or force kill.

After the capture outcome is saved, each job attempts normal host navigation to
about:blank (30s), then browser.close (30s). Unload failure and close failure are
separate and both fail the diagnostic; a successful close never hides a failed
unload. Earlier capture failure is preserved. Read-only pagehide console observers
record event and subsequent microtask, URL and persisted flag. This does not prove
all async disposal completed; missing console events do not prove pagehide absent.
Normal unload-before-close is a different cleanup condition from the prior direct
browser.close gate, which remains failed and is NOT retroactively passed.

Arm budget1100s; job envelope30min includes setup, launch and bounded cleanup.
Exact action-start/complete/failure/cancellation and outer/nested timeout metadata
remain. External process sampling15s survives no-match; no periodic frame/DOM/rAF
heartbeat. Actual browser product, unmasked WebGL identity, dimensions, CPU model,
CPU count and host memory are recorded. ps%CPU is lifetime-average and RSS is not
private/GPU allocation or leak proof.

Runner isolation prevents an unclosed baseline process contaminating candidate.
However the two runners are not a matched pair: load, hardware scheduling and
dynamic clock phase differ. Timings are descriptive observations only; no precise
baseline/candidate performance ratio, statistical regression, or environment-only
diagnosis is warranted. Same screenshot and original full lifecycle/UI gates remain
required before any production decision. Diagnostic passed remainsfalse always.

Local validation:11 mocked/static tests plus Python syntax. Identity preflight uses
the already verified published/candidate bytes; no local browser result claimed.
Independent review is required before separate QA-only execution. No main or
frozen QA branch change is included.
