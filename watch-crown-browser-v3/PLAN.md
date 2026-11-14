# Crown browser QA V3: isolated reap-first integration, not executed

Independent run verification: ../watch-cleanup-reap-first-run-independent/REPORT.json confirms one cleanup-only macOS run43648081708. This does not establish browser cleanup or crown success.

prepare.py/server.py/driver.py/QA_CLOSURE.json byte-identical to V2. Exact reviewed/tested reap-first cleanup.py copied unchanged. Supervisor differs only import from coordinator. New coordinator attempts both owned child groups even if first fails, preserves structured error reports, and invokes cleanup with literal grace0.5/post_grace1.0 matching platform diagnostic. Worst intended per-group budget≈6.5s; two≈13s excluding scheduler/syscall overhead. Any EPERM remains fail-closed; group absence required.

Browser scope unchanged: exact baseline/candidate298-file closures; only declared read-only telemetry; real keyboard/control direction in seated/pulled modes, original hotspot availability never overridden. Chromium sandbox retained. Source flags/holds unchanged. Helper group absence does not enumerate daemon descendants escaping group; explicit Playwright browser.close remains in driver. Actual browser-specific cleanup remains unverified until separately approved run.

Must materialize fresh prepared roots via prepare.py --materialize under180s bound before run_arm.py. Driver1100s, supervisor1170s unchanged. Cleanup results written success/failure. Four pure coordinator tests pass, no browser/materialization/platform run. Package requires independent integration review then exact workflow/payload review before any run. No main, deployment, source replacement, or retry.
