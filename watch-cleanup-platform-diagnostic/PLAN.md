# Prepared only: macOS cleanup diagnostic
No browser, asset payload, source/master changes or security relaxation. No launch authorized.

Two isolated owned Python process groups, children self-exit after20seconds, cleanup grace0.5seconds and leader waits5seconds. Disposable macos-latest job bounded3minutes. Same macOS runner family and Python3.12 as failed lazy jobs; exact image version may differ and must be recorded from Actions logs. No installs beyond sanctioned checkout/setup-python. Expected failure is evidence, not grounds for retry.

Capture before/after process-group zero probes, complete cleanup report, final escalation and leader reap. EPERM stays unverified; no dead-group inference. Result JSON preserved even when cleanup fails. Scoped success requires absent group after cleanup, not only leader reap. This tests ordinary live leader and exited leader with intended TERM-resistant descendant. The latter writes a fresh marker only after installing its TERM-ignore handler; parent waits at most5seconds for that handshake.

Readiness HOLD pending independent review, including validating the resistant-child startup handshake, artifact retention and outer bounds. Diagnostic has not run locally or remotely; only syntax compilation. Workflow is a proposal, not repository workflow.

## Reviewed-gate correction pending re-review
Success now requires exactly the two named distinct cases, started=true, initial probe present, cleanup with no recorded errors and leader reaped, final probe absent, successful final signal/reap evidence, and a positive resistant-child handshake PID. Initial EPERM cannot produce a pass. Nine pure gate unit tests pass, including incomplete/duplicate cases, initial/after EPERM, absent initial group, missing handshake, cleanup errors, and final failures. No diagnostic processes executed.
