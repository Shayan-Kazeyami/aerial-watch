# CASE hosted bootstrap fixture — preparation only

Separate relocatable package. No workflow upload/dispatch or browser/server execution.
Set CASE_FIXTURE_STAGING to exact reconstructed0116 staging root. Inventory ignores legacy local paths (removed), resolves only pinned URL paths inside staging, rejects symlink escape and verifies all298 manifest entries +3root entry files. Baseline/candidate override bytes unchanged. verify.py is read-only CPU preflight.

Workflow draft is manual-only, exact source/fixture commits, contents:read, no deploy/main writes, full SHA action pins and exact QA commit input, one job with35minute outer bound. Node from Ubuntu hosted runner is recorded, not claimed deterministic; any changed reconstruction bytes fail all original source pins. Python dependencies version-pinned, not cryptographic wheel hashes; hosted OS/dependency supply chain remains a disclosed reproducibility limitation. Require independent review of these package/workflow changes and exact future QA commit before upload/run. No unpinned branch checkout allowed. No sandbox-disabled fallback/retry.

Bundled browser from Playwright1.62.0 replaces this machine's unavailable cache/system binary; browser revision, actual binarySHA and runtime version must be recorded in artifacts. Sandbox explicitly enabled. Successful bootstrap is not lifecycle/disposal/abort or memory/RSS/FPS acceptance. Prior local failures remain untouched in their original packages. Existing watchdog same1350s+bounded group shutdown. No automatic cleanup of earlier evidence dirs.

## Exit-status correction

Harness and watchdog now return0 only for their exact completed-bootstrap status AND empty cleanup errors; every other status exits1 after writing evidence. Workflow set-e therefore cannot report green for HOLD/STOPPED reports. test_exit_contract.py checks the exact AST return expression against success, cleanup failure and9noncompleted statuses per component, and verifies evidence-finally precedes exit. These are isolated CPU/static regressions, not a real process/browser run. Prior immutable reviewed-watchdog equality claim is superseded by this explicit exit-policy-only correction.
